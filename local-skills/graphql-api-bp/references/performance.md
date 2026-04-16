# Performance Optimization

Comprehensive guide to optimizing GraphQL API performance.

## DataLoader Deep Dive

### Basic DataLoader Pattern

```typescript
import DataLoader from 'dataloader';

// Simple batch loader
const userLoader = new DataLoader(async (ids: readonly string[]) => {
  console.log(`Batching ${ids.length} user requests`);

  const users = await db.users.findMany({
    where: { id: { in: [...ids] } }
  });

  // CRITICAL: Return users in same order as input IDs
  const userMap = new Map(users.map(u => [u.id, u]));
  return ids.map(id => userMap.get(id) ?? new Error(`User ${id} not found`));
});

// Usage in resolver
const resolvers = {
  Post: {
    async author(post: Post, args, context) {
      return context.loaders.userLoader.load(post.authorId);
    }
  }
};
```

### One-to-Many DataLoader

```typescript
// Load multiple items per key (e.g., posts per user)
const postsByUserLoader = new DataLoader(async (userIds: readonly string[]) => {
  const posts = await db.posts.findMany({
    where: { authorId: { in: [...userIds] } }
  });

  // Group posts by userId
  const grouped = new Map<string, Post[]>();
  userIds.forEach(id => grouped.set(id, []));

  posts.forEach(post => {
    const existing = grouped.get(post.authorId) || [];
    grouped.set(post.authorId, [...existing, post]);
  });

  return userIds.map(id => grouped.get(id) || []);
});

// Usage
const resolvers = {
  User: {
    async posts(user: User, args, context) {
      return context.loaders.postsByUserLoader.load(user.id);
    }
  }
};
```

### Many-to-Many DataLoader

```typescript
// Load related items through join table
const tagsByPostLoader = new DataLoader(async (postIds: readonly string[]) => {
  // Fetch all post-tag relationships
  const postTags = await db.postTags.findMany({
    where: { postId: { in: [...postIds] } },
    include: { tag: true }
  });

  // Group tags by postId
  const grouped = new Map<string, Tag[]>();
  postIds.forEach(id => grouped.set(id, []));

  postTags.forEach(pt => {
    const existing = grouped.get(pt.postId) || [];
    grouped.set(pt.postId, [...existing, pt.tag]);
  });

  return postIds.map(id => grouped.get(id) || []);
});
```

### DataLoader with Caching Options

```typescript
// Disable cache for frequently changing data
const liveDataLoader = new DataLoader(batchFn, {
  cache: false
});

// Custom cache key function
const userByEmailLoader = new DataLoader(
  async (emails: readonly string[]) => {
    // batch load
  },
  {
    cacheKeyFn: (email: string) => email.toLowerCase()
  }
);

// Prime the cache after mutation
async createUser(input: CreateUserInput) {
  const user = await db.users.create({ data: input });

  // Prime both loaders
  context.loaders.userLoader.prime(user.id, user);
  context.loaders.userByEmailLoader.prime(user.email, user);

  return user;
}

// Clear cache after update
async updateUser(id: string, input: UpdateUserInput) {
  const user = await db.users.update({
    where: { id },
    data: input
  });

  // Clear cache to force reload
  context.loaders.userLoader.clear(id);

  return user;
}
```

### DataLoader Error Handling

```typescript
const userLoader = new DataLoader(
  async (ids: readonly string[]) => {
    try {
      const users = await db.users.findMany({
        where: { id: { in: [...ids] } }
      });

      const userMap = new Map(users.map(u => [u.id, u]));

      return ids.map(id => {
        const user = userMap.get(id);
        if (!user) {
          // Return Error instance for individual failures
          return new Error(`User ${id} not found`);
        }
        return user;
      });
    } catch (error) {
      // Entire batch fails
      console.error('Batch load failed:', error);
      return ids.map(() => error);
    }
  },
  {
    // Max batch size
    maxBatchSize: 100,

    // Custom error handling
    cacheKeyFn: (key) => key
  }
);
```

## Query Optimization

### Select Only Needed Fields

```typescript
import { GraphQLResolveInfo } from 'graphql';
import graphqlFields from 'graphql-fields';

// Parse requested fields from query
function getRequestedFields(info: GraphQLResolveInfo): string[] {
  const fields = graphqlFields(info);
  return Object.keys(fields);
}

const resolvers = {
  Query: {
    async users(parent, args, context, info) {
      const requestedFields = getRequestedFields(info);

      // Only select requested fields from database
      return db.users.findMany({
        select: {
          id: requestedFields.includes('id'),
          name: requestedFields.includes('name'),
          email: requestedFields.includes('email'),
          // Don't load posts unless requested
          posts: requestedFields.includes('posts')
        }
      });
    }
  }
};
```

### Projection with Prisma

```typescript
import { parseResolveInfo } from '@apollo/client/utilities';

const resolvers = {
  Query: {
    async post(parent, { id }, context, info) {
      const parsedInfo = parseResolveInfo(info);

      // Build Prisma select based on requested fields
      const select = {
        id: true,
        title: true,
        content: !!parsedInfo?.fieldsByTypeName.Post?.content,
        author: !!parsedInfo?.fieldsByTypeName.Post?.author,
        comments: parsedInfo?.fieldsByTypeName.Post?.comments ? {
          select: {
            id: true,
            text: true,
            author: true
          }
        } : false
      };

      return db.posts.findUnique({
        where: { id },
        select
      });
    }
  }
};
```

### Database Query Batching

```typescript
// Use database transaction for multiple queries
const resolvers = {
  Query: {
    async dashboard(parent, args, context) {
      return db.$transaction(async (tx) => {
        const [user, posts, notifications, stats] = await Promise.all([
          tx.users.findUnique({ where: { id: context.userId } }),
          tx.posts.findMany({ where: { authorId: context.userId }, take: 10 }),
          tx.notifications.findMany({ where: { userId: context.userId }, take: 5 }),
          tx.stats.findUnique({ where: { userId: context.userId } })
        ]);

        return { user, posts, notifications, stats };
      });
    }
  }
};
```

## Caching Strategies

### Response Caching

```typescript
import { KeyvAdapter } from '@apollo/utils.keyvadapter';
import Keyv from 'keyv';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  cache: new KeyvAdapter(new Keyv('redis://localhost:6379')),

  plugins: [
    // Automatic Persisted Queries
    ApolloServerPluginUsageReporting({
      generateClientInfo: ({ request }) => {
        return {
          clientName: request.http?.headers.get('client-name') || 'unknown',
          clientVersion: request.http?.headers.get('client-version') || 'unknown'
        };
      }
    })
  ]
});
```

### Cache Control Directives

```graphql
# Schema with cache hints
type Query {
  # Cache for 5 minutes
  posts: [Post!]! @cacheControl(maxAge: 300)

  # Cache for 1 hour, public
  publicPosts: [Post!]! @cacheControl(maxAge: 3600, scope: PUBLIC)

  # Don't cache user-specific data
  me: User @cacheControl(maxAge: 0)
}

type Post {
  id: ID!
  title: String! @cacheControl(maxAge: 300)

  # Author changes rarely, cache for 1 day
  author: User! @cacheControl(maxAge: 86400)
}
```

```typescript
// Programmatic cache control
const resolvers = {
  Query: {
    posts(parent, args, context, info) {
      info.cacheControl.setCacheHint({ maxAge: 300, scope: 'PUBLIC' });
      return context.db.posts.findMany();
    }
  },

  Post: {
    author(parent, args, context, info) {
      // Cache author for 1 day
      info.cacheControl.setCacheHint({ maxAge: 86400 });
      return context.loaders.userLoader.load(parent.authorId);
    }
  }
};
```

### Field-Level Caching with Redis

```typescript
import Redis from 'ioredis';

const redis = new Redis();

const resolvers = {
  Query: {
    async expensiveQuery(parent, { id }, context) {
      const cacheKey = `query:expensive:${id}`;

      // Try cache first
      const cached = await redis.get(cacheKey);
      if (cached) {
        return JSON.parse(cached);
      }

      // Compute result
      const result = await performExpensiveOperation(id);

      // Cache for 5 minutes
      await redis.setex(cacheKey, 300, JSON.stringify(result));

      return result;
    }
  },

  Mutation: {
    async updatePost(parent, { id, input }, context) {
      const post = await db.posts.update({
        where: { id },
        data: input
      });

      // Invalidate related caches
      await redis.del(`post:${id}`);
      await redis.del(`posts:user:${post.authorId}`);

      return post;
    }
  }
};
```

## Database Optimization

### Eager Loading with Prisma

```typescript
// Without eager loading (N+1 problem)
const posts = await db.posts.findMany();
// Then for each post: await db.users.findUnique({ where: { id: post.authorId } })

// With eager loading (1 query)
const posts = await db.posts.findMany({
  include: {
    author: true,
    comments: {
      include: {
        author: true
      }
    }
  }
});
```

### Database Indexes

```prisma
// Schema with indexes
model Post {
  id        String   @id @default(cuid())
  title     String
  content   String
  authorId  String
  createdAt DateTime @default(now())
  status    String

  author    User     @relation(fields: [authorId], references: [id])

  // Single field indexes
  @@index([authorId])
  @@index([createdAt])
  @@index([status])

  // Compound index for common queries
  @@index([authorId, createdAt])
  @@index([status, createdAt])
}
```

### Query Analysis

```typescript
// Enable Prisma query logging
const prisma = new PrismaClient({
  log: [
    { emit: 'event', level: 'query' },
    { emit: 'stdout', level: 'error' }
  ]
});

prisma.$on('query', (e) => {
  console.log('Query: ' + e.query);
  console.log('Duration: ' + e.duration + 'ms');
});
```

## Automatic Persisted Queries (APQ)

```typescript
// Server configuration
import { ApolloServer } from '@apollo/server';
import { KeyvAdapter } from '@apollo/utils.keyvadapter';
import Keyv from 'keyv';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  persistedQueries: {
    cache: new KeyvAdapter(new Keyv('redis://localhost:6379')),
    ttl: 86400 // 24 hours
  }
});
```

```typescript
// Client implementation
import { createPersistedQueryLink } from '@apollo/client/link/persisted-queries';
import { sha256 } from 'crypto-hash';

const link = createPersistedQueryLink({ sha256 }).concat(httpLink);

const client = new ApolloClient({
  link,
  cache: new InMemoryCache()
});

// First request: sends full query + hash
// Subsequent requests: sends only hash (smaller payload)
```

## Monitoring and Profiling

### Apollo Studio Integration

```typescript
import { ApolloServerPluginUsageReporting } from '@apollo/server/plugin/usageReporting';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    ApolloServerPluginUsageReporting({
      sendVariableValues: { all: true },
      sendHeaders: { all: true }
    })
  ]
});
```

### Custom Performance Monitoring

```typescript
const performancePlugin = {
  async requestDidStart() {
    const start = Date.now();

    return {
      async willSendResponse({ response, context }) {
        const duration = Date.now() - start;

        console.log({
          operation: context.operation?.operation,
          duration,
          errors: response.errors?.length || 0
        });

        // Send to monitoring service
        if (duration > 1000) {
          console.warn('Slow query detected:', {
            duration,
            operation: context.operation?.name?.value
          });
        }
      }
    };
  }
};

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [performancePlugin]
});
```

### Query Complexity Tracking

```typescript
import { getComplexity, simpleEstimator, fieldExtensionsEstimator } from 'graphql-query-complexity';

const complexityPlugin = {
  async requestDidStart() {
    return {
      async didResolveOperation({ request, document, schema }) {
        const complexity = getComplexity({
          schema,
          operationName: request.operationName,
          query: document,
          variables: request.variables,
          estimators: [
            fieldExtensionsEstimator(),
            simpleEstimator({ defaultComplexity: 1 })
          ]
        });

        console.log('Query complexity:', complexity);

        if (complexity > 1000) {
          throw new GraphQLError('Query is too complex', {
            extensions: { code: 'BAD_USER_INPUT', complexity }
          });
        }
      }
    };
  }
};
```
