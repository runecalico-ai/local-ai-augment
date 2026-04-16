# Schema Design Patterns

Advanced patterns for designing robust, scalable GraphQL schemas.

## Relay Specification

### Cursor-Based Pagination

```graphql
# Node interface - global object identification
interface Node {
  id: ID!
}

# Connection pattern
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

# Implementing Node interface
type Post implements Node {
  id: ID!
  title: String!
  content: String!
}

# Query with connection
type Query {
  posts(
    first: Int
    after: String
    last: Int
    before: String
  ): PostConnection!

  # Global node lookup
  node(id: ID!): Node
}
```

### Cursor Implementation

```typescript
// Base64 encode cursor
function encodeCursor(id: string): string {
  return Buffer.from(`Post:${id}`).toString('base64');
}

function decodeCursor(cursor: string): string {
  const decoded = Buffer.from(cursor, 'base64').toString('utf-8');
  return decoded.split(':')[1];
}

// Resolver implementation
async posts(parent, { first = 10, after, last, before }, context) {
  // Forward pagination
  if (first) {
    const cursor = after ? decodeCursor(after) : undefined;
    const items = await db.posts.findMany({
      take: first + 1,
      cursor: cursor ? { id: cursor } : undefined,
      orderBy: { createdAt: 'desc' }
    });

    const hasNextPage = items.length > first;
    const nodes = items.slice(0, first);

    return {
      edges: nodes.map(node => ({
        node,
        cursor: encodeCursor(node.id)
      })),
      pageInfo: {
        hasNextPage,
        hasPreviousPage: !!after,
        startCursor: nodes[0] ? encodeCursor(nodes[0].id) : null,
        endCursor: nodes[nodes.length - 1] ? encodeCursor(nodes[nodes.length - 1].id) : null
      },
      totalCount: await db.posts.count()
    };
  }

  // Backward pagination (last/before)
  // Similar implementation in reverse
}
```

## Interface and Union Patterns

### Interface Inheritance

```graphql
# Base interface for all content
interface Content {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  author: User!
}

# Specialized interfaces
interface Commentable {
  comments: CommentConnection!
}

interface Likeable {
  likes: Int!
  likedByMe: Boolean!
}

# Types implementing multiple interfaces
type Post implements Content & Commentable & Likeable {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  author: User!
  comments: CommentConnection!
  likes: Int!
  likedByMe: Boolean!
  title: String!
  content: String!
}

type Video implements Content & Commentable & Likeable {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  author: User!
  comments: CommentConnection!
  likes: Int!
  likedByMe: Boolean!
  url: URL!
  duration: Int!
}
```

### Union Type Patterns

```graphql
# Search results can be multiple types
union SearchResult = Post | User | Comment | Video

type Query {
  search(query: String!): [SearchResult!]!
}

# Client query with inline fragments
query Search($query: String!) {
  search(query: $query) {
    ... on Post {
      id
      title
      author { name }
    }
    ... on User {
      id
      name
      email
    }
    ... on Video {
      id
      url
      duration
    }
  }
}
```

```typescript
// Resolver for union types
const resolvers = {
  SearchResult: {
    __resolveType(obj: any) {
      if ('title' in obj && 'content' in obj) return 'Post';
      if ('email' in obj) return 'User';
      if ('text' in obj) return 'Comment';
      if ('url' in obj && 'duration' in obj) return 'Video';
      return null;
    }
  },

  Query: {
    async search(parent, { query }, context) {
      const [posts, users, videos] = await Promise.all([
        context.db.posts.search(query),
        context.db.users.search(query),
        context.db.videos.search(query)
      ]);

      return [...posts, ...users, ...videos];
    }
  }
};
```

## Input Type Patterns

### Input Validation

```graphql
# Separate input types for create vs update
input CreatePostInput {
  title: String!
  content: String!
  tags: [String!]
  publishedAt: DateTime
}

input UpdatePostInput {
  title: String
  content: String
  tags: [String!]
  publishedAt: DateTime
}

# Nested input types
input CreateCommentInput {
  postId: ID!
  text: String!
  replyTo: ID  # Optional parent comment
}

# Input with constraints
input PaginationInput {
  first: Int! @constraint(max: 100, min: 1)
  after: String
}
```

### Mutation Patterns

```graphql
# Input/Output pattern
type Mutation {
  createPost(input: CreatePostInput!): CreatePostPayload!
  updatePost(id: ID!, input: UpdatePostInput!): UpdatePostPayload!
  deletePost(id: ID!): DeletePostPayload!
}

# Payload types with errors
type CreatePostPayload {
  post: Post
  errors: [MutationError!]!
  success: Boolean!
}

type MutationError {
  message: String!
  field: String
  code: ErrorCode!
}

enum ErrorCode {
  VALIDATION_ERROR
  NOT_FOUND
  UNAUTHORIZED
  CONFLICT
}
```

## Custom Scalars

```typescript
import { GraphQLScalarType, Kind } from 'graphql';

// DateTime scalar
const DateTimeScalar = new GraphQLScalarType({
  name: 'DateTime',
  description: 'ISO 8601 date-time string',

  serialize(value: Date | string) {
    if (value instanceof Date) {
      return value.toISOString();
    }
    return value;
  },

  parseValue(value: string) {
    return new Date(value);
  },

  parseLiteral(ast) {
    if (ast.kind === Kind.STRING) {
      return new Date(ast.value);
    }
    return null;
  }
});

// Email scalar with validation
const EmailScalar = new GraphQLScalarType({
  name: 'EmailAddress',
  description: 'Valid email address',

  serialize(value: string) {
    if (!isValidEmail(value)) {
      throw new Error('Invalid email address');
    }
    return value;
  },

  parseValue(value: string) {
    if (!isValidEmail(value)) {
      throw new GraphQLError('Invalid email address', {
        extensions: { code: 'BAD_USER_INPUT' }
      });
    }
    return value;
  },

  parseLiteral(ast) {
    if (ast.kind === Kind.STRING && isValidEmail(ast.value)) {
      return ast.value;
    }
    throw new GraphQLError('Invalid email address');
  }
});

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
```

## Versioning Strategies

### Field Deprecation

```graphql
type User {
  id: ID!
  name: String!

  # Deprecated field
  username: String @deprecated(reason: "Use 'name' instead")

  # New field
  displayName: String!
}
```

### Additive Changes (Preferred)

```graphql
# V1 - Original
type Post {
  id: ID!
  title: String!
  content: String!
}

# V2 - Add new fields without breaking old queries
type Post {
  id: ID!
  title: String!
  content: String!
  # New fields
  summary: String
  tags: [String!]!
  metadata: PostMetadata
}

type PostMetadata {
  readTime: Int
  wordCount: Int
}
```

### Schema Stitching for Major Versions

```typescript
import { stitchSchemas } from '@graphql-tools/stitch';

// Separate schemas for different versions
const schemaV1 = buildSchema(/* v1 schema */);
const schemaV2 = buildSchema(/* v2 schema */);

// Stitch with namespace
const schema = stitchSchemas({
  subschemas: [
    { schema: schemaV1, batch: true },
    { schema: schemaV2, batch: true }
  ]
});
```

## Error Handling Patterns

### Field-Level Errors

```graphql
# Return errors as part of the data model
type PostResult {
  post: Post
  error: Error
}

type Error {
  message: String!
  code: ErrorCode!
  path: [String!]
}

type Mutation {
  createPost(input: CreatePostInput!): PostResult!
}
```

### Partial Success Pattern

```graphql
type BatchCreatePostsPayload {
  successful: [Post!]!
  failed: [FailedPost!]!
}

type FailedPost {
  input: CreatePostInput!
  error: Error!
}
```

## Federation Patterns

```graphql
# User service
type User @key(fields: "id") {
  id: ID!
  email: String!
  name: String!
}

# Post service - extends User
extend type User @key(fields: "id") {
  id: ID! @external
  posts: [Post!]!
}

type Post @key(fields: "id") {
  id: ID!
  title: String!
  author: User!
}
```

```typescript
// User service resolver
const resolvers = {
  User: {
    __resolveReference(user: { id: string }) {
      return getUserById(user.id);
    }
  }
};

// Post service resolver
const resolvers = {
  User: {
    posts(user: { id: string }) {
      return getPostsByUserId(user.id);
    }
  },

  Post: {
    __resolveReference(post: { id: string }) {
      return getPostById(post.id);
    },

    author(post: Post) {
      return { __typename: 'User', id: post.authorId };
    }
  }
};
```
