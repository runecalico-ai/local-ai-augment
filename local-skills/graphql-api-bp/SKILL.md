---
name: graphql-api-bp
description: Expert GraphQL API development with modern best practices. Use when designing, implementing, or reviewing GraphQL schemas, resolvers, queries, mutations, subscriptions, or GraphQL server implementations. Covers schema design, type safety, performance optimization (N+1 problem, DataLoader), error handling, security, authentication/authorization, and GraphQL-specific patterns. Apply when working with GraphQL servers (Apollo, GraphQL Yoga, etc.) or client implementations.
---

# GraphQL API Best Practices

Expert guidance for building robust, performant, and secure GraphQL APIs with modern tooling and patterns.

## When to Use This Skill

- Designing GraphQL schemas and type definitions
- Implementing resolvers, queries, mutations, and subscriptions
- Reviewing or refactoring GraphQL server code
- Optimizing GraphQL performance (N+1 queries, caching, DataLoader)
- Implementing authentication and authorization in GraphQL
- Error handling and validation in GraphQL APIs
- Setting up GraphQL servers (Apollo Server, GraphQL Yoga, etc.)
- Client-side GraphQL implementations and query optimization
- GraphQL security hardening (depth limiting, query complexity)

## Core Principles

### GraphQL Philosophy

- **Type safety first**: Leverage GraphQL's strong type system
- **Client-driven**: Let clients specify exactly what they need
- **Single endpoint**: One endpoint for all data needs
- **Introspectable**: Self-documenting through introspection
- **Evolutionary**: Add fields without versioning
- **Performance-conscious**: Solve N+1 problems, batch requests
- **Security-minded**: Rate limiting, depth limiting, query complexity analysis

### API Design Standards

- **Schema-first development**: Define schema before implementation
- **Nullable by default**: Make fields non-null only when guaranteed
- **Descriptive naming**: Clear, consistent field and type names
- **Pagination everywhere**: Use connection patterns for lists
- **Error handling**: Return structured errors with useful context
- **Authorization at field level**: Implement fine-grained permissions

## Quick Reference

### Schema Design Patterns

```graphql
# Type definitions with descriptions
"""
Represents a user in the system
"""
type User {
  """Unique identifier"""
  id: ID!
  """User's email address"""
  email: String!
  """User's display name"""
  name: String!
  """User's creation timestamp"""
  createdAt: DateTime!
  """Posts authored by this user"""
  posts(
    first: Int
    after: String
    orderBy: PostOrderBy
  ): PostConnection!
}

# Connection pattern for pagination (Relay spec)
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Input types for mutations
input CreatePostInput {
  title: String!
  content: String!
  tags: [String!]
}

# Union types for polymorphic returns
union SearchResult = User | Post | Comment

# Interface for common fields
interface Node {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Enums for constrained values
enum PostStatus {
  DRAFT
  PUBLISHED
  ARCHIVED
}

# Custom scalars
scalar DateTime
scalar EmailAddress
scalar URL
```

### Resolver Implementation

**JavaScript/TypeScript with Apollo Server:**

```typescript
import { GraphQLError } from 'graphql';
import DataLoader from 'dataloader';

// Context type with authentication and data loaders
interface Context {
  userId?: string;
  dataSources: {
    userLoader: DataLoader<string, User>;
    postLoader: DataLoader<string, Post>;
  };
  db: DatabaseClient;
}

// Type-safe resolvers
const resolvers = {
  Query: {
    // Simple query with authentication check
    async me(parent, args, context: Context) {
      if (!context.userId) {
        throw new GraphQLError('Authentication required', {
          extensions: { code: 'UNAUTHENTICATED' }
        });
      }
      return context.dataSources.userLoader.load(context.userId);
    },

    // Query with arguments and pagination
    async posts(
      parent,
      { first = 10, after, orderBy }: PostsArgs,
      context: Context
    ) {
      // Validate input
      if (first > 100) {
        throw new GraphQLError('Cannot request more than 100 items', {
          extensions: { code: 'BAD_USER_INPUT' }
        });
      }

      const results = await context.db.posts.findMany({
        take: first + 1,
        cursor: after ? { id: after } : undefined,
        orderBy: orderBy || { createdAt: 'desc' }
      });

      const hasNextPage = results.length > first;
      const edges = results.slice(0, first).map(post => ({
        node: post,
        cursor: post.id
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!after,
          startCursor: edges[0]?.cursor,
          endCursor: edges[edges.length - 1]?.cursor
        }
      };
    }
  },

  Mutation: {
    // Mutation with input validation and authorization
    async createPost(
      parent,
      { input }: { input: CreatePostInput },
      context: Context
    ) {
      if (!context.userId) {
        throw new GraphQLError('Authentication required', {
          extensions: { code: 'UNAUTHENTICATED' }
        });
      }

      // Validate input
      if (!input.title?.trim()) {
        throw new GraphQLError('Title is required', {
          extensions: {
            code: 'BAD_USER_INPUT',
            field: 'title'
          }
        });
      }

      const post = await context.db.posts.create({
        data: {
          ...input,
          authorId: context.userId
        }
      });

      return { post };
    },

    // Update mutation with optimistic concurrency control
    async updatePost(
      parent,
      { id, input, version }: UpdatePostArgs,
      context: Context
    ) {
      const post = await context.dataSources.postLoader.load(id);

      // Authorization check
      if (post.authorId !== context.userId) {
        throw new GraphQLError('Not authorized to update this post', {
          extensions: { code: 'FORBIDDEN' }
        });
      }

      // Optimistic concurrency check
      if (post.version !== version) {
        throw new GraphQLError('Post was modified by another user', {
          extensions: { code: 'CONFLICT' }
        });
      }

      return context.db.posts.update({
        where: { id },
        data: { ...input, version: version + 1 }
      });
    }
  },

  // Field-level resolver with DataLoader (solves N+1)
  User: {
    async posts(parent: User, args, context: Context) {
      return context.db.posts.findMany({
        where: { authorId: parent.id }
      });
    },

    // Computed field
    async fullName(parent: User) {
      return `${parent.firstName} ${parent.lastName}`;
    }
  },

  // Subscription resolver
  Subscription: {
    postCreated: {
      subscribe: (parent, args, context: Context) => {
        if (!context.userId) {
          throw new GraphQLError('Authentication required');
        }
        return context.pubsub.asyncIterator(['POST_CREATED']);
      }
    }
  },

  // Union type resolver
  SearchResult: {
    __resolveType(obj: any) {
      if (obj.email) return 'User';
      if (obj.title) return 'Post';
      if (obj.text) return 'Comment';
      return null;
    }
  }
};
```

**Python with Strawberry/Ariadne:**

```python
import strawberry
from typing import Optional, List
from strawberry.types import Info
from dataclasses import dataclass

@strawberry.type
class User:
    id: strawberry.ID
    email: str
    name: str
    created_at: datetime

    @strawberry.field
    async def posts(self, info: Info) -> List['Post']:
        # Use DataLoader from context to avoid N+1
        return await info.context.loaders.posts_by_user.load(self.id)

@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: Info) -> Optional[User]:
        user_id = info.context.user_id
        if not user_id:
            raise PermissionError("Authentication required")
        return await info.context.loaders.user.load(user_id)

    @strawberry.field
    async def posts(
        self,
        info: Info,
        first: int = 10,
        after: Optional[str] = None
    ) -> PostConnection:
        if first > 100:
            raise ValueError("Cannot request more than 100 items")

        # Implementation with pagination
        # ...

@strawberry.input
class CreatePostInput:
    title: str
    content: str
    tags: List[str] = strawberry.field(default_factory=list)

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_post(
        self,
        info: Info,
        input: CreatePostInput
    ) -> Post:
        if not info.context.user_id:
            raise PermissionError("Authentication required")

        # Create post
        # ...
```

### DataLoader Pattern (Solving N+1 Problem)

**TypeScript:**

```typescript
import DataLoader from 'dataloader';

// Batch function for loading users
async function batchLoadUsers(ids: readonly string[]): Promise<User[]> {
  const users = await db.users.findMany({
    where: { id: { in: [...ids] } }
  });

  // Return in same order as requested IDs
  const userMap = new Map(users.map(u => [u.id, u]));
  return ids.map(id => userMap.get(id) || new Error(`User ${id} not found`));
}

// Create DataLoader instance per request
function createLoaders(db: DatabaseClient) {
  return {
    userLoader: new DataLoader(batchLoadUsers),
    postLoader: new DataLoader(async (ids: readonly string[]) => {
      const posts = await db.posts.findMany({
        where: { id: { in: [...ids] } }
      });
      const postMap = new Map(posts.map(p => [p.id, p]));
      return ids.map(id => postMap.get(id) || new Error(`Post ${id} not found`));
    }),
    // Loader for one-to-many relationships
    postsByUserLoader: new DataLoader(async (userIds: readonly string[]) => {
      const posts = await db.posts.findMany({
        where: { authorId: { in: [...userIds] } }
      });

      // Group posts by userId
      const grouped = new Map<string, Post[]>();
      posts.forEach(post => {
        const existing = grouped.get(post.authorId) || [];
        grouped.set(post.authorId, [...existing, post]);
      });

      return userIds.map(id => grouped.get(id) || []);
    })
  };
}
```

### Error Handling Best Practices

```typescript
import { GraphQLError } from 'graphql';

// Standard error codes
enum ErrorCode {
  UNAUTHENTICATED = 'UNAUTHENTICATED',
  FORBIDDEN = 'FORBIDDEN',
  BAD_USER_INPUT = 'BAD_USER_INPUT',
  NOT_FOUND = 'NOT_FOUND',
  INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR',
  CONFLICT = 'CONFLICT'
}

// Error factory functions
function createAuthError(message = 'Authentication required') {
  return new GraphQLError(message, {
    extensions: { code: ErrorCode.UNAUTHENTICATED }
  });
}

function createForbiddenError(message = 'Access denied') {
  return new GraphQLError(message, {
    extensions: { code: ErrorCode.FORBIDDEN }
  });
}

function createValidationError(message: string, field?: string) {
  return new GraphQLError(message, {
    extensions: {
      code: ErrorCode.BAD_USER_INPUT,
      ...(field && { field })
    }
  });
}

// Error formatting for production
function formatError(formattedError: GraphQLFormattedError, error: unknown) {
  // Don't expose internal errors in production
  if (formattedError.extensions?.code === 'INTERNAL_SERVER_ERROR') {
    // Log full error server-side
    console.error('GraphQL Error:', error);

    // Return sanitized error to client
    return {
      message: 'An internal error occurred',
      extensions: { code: 'INTERNAL_SERVER_ERROR' }
    };
  }

  return formattedError;
}
```

### Security Best Practices

```typescript
import { createComplexityLimitRule } from 'graphql-validation-complexity';
import depthLimit from 'graphql-depth-limit';

// Apollo Server configuration with security plugins
const server = new ApolloServer({
  typeDefs,
  resolvers,

  // Depth limiting (prevent deeply nested queries)
  validationRules: [
    depthLimit(7), // Max query depth of 7
    createComplexityLimitRule(1000, {
      // Custom complexity calculation
      scalarCost: 1,
      objectCost: 5,
      listFactor: 10
    })
  ],

  // Introspection and playground disabled in production
  introspection: process.env.NODE_ENV !== 'production',

  // Error formatting
  formatError,

  plugins: [
    // Query complexity logging
    {
      async requestDidStart() {
        return {
          async didResolveOperation(requestContext) {
            const complexity = calculateComplexity(requestContext.operation);
            if (complexity > 1000) {
              throw new GraphQLError('Query is too complex', {
                extensions: {
                  code: 'BAD_USER_INPUT',
                  complexity
                }
              });
            }
          }
        };
      }
    }
  ]
});

// Rate limiting middleware
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
});

app.use('/graphql', limiter);

// Query cost analysis
const queryComplexity: GraphQLSchemaExtensions = {
  complexity: {
    User: { posts: 10 },      // Loading posts is expensive
    Post: { comments: 10 },   // Loading comments is expensive
    Query: {
      users: ({ args }) => args.first * 5,  // Cost scales with pagination
      search: 50  // Search is expensive
    }
  }
};
```

### Field-Level Authorization

```typescript
// Authorization directive
import { mapSchema, getDirective, MapperKind } from '@graphql-tools/utils';
import { defaultFieldResolver } from 'graphql';

function authDirective(schema: GraphQLSchema, directiveName: string) {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const authDirective = getDirective(schema, fieldConfig, directiveName)?.[0];

      if (authDirective) {
        const { requires } = authDirective;
        const { resolve = defaultFieldResolver } = fieldConfig;

        fieldConfig.resolve = async (source, args, context, info) => {
          // Check if user has required role
          if (!context.user?.roles?.includes(requires)) {
            throw new GraphQLError('Not authorized', {
              extensions: { code: 'FORBIDDEN' }
            });
          }

          return resolve(source, args, context, info);
        };
      }

      return fieldConfig;
    }
  });
}

// Schema with auth directive
const typeDefs = `
  directive @auth(requires: Role!) on FIELD_DEFINITION

  enum Role {
    ADMIN
    USER
  }

  type User {
    id: ID!
    email: String!
    name: String!
    # Only admins can see all users' private data
    privateData: PrivateData @auth(requires: ADMIN)
  }
`;

// Alternative: Resolver-level authorization
const resolvers = {
  User: {
    async privateData(parent: User, args, context: Context) {
      // Check authorization
      if (!context.user?.roles?.includes('ADMIN')) {
        if (context.user?.id !== parent.id) {
          return null; // Hide field for unauthorized users
        }
      }

      return context.dataSources.privateDataLoader.load(parent.id);
    }
  }
};
```

## Advanced Patterns

### Real-time with Subscriptions

```typescript
import { PubSub } from 'graphql-subscriptions';
import { withFilter } from 'graphql-subscriptions';

const pubsub = new PubSub();

const resolvers = {
  Mutation: {
    async createPost(parent, { input }, context: Context) {
      const post = await context.db.posts.create({ data: input });

      // Publish event
      await pubsub.publish('POST_CREATED', {
        postCreated: post,
        authorId: post.authorId
      });

      return { post };
    }
  },

  Subscription: {
    // Basic subscription
    postCreated: {
      subscribe: () => pubsub.asyncIterator(['POST_CREATED'])
    },

    // Filtered subscription (only posts from followed users)
    postCreatedByFollowing: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['POST_CREATED']),
        async (payload, variables, context: Context) => {
          // Check if current user follows the post author
          const following = await context.db.follows.findFirst({
            where: {
              followerId: context.userId,
              followingId: payload.authorId
            }
          });
          return !!following;
        }
      )
    }
  }
};
```

### Batch Mutations

```graphql
# Schema
input CreatePostsInput {
  posts: [CreatePostInput!]!
}

type CreatePostsPayload {
  posts: [Post!]!
  errors: [MutationError!]!
}

type MutationError {
  message: String!
  path: [String!]!
}

type Mutation {
  createPosts(input: CreatePostsInput!): CreatePostsPayload!
}
```

```typescript
// Resolver with partial success handling
const resolvers = {
  Mutation: {
    async createPosts(parent, { input }, context: Context) {
      const results = await Promise.allSettled(
        input.posts.map(post =>
          context.db.posts.create({ data: post })
        )
      );

      const posts: Post[] = [];
      const errors: MutationError[] = [];

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          posts.push(result.value);
        } else {
          errors.push({
            message: result.reason.message,
            path: [`posts[${index}]`]
          });
        }
      });

      return { posts, errors };
    }
  }
};
```

### File Uploads

```typescript
import { GraphQLUpload } from 'graphql-upload-ts';

const typeDefs = `
  scalar Upload

  type Mutation {
    uploadFile(file: Upload!): File!
    uploadFiles(files: [Upload!]!): [File!]!
  }
`;

const resolvers = {
  Upload: GraphQLUpload,

  Mutation: {
    async uploadFile(parent, { file }) {
      const { createReadStream, filename, mimetype } = await file;

      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
      if (!allowedTypes.includes(mimetype)) {
        throw new GraphQLError('Invalid file type', {
          extensions: { code: 'BAD_USER_INPUT' }
        });
      }

      // Stream to storage (S3, local, etc.)
      const stream = createReadStream();
      const url = await uploadToS3(stream, filename);

      return {
        url,
        filename,
        mimetype
      };
    }
  }
};
```

## Performance Optimization

### Caching Strategies

```typescript
import { KeyvAdapter } from '@apollo/utils.keyvadapter';
import Keyv from 'keyv';

const server = new ApolloServer({
  typeDefs,
  resolvers,

  // Response caching
  cache: new KeyvAdapter(new Keyv()),

  plugins: [
    // Cache control hints
    {
      async requestDidStart() {
        return {
          async willSendResponse({ response, context }) {
            // Set cache control headers
            response.http?.headers.set(
              'Cache-Control',
              'max-age=300, public'
            );
          }
        };
      }
    }
  ]
});

// Field-level cache hints
const resolvers = {
  Query: {
    posts: (parent, args, context, info) => {
      // Add cache hint
      info.cacheControl.setCacheHint({ maxAge: 60 });
      return context.db.posts.findMany();
    }
  }
};

// Schema-level cache control
const typeDefs = `
  type Query {
    posts: [Post!]! @cacheControl(maxAge: 60)
    user(id: ID!): User @cacheControl(maxAge: 300)
  }
`;
```

### Persisted Queries

```typescript
// Automatic Persisted Queries (APQ)
import { ApolloServerPluginUsageReporting } from '@apollo/server/plugin/usageReporting';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  persistedQueries: {
    cache: new KeyvAdapter(new Keyv())
  }
});

// Client sends hash instead of full query
// First request: send query + hash
// Subsequent requests: send only hash
```

## Testing GraphQL APIs

```typescript
import { ApolloServer } from '@apollo/server';
import { createTestClient } from 'apollo-server-testing';

describe('GraphQL API', () => {
  let server: ApolloServer;
  let query: any;
  let mutate: any;

  beforeEach(() => {
    server = new ApolloServer({
      typeDefs,
      resolvers
    });

    const testClient = createTestClient(server);
    query = testClient.query;
    mutate = testClient.mutate;
  });

  it('should fetch user by id', async () => {
    const { data } = await query({
      query: gql`
        query GetUser($id: ID!) {
          user(id: $id) {
            id
            name
            email
          }
        }
      `,
      variables: { id: '1' }
    });

    expect(data.user).toEqual({
      id: '1',
      name: 'John Doe',
      email: 'john@example.com'
    });
  });

  it('should handle authentication errors', async () => {
    const { errors } = await query({
      query: gql`
        query { me { id } }
      `
    });

    expect(errors[0].extensions.code).toBe('UNAUTHENTICATED');
  });

  it('should create post with valid input', async () => {
    const { data } = await mutate({
      mutation: gql`
        mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            post { id title }
          }
        }
      `,
      variables: {
        input: { title: 'Test Post', content: 'Content' }
      },
      context: { userId: '1' }
    });

    expect(data.createPost.post.title).toBe('Test Post');
  });
});
```

## Common Anti-Patterns to Avoid

❌ **Don't: Return nullable arrays**
```graphql
type User {
  posts: [Post!]  # Can be null - bad!
}
```

✅ **Do: Return empty arrays instead**
```graphql
type User {
  posts: [Post!]!  # Always returns array (may be empty)
}
```

❌ **Don't: Ignore N+1 queries**
```typescript
// Resolver that causes N+1
User: {
  async posts(parent: User) {
    return db.posts.findMany({ where: { authorId: parent.id } });
  }
}
```

✅ **Do: Use DataLoader**
```typescript
User: {
  async posts(parent: User, args, context: Context) {
    return context.dataSources.postsByUserLoader.load(parent.id);
  }
}
```

❌ **Don't: Throw generic errors**
```typescript
throw new Error('Something went wrong');
```

✅ **Do: Use typed GraphQL errors**
```typescript
throw new GraphQLError('User not found', {
  extensions: { code: 'NOT_FOUND', userId }
});
```

❌ **Don't: Allow unlimited pagination**
```typescript
async posts(parent, { first }) {
  return db.posts.findMany({ take: first }); // No limit!
}
```

✅ **Do: Enforce maximum limits**
```typescript
async posts(parent, { first = 10 }) {
  if (first > 100) {
    throw new GraphQLError('Cannot request more than 100 items');
  }
  return db.posts.findMany({ take: first });
}
```

## Reference Documentation

For detailed patterns and implementation guides, see:

- **[Schema Design Patterns](references/schema-patterns.md)** - Advanced schema design, interfaces, unions, relay spec
- **[Performance Optimization](references/performance.md)** - DataLoader patterns, caching strategies, query optimization
- **[Security Hardening](references/security.md)** - Authentication, authorization, query complexity, rate limiting
- **[Testing Strategies](references/testing.md)** - Unit tests, integration tests, schema testing

## Framework-Specific Guidance

When working with specific GraphQL frameworks:

- **Apollo Server**: See [references/apollo-server.md](references/apollo-server.md)
- **GraphQL Yoga**: See [references/graphql-yoga.md](references/graphql-yoga.md)
- **Strawberry (Python)**: See [references/strawberry.md](references/strawberry.md)
- **Ariadne (Python)**: See [references/ariadne.md](references/ariadne.md)
- **GraphQL.NET (C#)**: See [references/graphql-dotnet.md](references/graphql-dotnet.md)

Load the appropriate reference file based on the framework being used.
