# Apollo Server

Specific guidance for Apollo Server implementations.

## Server Setup

### Basic Apollo Server 4

```typescript
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { typeDefs } from './schema';
import { resolvers } from './resolvers';

const server = new ApolloServer({
  typeDefs,
  resolvers,

  // Enable introspection in development only
  introspection: process.env.NODE_ENV !== 'production',

  // Include stack traces in errors (dev only)
  includeStacktraceInErrorResponses: process.env.NODE_ENV !== 'production'
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },

  context: async ({ req }) => ({
    userId: getUserIdFromToken(req.headers.authorization),
    dataSources: createDataSources(),
    db: prisma
  })
});

console.log(`🚀 Server ready at ${url}`);
```

### Apollo Server with Express

```typescript
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import express from 'express';
import http from 'http';
import cors from 'cors';
import bodyParser from 'body-parser';

const app = express();
const httpServer = http.createServer(app);

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    ApolloServerPluginDrainHttpServer({ httpServer })
  ]
});

await server.start();

app.use(
  '/graphql',
  cors<cors.CorsRequest>(),
  bodyParser.json(),
  expressMiddleware(server, {
    context: async ({ req }) => ({
      userId: getUserIdFromToken(req.headers.authorization),
      dataSources: createDataSources()
    })
  })
);

await new Promise<void>((resolve) => httpServer.listen({ port: 4000 }, resolve));
console.log(`🚀 Server ready at http://localhost:4000/graphql`);
```

## Apollo Server Plugins

### Custom Logging Plugin

```typescript
const loggingPlugin = {
  async requestDidStart(requestContext) {
    const start = Date.now();

    console.log('Request started:', {
      query: requestContext.request.query,
      variables: requestContext.request.variables,
      operationName: requestContext.request.operationName
    });

    return {
      async willSendResponse({ response }) {
        const duration = Date.now() - start;
        console.log('Request completed:', {
          duration: `${duration}ms`,
          errors: response.errors?.length || 0
        });
      },

      async didEncounterErrors({ errors }) {
        console.error('Request errors:', errors);
      }
    };
  }
};
```

### Authentication Plugin

```typescript
const authPlugin = {
  async requestDidStart() {
    return {
      async didResolveOperation({ request, operation, context }) {
        // Skip auth check for introspection
        if (operation.operation === 'introspection') {
          return;
        }

        // Check if operation requires auth
        const requiresAuth = checkOperationRequiresAuth(operation);

        if (requiresAuth && !context.userId) {
          throw new GraphQLError('Authentication required', {
            extensions: { code: 'UNAUTHENTICATED' }
          });
        }
      }
    };
  }
};
```

### Query Complexity Plugin

```typescript
import { getComplexity, simpleEstimator } from 'graphql-query-complexity';

const complexityPlugin = {
  async requestDidStart() {
    return {
      async didResolveOperation({ request, document, schema, context }) {
        const complexity = getComplexity({
          schema,
          operationName: request.operationName,
          query: document,
          variables: request.variables,
          estimators: [simpleEstimator({ defaultComplexity: 1 })]
        });

        // Log complexity
        console.log('Query complexity:', complexity);

        // Enforce limit
        const maxComplexity = context.userId ? 1000 : 100;
        if (complexity > maxComplexity) {
          throw new GraphQLError(`Query too complex: ${complexity} exceeds ${maxComplexity}`, {
            extensions: { code: 'BAD_USER_INPUT', complexity }
          });
        }
      }
    };
  }
};
```

## Data Sources

### REST Data Source

```typescript
import { RESTDataSource } from '@apollo/datasource-rest';

class UsersAPI extends RESTDataSource {
  override baseURL = 'https://api.example.com/';

  async getUser(id: string) {
    return this.get(`users/${id}`);
  }

  async getUsers() {
    return this.get('users');
  }

  async createUser(user: CreateUserInput) {
    return this.post('users', { body: user });
  }

  // Add caching
  override cacheKeyFor(url: string, request: RequestInit) {
    return `users:${url}`;
  }
}

// Use in context
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }) => ({
    dataSources: {
      usersAPI: new UsersAPI({ cache: server.cache })
    }
  })
});
```

### Database Data Source

```typescript
class DatabaseDataSource {
  private db: PrismaClient;

  constructor(db: PrismaClient) {
    this.db = db;
  }

  async getUser(id: string) {
    return this.db.user.findUnique({ where: { id } });
  }

  async getUserPosts(userId: string) {
    return this.db.post.findMany({ where: { authorId: userId } });
  }
}
```

## Error Handling

### Custom Error Classes

```typescript
import { GraphQLError, GraphQLErrorOptions } from 'graphql';

class AuthenticationError extends GraphQLError {
  constructor(message: string, options?: GraphQLErrorOptions) {
    super(message, {
      ...options,
      extensions: {
        ...options?.extensions,
        code: 'UNAUTHENTICATED'
      }
    });
  }
}

class ForbiddenError extends GraphQLError {
  constructor(message: string, options?: GraphQLErrorOptions) {
    super(message, {
      ...options,
      extensions: {
        ...options?.extensions,
        code: 'FORBIDDEN'
      }
    });
  }
}

class ValidationError extends GraphQLError {
  constructor(message: string, field?: string, options?: GraphQLErrorOptions) {
    super(message, {
      ...options,
      extensions: {
        ...options?.extensions,
        code: 'BAD_USER_INPUT',
        ...(field && { field })
      }
    });
  }
}

// Usage in resolvers
if (!context.userId) {
  throw new AuthenticationError('You must be logged in');
}

if (input.email && !isValidEmail(input.email)) {
  throw new ValidationError('Invalid email address', 'email');
}
```

### Error Formatting

```typescript
const server = new ApolloServer({
  typeDefs,
  resolvers,

  formatError: (formattedError, error) => {
    // Don't expose internal errors
    if (formattedError.extensions?.code === 'INTERNAL_SERVER_ERROR') {
      console.error('Internal error:', error);

      return {
        message: 'An internal error occurred',
        extensions: { code: 'INTERNAL_SERVER_ERROR' }
      };
    }

    // Log all errors
    console.error('GraphQL Error:', {
      message: formattedError.message,
      code: formattedError.extensions?.code,
      path: formattedError.path
    });

    return formattedError;
  }
});
```

## Subscriptions

### WebSocket Setup with Apollo Server

```typescript
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';
import { makeExecutableSchema } from '@graphql-tools/schema';

const schema = makeExecutableSchema({ typeDefs, resolvers });

// WebSocket server
const wsServer = new WebSocketServer({
  server: httpServer,
  path: '/graphql'
});

// Setup subscription handling
useServer(
  {
    schema,
    context: async (ctx) => {
      // Get token from connection params
      const token = ctx.connectionParams?.authorization;
      const userId = getUserIdFromToken(token);

      return {
        userId,
        pubsub
      };
    },

    onConnect: async (ctx) => {
      console.log('Client connected');
    },

    onDisconnect: (ctx) => {
      console.log('Client disconnected');
    }
  },
  wsServer
);
```

### PubSub Implementation

```typescript
import { RedisPubSub } from 'graphql-redis-subscriptions';
import Redis from 'ioredis';

const options = {
  host: process.env.REDIS_HOST,
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times: number) => Math.min(times * 50, 2000)
};

const pubsub = new RedisPubSub({
  publisher: new Redis(options),
  subscriber: new Redis(options)
});

// Publish events
await pubsub.publish('POST_CREATED', { postCreated: newPost });

// Subscribe in resolvers
const resolvers = {
  Subscription: {
    postCreated: {
      subscribe: () => pubsub.asyncIterator(['POST_CREATED'])
    }
  }
};
```

## Response Caching

### Apollo Server Cache

```typescript
import { KeyvAdapter } from '@apollo/utils.keyvadapter';
import Keyv from 'keyv';
import KeyvRedis from '@keyv/redis';

const redis = new KeyvRedis('redis://localhost:6379');
const cache = new KeyvAdapter(new Keyv({ store: redis }));

const server = new ApolloServer({
  typeDefs,
  resolvers,
  cache
});
```

### Cache Control

```typescript
// Schema-level cache control
const typeDefs = `
  type Query {
    posts: [Post!]! @cacheControl(maxAge: 300)
    user(id: ID!): User @cacheControl(maxAge: 600)
  }

  type Post @cacheControl(maxAge: 300) {
    id: ID!
    title: String!
  }
`;

// Resolver-level cache control
const resolvers = {
  Query: {
    posts(parent, args, context, info) {
      info.cacheControl.setCacheHint({ maxAge: 300, scope: 'PUBLIC' });
      return context.db.posts.findMany();
    }
  }
};
```

## Apollo Federation

### Subgraph Definition

```typescript
import { buildSubgraphSchema } from '@apollo/subgraph';

const typeDefs = gql`
  extend schema
    @link(url: "https://specs.apollo.dev/federation/v2.0",
          import: ["@key", "@shareable"])

  type User @key(fields: "id") {
    id: ID!
    email: String!
    name: String!
  }
`;

const resolvers = {
  User: {
    __resolveReference(reference: { id: string }) {
      return getUserById(reference.id);
    }
  }
};

const schema = buildSubgraphSchema({ typeDefs, resolvers });
```

### Gateway Setup

```typescript
import { ApolloGateway, IntrospectAndCompose } from '@apollo/gateway';

const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'users', url: 'http://localhost:4001/graphql' },
      { name: 'posts', url: 'http://localhost:4002/graphql' }
    ]
  })
});

const server = new ApolloServer({
  gateway
});
```

## Apollo Studio Integration

```typescript
import { ApolloServerPluginUsageReporting } from '@apollo/server/plugin/usageReporting';
import { ApolloServerPluginSchemaReporting } from '@apollo/server/plugin/schemaReporting';

const server = new ApolloServer({
  typeDefs,
  resolvers,

  plugins: [
    // Usage reporting
    ApolloServerPluginUsageReporting({
      sendVariableValues: { all: true },
      sendHeaders: { all: true }
    }),

    // Schema reporting
    ApolloServerPluginSchemaReporting()
  ]
});
```
