# GraphQL Yoga

Specific guidance for GraphQL Yoga implementations.

## Server Setup

### Basic GraphQL Yoga Server

```typescript
import { createYoga } from 'graphql-yoga';
import { createServer } from 'node:http';
import { schema } from './schema';

const yoga = createYoga({
  schema,

  // Context factory
  context: async ({ request }) => {
    const token = request.headers.get('authorization')?.replace('Bearer ', '');
    const userId = await getUserIdFromToken(token);

    return {
      userId,
      db: prisma,
      dataSources: createDataSources()
    };
  },

  // GraphiQL configuration
  graphiql: {
    title: 'My GraphQL API',
    defaultQuery: `
      query {
        posts {
          id
          title
        }
      }
    `
  }
});

const server = createServer(yoga);
server.listen(4000, () => {
  console.log('🚀 Server ready at http://localhost:4000/graphql');
});
```

### Yoga with Express

```typescript
import { createYoga } from 'graphql-yoga';
import express from 'express';

const app = express();

const yoga = createYoga({
  schema,

  // Use Express request/response
  graphqlEndpoint: '/graphql',

  context: ({ req }) => ({
    userId: getUserIdFromToken(req.headers.authorization),
    db: prisma
  })
});

app.use('/graphql', yoga);

app.listen(4000, () => {
  console.log('Server is running on http://localhost:4000/graphql');
});
```

## Schema Building

### Code-First with GraphQL Yoga

```typescript
import { createSchema } from 'graphql-yoga';

const schema = createSchema({
  typeDefs: `
    type Query {
      hello(name: String!): String!
      posts: [Post!]!
    }

    type Post {
      id: ID!
      title: String!
      content: String!
      author: User!
    }

    type User {
      id: ID!
      name: String!
    }
  `,

  resolvers: {
    Query: {
      hello: (_, { name }) => `Hello ${name}!`,
      posts: async (_, __, context) => {
        return context.db.posts.findMany();
      }
    },

    Post: {
      author: async (parent, _, context) => {
        return context.dataSources.userLoader.load(parent.authorId);
      }
    }
  }
});
```

## Plugins

### Logging Plugin

```typescript
import { Plugin } from 'graphql-yoga';

const loggingPlugin: Plugin = {
  onRequest({ request, url }) {
    console.log(`Request: ${request.method} ${url}`);
  },

  onResponse({ response }) {
    console.log(`Response: ${response.status}`);
  },

  onExecute({ args }) {
    const start = Date.now();

    return {
      onExecuteDone() {
        const duration = Date.now() - start;
        console.log(`Execution completed in ${duration}ms`);
      }
    };
  }
};

const yoga = createYoga({
  schema,
  plugins: [loggingPlugin]
});
```

### Authentication Plugin

```typescript
const authPlugin: Plugin = {
  onContextBuilding({ context, extendContext }) {
    const token = context.request.headers.get('authorization')?.replace('Bearer ', '');

    if (token) {
      try {
        const user = verifyToken(token);
        extendContext({ user, userId: user.id });
      } catch (error) {
        console.warn('Invalid token');
      }
    }
  }
};
```

### Error Masking Plugin

```typescript
import { Plugin } from 'graphql-yoga';

const errorMaskingPlugin: Plugin = {
  onResultProcess({ result, setResult }) {
    if (result.errors) {
      const maskedErrors = result.errors.map(error => {
        // Don't expose internal errors in production
        if (process.env.NODE_ENV === 'production' &&
            error.extensions?.code === 'INTERNAL_SERVER_ERROR') {
          return {
            message: 'An internal error occurred',
            extensions: { code: 'INTERNAL_SERVER_ERROR' }
          };
        }
        return error;
      });

      setResult({ ...result, errors: maskedErrors });
    }
  }
};
```

## File Uploads

```typescript
import { createSchema } from 'graphql-yoga';
import fs from 'fs/promises';
import path from 'path';

const schema = createSchema({
  typeDefs: `
    scalar File

    type Mutation {
      uploadFile(file: File!): UploadResult!
    }

    type UploadResult {
      success: Boolean!
      url: String
    }
  `,

  resolvers: {
    Mutation: {
      uploadFile: async (_, { file }) => {
        // File is already parsed by Yoga
        const uploadDir = './uploads';
        await fs.mkdir(uploadDir, { recursive: true });

        const filePath = path.join(uploadDir, file.name);
        const arrayBuffer = await file.arrayBuffer();
        await fs.writeFile(filePath, Buffer.from(arrayBuffer));

        return {
          success: true,
          url: `/uploads/${file.name}`
        };
      }
    }
  }
});

// Client usage (multipart form data):
// const formData = new FormData();
// formData.append('operations', JSON.stringify({
//   query: 'mutation ($file: File!) { uploadFile(file: $file) { url } }',
//   variables: { file: null }
// }));
// formData.append('map', JSON.stringify({ '0': ['variables.file'] }));
// formData.append('0', fileBlob);
```

## Subscriptions

### Server-Sent Events (SSE)

```typescript
import { createYoga, createPubSub } from 'graphql-yoga';

const pubsub = createPubSub();

const schema = createSchema({
  typeDefs: `
    type Subscription {
      countdown(from: Int!): Int!
      postCreated: Post!
    }

    type Mutation {
      createPost(input: CreatePostInput!): Post!
    }
  `,

  resolvers: {
    Subscription: {
      countdown: {
        async *subscribe(_, { from }) {
          for (let i = from; i >= 0; i--) {
            yield { countdown: i };
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      },

      postCreated: {
        subscribe: () => pubsub.subscribe('POST_CREATED')
      }
    },

    Mutation: {
      createPost: async (_, { input }, context) => {
        const post = await context.db.posts.create({ data: input });
        pubsub.publish('POST_CREATED', { postCreated: post });
        return post;
      }
    }
  }
});

const yoga = createYoga({ schema });
```

### WebSocket Subscriptions

```typescript
import { createYoga, createPubSub } from 'graphql-yoga';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';

const pubsub = createPubSub();

const yoga = createYoga({
  schema,
  graphiql: {
    subscriptionsProtocol: 'WS'
  }
});

const server = createServer(yoga);

const wsServer = new WebSocketServer({
  server,
  path: yoga.graphqlEndpoint
});

useServer(
  {
    schema: yoga.schema,
    execute: (args: any) => args.rootValue.execute(args),
    subscribe: (args: any) => args.rootValue.subscribe(args),
    onSubscribe: async (ctx, msg) => {
      const { schema, execute, subscribe, contextFactory, parse, validate } = yoga.getEnveloped({
        ...ctx,
        req: ctx.extra.request,
        socket: ctx.extra.socket,
        params: msg.payload
      });

      const args = {
        schema,
        operationName: msg.payload.operationName,
        document: parse(msg.payload.query),
        variableValues: msg.payload.variables,
        contextValue: await contextFactory(),
        rootValue: {
          execute,
          subscribe
        }
      };

      const errors = validate(args.schema, args.document);
      if (errors.length) return errors;

      return args;
    }
  },
  wsServer
);

server.listen(4000);
```

## Response Caching

### HTTP Caching

```typescript
import { useResponseCache } from '@graphql-yoga/plugin-response-cache';
import { createYoga } from 'graphql-yoga';

const yoga = createYoga({
  schema,

  plugins: [
    useResponseCache({
      // Cache based on session
      session: (request) => {
        return request.headers.get('authorization') || null;
      },

      // TTL in milliseconds
      ttl: 60_000, // 1 minute

      // Include extension in response
      includeExtensionMetadata: true
    })
  ]
});
```

### Cache Control

```typescript
const schema = createSchema({
  typeDefs: `
    type Query {
      posts: [Post!]! @cacheControl(maxAge: 300)
      me: User @cacheControl(maxAge: 0)
    }
  `,
  resolvers: {
    Query: {
      posts: async (_, __, context, info) => {
        // Programmatically set cache control
        info.cacheControl?.setCacheHint({ maxAge: 300, scope: 'PUBLIC' });
        return context.db.posts.findMany();
      }
    }
  }
});
```

## Rate Limiting

```typescript
import { useRateLimiter } from '@envelop/rate-limiter';

const yoga = createYoga({
  schema,

  plugins: [
    useRateLimiter({
      // Global limit
      max: 100,
      window: '15m',

      // Per-field limits
      fieldLimits: {
        'Mutation.sendEmail': {
          max: 5,
          window: '1h'
        },
        'Mutation.createPost': {
          max: 10,
          window: '1h'
        }
      },

      // Identify users
      identifyFn: (context) => {
        return context.userId || context.request.headers.get('x-forwarded-for');
      }
    })
  ]
});
```

## Depth Limiting

```typescript
import { useDepthLimit } from '@envelop/depth-limit';

const yoga = createYoga({
  schema,

  plugins: [
    useDepthLimit({
      maxDepth: 10,

      // Ignore certain fields from depth calculation
      ignore: ['node', '__typename']
    })
  ]
});
```

## CORS Configuration

```typescript
const yoga = createYoga({
  schema,

  cors: {
    origin: ['http://localhost:3000', 'https://myapp.com'],
    credentials: true,
    methods: ['POST'],
    allowedHeaders: ['Content-Type', 'Authorization']
  }
});
```

## Envelop Plugins Integration

```typescript
import { envelop, useLogger, useSchema, useTiming } from '@envelop/core';
import { useGenericAuth } from '@envelop/generic-auth';
import { useParserCache } from '@envelop/parser-cache';
import { useValidationCache } from '@envelop/validation-cache';

const getEnveloped = envelop({
  plugins: [
    useSchema(schema),
    useLogger(),
    useTiming(),
    useParserCache(),
    useValidationCache(),

    useGenericAuth({
      resolveUserFn: async (context) => {
        const token = context.request.headers.get('authorization');
        if (!token) return null;

        try {
          return await verifyToken(token);
        } catch {
          return null;
        }
      },

      mode: 'protect-granular',

      // Protect specific fields
      authConfig: {
        'Query.me': true,
        'Mutation.createPost': true,
        'Mutation.deletePost': { requires: 'admin' }
      }
    })
  ]
});

const yoga = createYoga({
  schema,
  plugins: [getEnveloped]
});
```
