# Security Hardening

Comprehensive security best practices for GraphQL APIs.

## Authentication Strategies

### JWT Authentication

```typescript
import jwt from 'jsonwebtoken';
import { GraphQLError } from 'graphql';

interface JWTPayload {
  userId: string;
  email: string;
  roles: string[];
}

// Verify JWT token
function verifyToken(token: string): JWTPayload {
  try {
    return jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload;
  } catch (error) {
    throw new GraphQLError('Invalid or expired token', {
      extensions: { code: 'UNAUTHENTICATED' }
    });
  }
}

// Context creation with authentication
async function createContext({ req }): Promise<Context> {
  const authHeader = req.headers.authorization || '';
  const token = authHeader.replace('Bearer ', '');

  let user: JWTPayload | null = null;

  if (token) {
    try {
      user = verifyToken(token);
    } catch (error) {
      // Log but don't throw - allow introspection queries
      console.warn('Invalid token:', error);
    }
  }

  return {
    user,
    userId: user?.userId,
    dataSources: createDataSources(),
    db
  };
}

const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: createContext
});
```

### Session-Based Authentication

```typescript
import session from 'express-session';
import RedisStore from 'connect-redis';
import Redis from 'ioredis';

const redis = new Redis();

app.use(
  session({
    store: new RedisStore({ client: redis }),
    secret: process.env.SESSION_SECRET!,
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: process.env.NODE_ENV === 'production',
      httpOnly: true,
      maxAge: 1000 * 60 * 60 * 24 * 7 // 1 week
    }
  })
);

// Context with session
async function createContext({ req }): Promise<Context> {
  return {
    userId: req.session?.userId,
    db,
    dataSources: createDataSources()
  };
}
```

### API Key Authentication

```typescript
// Context with API key validation
async function createContext({ req }): Promise<Context> {
  const apiKey = req.headers['x-api-key'] as string;

  if (!apiKey) {
    return { db, dataSources: createDataSources() };
  }

  // Validate API key
  const client = await db.apiClients.findUnique({
    where: { apiKey }
  });

  if (!client) {
    throw new GraphQLError('Invalid API key', {
      extensions: { code: 'UNAUTHENTICATED' }
    });
  }

  // Check rate limits
  const usage = await redis.incr(`api:${apiKey}:${getCurrentHour()}`);
  if (usage > client.rateLimit) {
    throw new GraphQLError('Rate limit exceeded', {
      extensions: { code: 'TOO_MANY_REQUESTS' }
    });
  }

  return {
    client,
    clientId: client.id,
    db,
    dataSources: createDataSources()
  };
}
```

## Authorization Patterns

### Resolver-Level Authorization

```typescript
// Authorization helper
function requireAuth(context: Context) {
  if (!context.userId) {
    throw new GraphQLError('Authentication required', {
      extensions: { code: 'UNAUTHENTICATED' }
    });
  }
}

function requireRole(context: Context, role: string) {
  requireAuth(context);
  if (!context.user?.roles?.includes(role)) {
    throw new GraphQLError(`Requires ${role} role`, {
      extensions: { code: 'FORBIDDEN' }
    });
  }
}

const resolvers = {
  Query: {
    async adminUsers(parent, args, context: Context) {
      requireRole(context, 'admin');
      return context.db.users.findMany();
    },

    async me(parent, args, context: Context) {
      requireAuth(context);
      return context.loaders.userLoader.load(context.userId!);
    }
  },

  Mutation: {
    async deleteUser(parent, { id }, context: Context) {
      requireRole(context, 'admin');
      return context.db.users.delete({ where: { id } });
    }
  }
};
```

### Directive-Based Authorization

```graphql
# Schema with auth directives
directive @auth(requires: Role = USER) on OBJECT | FIELD_DEFINITION

enum Role {
  ADMIN
  USER
  GUEST
}

type Query {
  publicPosts: [Post!]!
  me: User @auth
  adminDashboard: Dashboard @auth(requires: ADMIN)
}

type Mutation {
  createPost(input: CreatePostInput!): Post! @auth
  deleteAnyPost(id: ID!): Boolean! @auth(requires: ADMIN)
}
```

```typescript
import { mapSchema, getDirective, MapperKind } from '@graphql-tools/utils';
import { defaultFieldResolver, GraphQLSchema } from 'graphql';

function authDirectiveTransformer(schema: GraphQLSchema) {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const authDirective = getDirective(schema, fieldConfig, 'auth')?.[0];

      if (authDirective) {
        const { requires = 'USER' } = authDirective;
        const { resolve = defaultFieldResolver } = fieldConfig;

        fieldConfig.resolve = async function (source, args, context, info) {
          if (!context.userId) {
            throw new GraphQLError('Authentication required', {
              extensions: { code: 'UNAUTHENTICATED' }
            });
          }

          if (requires !== 'USER' && !context.user?.roles?.includes(requires)) {
            throw new GraphQLError(`Requires ${requires} role`, {
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

// Apply directive transformer
const schema = authDirectiveTransformer(executableSchema);
```

### Field-Level Authorization

```typescript
// Hide sensitive fields for unauthorized users
const resolvers = {
  User: {
    email(parent: User, args, context: Context) {
      // Only show email to the user themselves or admins
      if (context.userId === parent.id || context.user?.roles?.includes('ADMIN')) {
        return parent.email;
      }
      return null;
    },

    phoneNumber(parent: User, args, context: Context) {
      // Always hide phone number from other users
      if (context.userId !== parent.id) {
        return null;
      }
      return parent.phoneNumber;
    }
  },

  Post: {
    async content(parent: Post, args, context: Context) {
      // Show full content only for published posts or author
      if (parent.status === 'PUBLISHED' || parent.authorId === context.userId) {
        return parent.content;
      }

      // Show excerpt for drafts
      return parent.content.substring(0, 100) + '...';
    }
  }
};
```

### Resource-Based Authorization

```typescript
// Check ownership before allowing operations
const resolvers = {
  Mutation: {
    async updatePost(parent, { id, input }, context: Context) {
      requireAuth(context);

      const post = await context.db.posts.findUnique({ where: { id } });

      if (!post) {
        throw new GraphQLError('Post not found', {
          extensions: { code: 'NOT_FOUND' }
        });
      }

      // Check ownership
      if (post.authorId !== context.userId && !context.user?.roles?.includes('ADMIN')) {
        throw new GraphQLError('Not authorized to update this post', {
          extensions: { code: 'FORBIDDEN' }
        });
      }

      return context.db.posts.update({
        where: { id },
        data: input
      });
    }
  }
};
```

## Query Complexity Limits

### Complexity Calculation

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
            // Custom complexity for specific fields
            fieldExtensionsEstimator(),

            // Default complexity
            simpleEstimator({ defaultComplexity: 1 })
          ]
        });

        // Enforce maximum complexity
        const maxComplexity = 1000;
        if (complexity > maxComplexity) {
          throw new GraphQLError(
            `Query complexity of ${complexity} exceeds maximum of ${maxComplexity}`,
            {
              extensions: {
                code: 'BAD_USER_INPUT',
                complexity,
                maxComplexity
              }
            }
          );
        }
      }
    };
  }
};
```

### Schema with Complexity Hints

```graphql
# Add complexity cost to expensive fields
type Query {
  users(first: Int!): [User!]! # Complexity = first * 5
  search(query: String!): [SearchResult!]! # Complexity = 50
}

type User {
  id: ID! # Complexity = 1
  posts(first: Int = 10): [Post!]! # Complexity = first * 10
}
```

```typescript
// Custom complexity estimator
const customComplexity = (options) => {
  return (args, childComplexity) => {
    // Lists have multiplied complexity
    if (args.first) {
      return args.first * childComplexity;
    }

    return childComplexity;
  };
};
```

## Depth Limiting

```typescript
import depthLimit from 'graphql-depth-limit';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    depthLimit(
      7, // Maximum depth
      {},
      (depths) => {
        console.log('Query depths:', depths);
      }
    )
  ]
});

// This query would be rejected (depth = 8):
// query {
//   user {           # depth 1
//     posts {        # depth 2
//       author {     # depth 3
//         posts {    # depth 4
//           author { # depth 5
//             posts { # depth 6
//               author { # depth 7
//                 posts { # depth 8 - REJECTED
//                   title
//                 }
//               }
//             }
//           }
//         }
//       }
//     }
//   }
// }
```

## Rate Limiting

### IP-Based Rate Limiting

```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import Redis from 'ioredis';

const redis = new Redis();

// Global rate limit
const limiter = rateLimit({
  store: new RedisStore({
    client: redis,
    prefix: 'rl:global:'
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false
});

app.use('/graphql', limiter);

// Authenticated user rate limit (higher limit)
const authLimiter = rateLimit({
  store: new RedisStore({
    client: redis,
    prefix: 'rl:auth:'
  }),
  windowMs: 15 * 60 * 1000,
  max: 1000,
  skip: (req) => !req.headers.authorization,
  keyGenerator: (req) => {
    // Use user ID from token
    const token = req.headers.authorization?.replace('Bearer ', '');
    const payload = jwt.decode(token) as JWTPayload;
    return payload?.userId || req.ip;
  }
});
```

### Resolver-Level Rate Limiting

```typescript
import { RateLimiterRedis } from 'rate-limiter-flexible';

const rateLimiter = new RateLimiterRedis({
  storeClient: redis,
  points: 10, // Number of requests
  duration: 60 // Per 60 seconds
});

const resolvers = {
  Mutation: {
    async sendEmail(parent, { to, subject, body }, context: Context) {
      requireAuth(context);

      // Rate limit per user
      try {
        await rateLimiter.consume(context.userId!);
      } catch (error) {
        throw new GraphQLError('Rate limit exceeded. Please try again later.', {
          extensions: {
            code: 'TOO_MANY_REQUESTS',
            retryAfter: error.msBeforeNext / 1000
          }
        });
      }

      // Send email
      await emailService.send({ to, subject, body });
      return true;
    }
  }
};
```

### Query Cost-Based Rate Limiting

```typescript
// Track query costs per user
const costLimiter = new RateLimiterRedis({
  storeClient: redis,
  keyPrefix: 'cost:',
  points: 10000, // Total cost points
  duration: 60 * 60 // Per hour
});

const costPlugin = {
  async requestDidStart() {
    return {
      async didResolveOperation({ request, document, schema, context }) {
        if (!context.userId) return;

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

        try {
          await costLimiter.consume(context.userId, complexity);
        } catch (error) {
          throw new GraphQLError('Query cost limit exceeded', {
            extensions: {
              code: 'TOO_MANY_REQUESTS',
              cost: complexity,
              retryAfter: error.msBeforeNext / 1000
            }
          });
        }
      }
    };
  }
};
```

## Input Validation

### Schema-Level Validation

```graphql
# Use custom scalars for validation
scalar EmailAddress
scalar URL
scalar PhoneNumber

input CreateUserInput {
  email: EmailAddress!
  website: URL
  phone: PhoneNumber
}
```

```typescript
// Custom scalar with validation
import { GraphQLScalarType, GraphQLError } from 'graphql';

const EmailAddressScalar = new GraphQLScalarType({
  name: 'EmailAddress',
  description: 'Valid email address',

  parseValue(value: string) {
    if (!isValidEmail(value)) {
      throw new GraphQLError('Invalid email address', {
        extensions: { code: 'BAD_USER_INPUT' }
      });
    }
    return value.toLowerCase();
  },

  serialize(value: string) {
    return value;
  }
});
```

### Resolver-Level Validation

```typescript
import { z } from 'zod';

// Define validation schema
const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1).max(10000),
  tags: z.array(z.string()).max(10).optional(),
  publishedAt: z.date().optional()
});

const resolvers = {
  Mutation: {
    async createPost(parent, { input }, context: Context) {
      requireAuth(context);

      // Validate input
      try {
        createPostSchema.parse(input);
      } catch (error) {
        throw new GraphQLError('Validation failed', {
          extensions: {
            code: 'BAD_USER_INPUT',
            validationErrors: error.errors
          }
        });
      }

      return context.db.posts.create({
        data: {
          ...input,
          authorId: context.userId!
        }
      });
    }
  }
};
```

## Preventing Injection Attacks

### Parameterized Queries

```typescript
// UNSAFE - vulnerable to SQL injection
const resolvers = {
  Query: {
    async user(parent, { email }) {
      // DON'T DO THIS
      return db.$queryRaw`SELECT * FROM users WHERE email = '${email}'`;
    }
  }
};

// SAFE - use parameterized queries
const resolvers = {
  Query: {
    async user(parent, { email }) {
      return db.users.findUnique({
        where: { email } // Prisma handles parameterization
      });
    }
  }
};
```

### Sanitize User Input

```typescript
import DOMPurify from 'isomorphic-dompurify';

const resolvers = {
  Mutation: {
    async createPost(parent, { input }, context: Context) {
      // Sanitize HTML content
      const sanitized = {
        ...input,
        content: DOMPurify.sanitize(input.content, {
          ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'a'],
          ALLOWED_ATTR: ['href']
        })
      };

      return context.db.posts.create({ data: sanitized });
    }
  }
};
```

## Production Security Checklist

```typescript
const server = new ApolloServer({
  typeDefs,
  resolvers,

  // ✅ Disable introspection in production
  introspection: process.env.NODE_ENV !== 'production',

  // ✅ Enable CSRF protection
  csrfPrevention: true,

  // ✅ Limit query depth
  validationRules: [depthLimit(7)],

  // ✅ Add security plugins
  plugins: [
    complexityPlugin,
    costPlugin,
    auditLogPlugin
  ],

  // ✅ Format errors (hide internals)
  formatError: (error) => {
    if (error.extensions?.code === 'INTERNAL_SERVER_ERROR') {
      console.error('Internal error:', error);
      return new GraphQLError('An internal error occurred');
    }
    return error;
  }
});

// ✅ HTTPS only in production
if (process.env.NODE_ENV === 'production') {
  app.use((req, res, next) => {
    if (req.header('x-forwarded-proto') !== 'https') {
      res.redirect(`https://${req.header('host')}${req.url}`);
    } else {
      next();
    }
  });
}

// ✅ Security headers
import helmet from 'helmet';
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"]
    }
  }
}));

// ✅ CORS configuration
import cors from 'cors';
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true
}));
```
