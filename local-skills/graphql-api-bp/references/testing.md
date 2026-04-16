# Testing Strategies

Comprehensive testing approaches for GraphQL APIs.

## Unit Testing Resolvers

### Basic Resolver Tests

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('User Resolvers', () => {
  let mockContext: Context;

  beforeEach(() => {
    mockContext = {
      userId: '123',
      user: { id: '123', email: 'test@example.com', roles: ['USER'] },
      db: {
        users: {
          findUnique: vi.fn(),
          findMany: vi.fn(),
          create: vi.fn(),
          update: vi.fn(),
          delete: vi.fn()
        }
      },
      dataSources: {
        userLoader: {
          load: vi.fn()
        }
      }
    };
  });

  describe('Query.me', () => {
    it('should return current user', async () => {
      const mockUser = { id: '123', name: 'Test User', email: 'test@example.com' };
      mockContext.dataSources.userLoader.load.mockResolvedValue(mockUser);

      const result = await resolvers.Query.me(null, {}, mockContext);

      expect(result).toEqual(mockUser);
      expect(mockContext.dataSources.userLoader.load).toHaveBeenCalledWith('123');
    });

    it('should throw error when not authenticated', async () => {
      mockContext.userId = undefined;

      await expect(
        resolvers.Query.me(null, {}, mockContext)
      ).rejects.toThrow('Authentication required');
    });
  });

  describe('Mutation.createPost', () => {
    it('should create post with valid input', async () => {
      const input = { title: 'Test Post', content: 'Content' };
      const mockPost = { id: '1', ...input, authorId: '123' };

      mockContext.db.posts.create.mockResolvedValue(mockPost);

      const result = await resolvers.Mutation.createPost(
        null,
        { input },
        mockContext
      );

      expect(result.post).toEqual(mockPost);
      expect(mockContext.db.posts.create).toHaveBeenCalledWith({
        data: { ...input, authorId: '123' }
      });
    });

    it('should validate input', async () => {
      const input = { title: '', content: 'Content' };

      await expect(
        resolvers.Mutation.createPost(null, { input }, mockContext)
      ).rejects.toThrow('Title is required');
    });

    it('should require authentication', async () => {
      mockContext.userId = undefined;

      await expect(
        resolvers.Mutation.createPost(
          null,
          { input: { title: 'Test', content: 'Content' } },
          mockContext
        )
      ).rejects.toThrow('Authentication required');
    });
  });

  describe('User.posts', () => {
    it('should load user posts', async () => {
      const user = { id: '123' };
      const mockPosts = [
        { id: '1', title: 'Post 1' },
        { id: '2', title: 'Post 2' }
      ];

      mockContext.db.posts.findMany.mockResolvedValue(mockPosts);

      const result = await resolvers.User.posts(user, {}, mockContext);

      expect(result).toEqual(mockPosts);
      expect(mockContext.db.posts.findMany).toHaveBeenCalledWith({
        where: { authorId: '123' }
      });
    });
  });
});
```

### Testing with DataLoader

```typescript
import DataLoader from 'dataloader';

describe('DataLoader Integration', () => {
  it('should batch user requests', async () => {
    const batchLoadFn = vi.fn(async (ids) => {
      return ids.map(id => ({ id, name: `User ${id}` }));
    });

    const userLoader = new DataLoader(batchLoadFn);

    // Load multiple users
    const [user1, user2, user3] = await Promise.all([
      userLoader.load('1'),
      userLoader.load('2'),
      userLoader.load('3')
    ]);

    // Should batch into single call
    expect(batchLoadFn).toHaveBeenCalledTimes(1);
    expect(batchLoadFn).toHaveBeenCalledWith(['1', '2', '3']);
    expect(user1).toEqual({ id: '1', name: 'User 1' });
  });

  it('should cache loaded values', async () => {
    const batchLoadFn = vi.fn(async (ids) => {
      return ids.map(id => ({ id, name: `User ${id}` }));
    });

    const userLoader = new DataLoader(batchLoadFn);

    // Load same user twice
    await userLoader.load('1');
    await userLoader.load('1');

    // Should only call batch function once
    expect(batchLoadFn).toHaveBeenCalledTimes(1);
  });
});
```

## Integration Testing

### Testing with Apollo Server Test Client

```typescript
import { ApolloServer } from '@apollo/server';
import { describe, it, expect, beforeEach } from 'vitest';

describe('GraphQL API Integration', () => {
  let server: ApolloServer;

  beforeEach(() => {
    server = new ApolloServer({
      typeDefs,
      resolvers
    });
  });

  it('should query users', async () => {
    const response = await server.executeOperation({
      query: `
        query GetUsers {
          users {
            id
            name
            email
          }
        }
      `
    });

    expect(response.body.kind).toBe('single');
    if (response.body.kind === 'single') {
      expect(response.body.singleResult.errors).toBeUndefined();
      expect(response.body.singleResult.data?.users).toBeInstanceOf(Array);
    }
  });

  it('should create post with mutation', async () => {
    const response = await server.executeOperation(
      {
        query: `
          mutation CreatePost($input: CreatePostInput!) {
            createPost(input: $input) {
              post {
                id
                title
                content
              }
            }
          }
        `,
        variables: {
          input: {
            title: 'Test Post',
            content: 'Test content'
          }
        }
      },
      {
        contextValue: {
          userId: '123',
          user: { id: '123', roles: ['USER'] }
        }
      }
    );

    expect(response.body.kind).toBe('single');
    if (response.body.kind === 'single') {
      expect(response.body.singleResult.errors).toBeUndefined();
      expect(response.body.singleResult.data?.createPost.post).toMatchObject({
        title: 'Test Post',
        content: 'Test content'
      });
    }
  });

  it('should return error for unauthenticated request', async () => {
    const response = await server.executeOperation({
      query: `
        query Me {
          me {
            id
            email
          }
        }
      `
    });

    expect(response.body.kind).toBe('single');
    if (response.body.kind === 'single') {
      expect(response.body.singleResult.errors).toBeDefined();
      expect(response.body.singleResult.errors?.[0].extensions?.code).toBe('UNAUTHENTICATED');
    }
  });
});
```

### E2E Testing with Supertest

```typescript
import request from 'supertest';
import { app } from '../src/server';

describe('GraphQL API E2E', () => {
  let authToken: string;

  beforeAll(async () => {
    // Create test user and get auth token
    const response = await request(app)
      .post('/graphql')
      .send({
        query: `
          mutation Login($email: String!, $password: String!) {
            login(email: $email, password: $password) {
              token
              user { id email }
            }
          }
        `,
        variables: {
          email: 'test@example.com',
          password: 'password123'
        }
      });

    authToken = response.body.data.login.token;
  });

  it('should fetch current user', async () => {
    const response = await request(app)
      .post('/graphql')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        query: `
          query Me {
            me {
              id
              email
              name
            }
          }
        `
      });

    expect(response.status).toBe(200);
    expect(response.body.data.me).toMatchObject({
      email: 'test@example.com'
    });
  });

  it('should create and fetch post', async () => {
    // Create post
    const createResponse = await request(app)
      .post('/graphql')
      .set('Authorization', `Bearer ${authToken}`)
      .send({
        query: `
          mutation CreatePost($input: CreatePostInput!) {
            createPost(input: $input) {
              post { id title }
            }
          }
        `,
        variables: {
          input: { title: 'E2E Test Post', content: 'Content' }
        }
      });

    const postId = createResponse.body.data.createPost.post.id;

    // Fetch post
    const fetchResponse = await request(app)
      .post('/graphql')
      .send({
        query: `
          query GetPost($id: ID!) {
            post(id: $id) {
              id
              title
              content
              author { id name }
            }
          }
        `,
        variables: { id: postId }
      });

    expect(fetchResponse.body.data.post).toMatchObject({
      id: postId,
      title: 'E2E Test Post',
      content: 'Content'
    });
  });
});
```

## Schema Testing

### Schema Validation Tests

```typescript
import { buildSchema, validate, parse } from 'graphql';

describe('Schema Validation', () => {
  it('should have valid schema', () => {
    expect(() => buildSchema(typeDefs)).not.toThrow();
  });

  it('should validate valid queries', () => {
    const schema = buildSchema(typeDefs);
    const query = parse(`
      query GetUser($id: ID!) {
        user(id: $id) {
          id
          name
        }
      }
    `);

    const errors = validate(schema, query);
    expect(errors).toHaveLength(0);
  });

  it('should reject invalid queries', () => {
    const schema = buildSchema(typeDefs);
    const query = parse(`
      query GetUser {
        user {
          invalidField
        }
      }
    `);

    const errors = validate(schema, query);
    expect(errors.length).toBeGreaterThan(0);
  });
});
```

### Type Coverage Tests

```typescript
import { printSchema } from 'graphql';

describe('Schema Coverage', () => {
  it('should have descriptions on all types', () => {
    const schema = buildSchema(typeDefs);
    const printed = printSchema(schema);

    // Check for missing descriptions
    const types = schema.getTypeMap();
    Object.entries(types).forEach(([name, type]) => {
      if (!name.startsWith('__')) {
        expect(type.description).toBeDefined();
      }
    });
  });

  it('should have consistent naming', () => {
    const schema = buildSchema(typeDefs);
    const types = schema.getTypeMap();

    Object.keys(types).forEach(name => {
      if (!name.startsWith('__')) {
        // PascalCase for types
        expect(name).toMatch(/^[A-Z][a-zA-Z0-9]*$/);
      }
    });
  });
});
```

## Performance Testing

### Load Testing with Artillery

```yaml
# artillery.yml
config:
  target: "http://localhost:4000"
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 120
      arrivalRate: 50
      name: "Sustained load"

scenarios:
  - name: "GraphQL Queries"
    flow:
      - post:
          url: "/graphql"
          json:
            query: |
              query GetPosts {
                posts(first: 10) {
                  edges {
                    node {
                      id
                      title
                      author { name }
                    }
                  }
                }
              }
```

### Query Performance Tests

```typescript
describe('Performance', () => {
  it('should resolve query within time limit', async () => {
    const start = Date.now();

    await server.executeOperation({
      query: `
        query GetPosts {
          posts(first: 100) {
            edges {
              node {
                id
                title
                author { id name }
                comments(first: 10) {
                  edges {
                    node {
                      id
                      text
                    }
                  }
                }
              }
            }
          }
        }
      `
    });

    const duration = Date.now() - start;
    expect(duration).toBeLessThan(1000); // Should complete within 1s
  });

  it('should not cause N+1 queries', async () => {
    const queryCount = { count: 0 };

    // Mock db to count queries
    const mockDb = {
      users: {
        findMany: vi.fn(async () => {
          queryCount.count++;
          return mockUsers;
        })
      },
      posts: {
        findMany: vi.fn(async () => {
          queryCount.count++;
          return mockPosts;
        })
      }
    };

    await server.executeOperation(
      {
        query: `
          query GetPosts {
            posts(first: 10) {
              edges {
                node {
                  id
                  author { name }
                }
              }
            }
          }
        `
      },
      {
        contextValue: { db: mockDb, dataSources: createLoaders(mockDb) }
      }
    );

    // Should make 2 queries (posts + batched users), not 11 (posts + 10 individual users)
    expect(queryCount.count).toBeLessThanOrEqual(2);
  });
});
```

## Snapshot Testing

```typescript
describe('Query Snapshots', () => {
  it('should match snapshot for user query', async () => {
    const response = await server.executeOperation({
      query: `
        query GetUser($id: ID!) {
          user(id: $id) {
            id
            name
            email
            posts(first: 5) {
              edges {
                node {
                  id
                  title
                }
              }
            }
          }
        }
      `,
      variables: { id: '123' }
    });

    expect(response).toMatchSnapshot();
  });
});
```

## Mocking Strategies

### Mock Resolvers

```typescript
import { addMocksToSchema } from '@graphql-tools/mock';
import { makeExecutableSchema } from '@graphql-tools/schema';

const schema = makeExecutableSchema({ typeDefs });

const mocks = {
  User: () => ({
    id: () => '123',
    name: () => 'Test User',
    email: () => 'test@example.com'
  }),
  Post: () => ({
    id: () => '456',
    title: () => 'Mock Post',
    content: () => 'Mock content'
  }),
  DateTime: () => new Date('2024-01-01')
};

const schemaWithMocks = addMocksToSchema({
  schema,
  mocks,
  preserveResolvers: false
});
```

### Mock Data Builders

```typescript
// Test data builders
class UserBuilder {
  private user: Partial<User> = {
    id: '123',
    email: 'test@example.com',
    name: 'Test User',
    createdAt: new Date()
  };

  withId(id: string) {
    this.user.id = id;
    return this;
  }

  withEmail(email: string) {
    this.user.email = email;
    return this;
  }

  withRole(role: string) {
    this.user.roles = [role];
    return this;
  }

  build(): User {
    return this.user as User;
  }
}

// Usage in tests
const admin = new UserBuilder()
  .withId('admin-1')
  .withEmail('admin@example.com')
  .withRole('ADMIN')
  .build();
```
