# Groovy DSL Patterns for Jenkins

Idiomatic Groovy patterns, language features, and best practices for Jenkins pipeline development.

## Table of Contents

- [String Operations](#string-operations)
- [Collections](#collections)
- [Closures](#closures)
- [Control Flow](#control-flow)
- [Object-Oriented Features](#object-oriented-features)
- [Functional Programming](#functional-programming)
- [Safe Navigation](#safe-navigation)
- [Regular Expressions](#regular-expressions)
- [Metaprogramming](#metaprogramming)

## String Operations

### String Interpolation (GString)

```groovy
def version = "1.2.3"
def environment = "production"

// Single quotes - no interpolation (String literal)
def literal = 'Version: ${version}'
echo literal  // Output: Version: ${version}

// Double quotes - interpolation (GString)
def interpolated = "Version: ${version}"
echo interpolated  // Output: Version: 1.2.3

// Expression in interpolation
def message = "Deploying version ${version} to ${environment.toUpperCase()}"
echo message  // Output: Deploying version 1.2.3 to PRODUCTION

// Multiline strings
def yaml = """
apiVersion: v1
kind: Service
metadata:
  name: ${params.SERVICE_NAME}
  environment: ${environment}
"""

// Multiline with no interpolation
def script = '''
#!/bin/bash
echo "This ${variable} won't be interpolated"
'''
```

### String Methods

```groovy
def text = "  Hello World  "

// Trimming
echo text.trim()           // "Hello World"
echo text.stripIndent()    // Remove common indentation

// Case conversion
echo text.toLowerCase()    // "  hello world  "
echo text.toUpperCase()    // "  HELLO WORLD  "
echo text.capitalize()     // "  Hello world  "

// Checking content
if (text.contains("World")) {
    echo "Found World"
}

if (text.startsWith("Hello")) {
    echo "Starts with Hello"
}

if (text.endsWith("World")) {
    echo "Ends with World"
}

// Splitting
def parts = "a,b,c".split(',')  // ['a', 'b', 'c']
def words = "hello world".tokenize()  // ['hello', 'world']

// Joining
def joined = ['a', 'b', 'c'].join(',')  // "a,b,c"

// Replacing
def fixed = "foo bar foo".replace('foo', 'baz')  // "baz bar baz"
def regex = "foo123bar".replaceAll(/\d+/, 'XXX')  // "fooXXXbar"

// Padding
echo "42".padLeft(5, '0')   // "00042"
echo "42".padRight(5, '0')  // "42000"
```

### String Building

```groovy
// For complex string construction
def builder = new StringBuilder()
builder << "Line 1\n"
builder << "Line 2\n"
builder << "Line 3\n"
def result = builder.toString()

// Or more Groovy way
def lines = []
lines << "Line 1"
lines << "Line 2"
lines << "Line 3"
def result = lines.join('\n')
```

## Collections

### Lists

```groovy
// Creating lists
def empty = []
def numbers = [1, 2, 3, 4, 5]
def mixed = [1, 'two', 3.0, true]

// Accessing elements
echo numbers[0]        // 1
echo numbers[-1]       // 5 (last element)
echo numbers[-2]       // 4 (second to last)

// Ranges
def range = 1..10      // [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
def exclusive = 1..<10 // [1, 2, 3, 4, 5, 6, 7, 8, 9]

// Adding elements
numbers << 6           // [1, 2, 3, 4, 5, 6]
numbers.add(7)         // [1, 2, 3, 4, 5, 6, 7]
numbers += [8, 9]      // [1, 2, 3, 4, 5, 6, 7, 8, 9]

// Removing elements
numbers.remove(0)      // Removes first element
numbers -= [8, 9]      // Removes 8 and 9

// List operations
def first = numbers.first()
def last = numbers.last()
def size = numbers.size()
def reversed = numbers.reverse()
def sorted = numbers.sort()
def unique = numbers.unique()

// Sublists
def slice = numbers[1..3]      // Elements 1, 2, 3
def step = numbers[0..6:2]     // Every 2nd element from 0 to 6
```

### List Iteration and Transformation

```groovy
def numbers = [1, 2, 3, 4, 5]

// each - iterate (returns original list)
numbers.each { num ->
    echo "Number: ${num}"
}

// eachWithIndex
numbers.eachWithIndex { num, idx ->
    echo "Index ${idx}: ${num}"
}

// collect - transform (map)
def doubled = numbers.collect { it * 2 }  // [2, 4, 6, 8, 10]

// findAll - filter
def evens = numbers.findAll { it % 2 == 0 }  // [2, 4]

// find - first match
def firstEven = numbers.find { it % 2 == 0 }  // 2

// any - check if any element matches
def hasEven = numbers.any { it % 2 == 0 }  // true

// every - check if all elements match
def allPositive = numbers.every { it > 0 }  // true

// sum
def total = numbers.sum()  // 15

// max/min
def maximum = numbers.max()  // 5
def minimum = numbers.min()  // 1

// flatten - flatten nested lists
def nested = [[1, 2], [3, 4], [5]]
def flat = nested.flatten()  // [1, 2, 3, 4, 5]

// groupBy - group by criteria
def grouped = numbers.groupBy { it % 2 == 0 ? 'even' : 'odd' }
// [odd: [1, 3, 5], even: [2, 4]]
```

### Maps

```groovy
// Creating maps
def empty = [:]
def person = [
    name: 'John',
    age: 30,
    city: 'New York'
]

// Accessing values
echo person.name       // 'John'
echo person['age']     // 30

// Adding/updating
person.country = 'USA'
person['state'] = 'NY'

// Checking existence
if (person.containsKey('name')) {
    echo "Has name"
}

if ('age' in person) {
    echo "Has age"
}

// Removing
person.remove('state')

// Map operations
def keys = person.keySet()
def values = person.values()
def size = person.size()

// Iteration
person.each { key, value ->
    echo "${key}: ${value}"
}

// Transform
def upperKeys = person.collectEntries { k, v ->
    [k.toUpperCase(), v]
}

// Filter
def filtered = person.findAll { k, v ->
    v instanceof String
}

// Merge maps
def defaults = [timeout: 60, retries: 3]
def config = [timeout: 120]
def merged = defaults + config  // config overrides defaults
// Result: [timeout: 120, retries: 3]
```

### Sets

```groovy
def set = [1, 2, 3, 2, 1] as Set  // [1, 2, 3]

// Add elements
set << 4
set.add(5)

// Check membership
if (3 in set) {
    echo "Contains 3"
}

// Set operations
def a = [1, 2, 3] as Set
def b = [2, 3, 4] as Set

def union = a + b         // [1, 2, 3, 4]
def intersection = a.intersect(b)  // [2, 3]
def difference = a - b    // [1]
```

## Closures

### Basic Closures

```groovy
// Simple closure
def greet = { name ->
    echo "Hello, ${name}!"
}
greet('World')  // Output: Hello, World!

// Multiple parameters
def add = { a, b ->
    return a + b
}
def result = add(5, 3)  // 8

// Implicit parameter 'it'
def square = { it * it }
echo square(5)  // 25

// No parameters
def sayHello = {
    echo "Hello!"
}
sayHello()

// Last expression is returned
def multiply = { a, b ->
    a * b  // Implicit return
}
```

### Closure Scope

```groovy
def multiplier = 2

def multiplyBy = { num ->
    num * multiplier  // Captures 'multiplier' from outer scope
}

echo multiplyBy(5)  // 10

// Closure can modify outer variables
def counter = 0
def increment = {
    counter++
}
increment()
increment()
echo counter  // 2
```

### Closures as Parameters

```groovy
def repeat(int times, Closure action) {
    for (int i = 0; i < times; i++) {
        action(i)
    }
}

// Usage
repeat(3) { num ->
    echo "Iteration ${num}"
}

// Common in Jenkins DSL
def withRetry(int maxRetries, Closure action) {
    for (int i = 0; i < maxRetries; i++) {
        try {
            action.call()
            return  // Success
        } catch (Exception e) {
            if (i == maxRetries - 1) {
                throw e  // Last attempt failed
            }
            echo "Retry ${i + 1}/${maxRetries}"
            sleep(time: i + 1, unit: 'SECONDS')
        }
    }
}

// Usage
withRetry(3) {
    sh 'flaky-command.sh'
}
```

### Closure Delegation

```groovy
class ConfigBuilder {
    def config = [:]

    def database(Closure cl) {
        def dbConfig = [:]
        cl.delegate = dbConfig
        cl.resolveStrategy = Closure.DELEGATE_FIRST
        cl()
        config.database = dbConfig
    }
}

// Usage (similar to Jenkins DSL)
def builder = new ConfigBuilder()
builder.database {
    host = 'localhost'
    port = 5432
    name = 'mydb'
}

echo builder.config
// [database: [host: 'localhost', port: 5432, name: 'mydb']]
```

## Control Flow

### If-Else

```groovy
def environment = params.ENVIRONMENT

if (environment == 'production') {
    echo "Deploying to production"
} else if (environment == 'staging') {
    echo "Deploying to staging"
} else {
    echo "Deploying to development"
}

// Ternary operator
def timeout = environment == 'production' ? 3600 : 600

// Elvis operator (null coalescing)
def branch = params.BRANCH ?: 'main'
def host = config?.database?.host ?: 'localhost'
```

### Switch

```groovy
def environment = params.ENVIRONMENT

switch (environment) {
    case 'production':
        deployToProd()
        break
    case 'staging':
        deployToStaging()
        break
    case ~/dev-.*/:  // Regex pattern
        deployToDev()
        break
    case ['qa', 'test']:  // List of values
        deployToTest()
        break
    default:
        error "Unknown environment: ${environment}"
}

// Switch with return value
def timeout = switch (environment) {
    case 'production' -> 3600
    case 'staging' -> 1800
    default -> 600
}
```

### Loops

```groovy
// Classic for loop
for (int i = 0; i < 5; i++) {
    echo "Iteration ${i}"
}

// For-each (works with any Iterable)
def items = ['a', 'b', 'c']
for (item in items) {
    echo "Item: ${item}"
}

// While loop
def count = 0
while (count < 5) {
    echo "Count: ${count}"
    count++
}

// Groovy each (preferred in Jenkins)
items.each { item ->
    echo "Item: ${item}"
}

// Range iteration
(1..5).each { num ->
    echo "Number: ${num}"
}

// Times (simple repetition)
5.times { i ->
    echo "Iteration ${i}"
}

// Step
(0..10).step(2) { num ->
    echo "Even: ${num}"
}
```

### Exception Handling

```groovy
try {
    sh 'risky-command'
} catch (Exception e) {
    echo "Error occurred: ${e.message}"
    echo "Stack trace: ${e.printStackTrace()}"
    currentBuild.result = 'FAILURE'
} finally {
    echo "Cleanup"
    cleanWs()
}

// Multiple catch blocks
try {
    sh 'command'
} catch (FileNotFoundException e) {
    echo "File not found: ${e.message}"
} catch (IOException e) {
    echo "I/O error: ${e.message}"
} catch (Exception e) {
    echo "Unknown error: ${e.message}"
    throw e
}

// Try with resources (Groovy 3+)
try (def file = new File('/tmp/data.txt').newReader()) {
    def content = file.text
    echo content
}
```

## Object-Oriented Features

### Classes (in Shared Libraries)

```groovy
// In src/org/company/DeploymentConfig.groovy
package org.company

class DeploymentConfig implements Serializable {
    String environment
    String version
    int replicas = 3
    Map<String, String> labels = [:]

    // Constructor
    DeploymentConfig(String env, String ver) {
        this.environment = env
        this.version = ver
    }

    // Method
    def validate() {
        if (!environment) {
            throw new IllegalArgumentException("Environment required")
        }
        if (!version) {
            throw new IllegalArgumentException("Version required")
        }
        return true
    }

    // Getter/Setter (automatic with Groovy)
    def getFullVersion() {
        return "${environment}-${version}"
    }
}

// Usage in pipeline
@Library('my-lib') _
import org.company.DeploymentConfig

def config = new DeploymentConfig('production', '1.2.3')
config.replicas = 5
config.labels = [app: 'myapp', tier: 'backend']

if (config.validate()) {
    echo "Deploying ${config.fullVersion} with ${config.replicas} replicas"
}
```

### Traits (Mixins)

```groovy
// In shared library
trait Loggable {
    def log(String message) {
        echo "[${new Date()}] ${message}"
    }
}

trait Retryable {
    def retry(int times, Closure action) {
        for (int i = 0; i < times; i++) {
            try {
                return action()
            } catch (Exception e) {
                if (i == times - 1) throw e
                log("Retry ${i + 1}/${times}")
            }
        }
    }
}

class Deployer implements Loggable, Retryable, Serializable {
    def deploy(String app) {
        log("Deploying ${app}")
        retry(3) {
            // Deployment logic
            return true
        }
    }
}
```

## Functional Programming

### Map/Filter/Reduce Patterns

```groovy
def numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Map (collect)
def squared = numbers.collect { it ** 2 }
// [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

// Filter (findAll)
def evens = numbers.findAll { it % 2 == 0 }
// [2, 4, 6, 8, 10]

// Reduce (inject)
def sum = numbers.inject(0) { acc, num -> acc + num }
// 55

def product = numbers.inject(1) { acc, num -> acc * num }
// 3628800

// Chaining operations
def result = numbers
    .findAll { it % 2 == 0 }      // Get evens: [2, 4, 6, 8, 10]
    .collect { it ** 2 }           // Square: [4, 16, 36, 64, 100]
    .inject(0) { acc, n -> acc + n }  // Sum: 220

// Complex transformation
def environments = ['dev', 'staging', 'production']
def configs = environments.collect { env ->
    [
        name: env,
        url: "https://${env}.example.com",
        timeout: env == 'production' ? 3600 : 600
    ]
}
```

### Partial Application and Currying

```groovy
// Currying - fixing some arguments
def multiply = { a, b -> a * b }
def double = multiply.curry(2)  // Fix first argument to 2

echo double(5)  // 10
echo double(7)  // 14

// Right curry
def divide = { a, b -> a / b }
def divideBy2 = divide.rcurry(2)  // Fix second argument to 2

echo divideBy2(10)  // 5
echo divideBy2(20)  // 10
```

### Lazy Evaluation

```groovy
// Lazy lists (compute on demand)
def fibonacci = [0, 1]
(2..10).each { i ->
    fibonacci << fibonacci[i-1] + fibonacci[i-2]
}
// Only computed when accessed
```

## Safe Navigation

### Null-Safe Operations

```groovy
// Traditional null checking
if (config != null && config.database != null && config.database.host != null) {
    echo config.database.host
}

// Safe navigation operator ?.
echo config?.database?.host  // Returns null if any part is null

// With Elvis for default
def host = config?.database?.host ?: 'localhost'

// Method calls
def result = object?.someMethod()?.anotherMethod()

// Collections
def firstElement = list?.get(0)
def size = list?.size() ?: 0
```

### Safe Indexing

```groovy
def list = ['a', 'b', 'c']

// Traditional
def item = list.size() > 5 ? list[5] : null

// Safe
def item = list?.getAt(5)  // Returns null if out of bounds

// Map access
def config = [timeout: 60]
def retries = config?.retries ?: 3  // Use default if not set
```

## Regular Expressions

### Pattern Matching

```groovy
def text = "Version 1.2.3"

// Match operator (=~) creates Matcher
def matcher = text =~ /(\d+)\.(\d+)\.(\d+)/
if (matcher) {
    def major = matcher[0][1]  // '1'
    def minor = matcher[0][2]  // '2'
    def patch = matcher[0][3]  // '3'
    echo "Version: ${major}.${minor}.${patch}"
}

// Find operator (==~) boolean match
if (text ==~ /Version \d+\.\d+\.\d+/) {
    echo "Valid version format"
}

// Extract all matches
def tags = "v1.2.3, v2.0.0, v1.5.7"
def versions = (tags =~ /v(\d+\.\d+\.\d+)/).collect { it[1] }
// ['1.2.3', '2.0.0', '1.5.7']
```

### String Replacement with Regex

```groovy
def text = "foo123bar456baz"

// Replace all digits
def cleaned = text.replaceAll(/\d+/, 'X')
// "fooXbarXbaz"

// Replace with capture groups
def version = "v1.2.3"
def normalized = version.replaceAll(/v(\d+\.\d+)\.(\d+)/, '$1')
// "1.2"

// Replace first match
def replaced = text.replaceFirst(/\d+/, 'NUM')
// "fooNUMbar456baz"
```

### Pattern Validation

```groovy
def validateBranchName(String branch) {
    // Only allow alphanumeric, dash, underscore, slash
    if (!(branch ==~ /^[a-zA-Z0-9_\-\/]+$/)) {
        error "Invalid branch name: ${branch}"
    }
}

def validateEmail(String email) {
    if (!(email ==~ /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$/)) {
        error "Invalid email: ${email}"
    }
}

def validateVersion(String version) {
    if (!(version ==~ /^\d+\.\d+\.\d+$/)) {
        error "Invalid version: ${version}. Expected format: X.Y.Z"
    }
}
```

## Metaprogramming

### Dynamic Method Invocation

```groovy
def methodName = 'toLowerCase'
def text = "HELLO"
def result = text."${methodName}"()  // Calls text.toLowerCase()
echo result  // "hello"

// Dynamic property access
def propertyName = 'name'
def person = [name: 'John', age: 30]
def value = person."${propertyName}"  // person.name
```

### Adding Methods at Runtime

```groovy
// In shared library or @NonCPS
@NonCPS
def enhanceString() {
    String.metaClass.shout = {
        delegate.toUpperCase() + '!!!'
    }
}

enhanceString()
echo "hello".shout()  // "HELLO!!!"
```

### Method Missing (DSL Creation)

```groovy
// In shared library
class DynamicBuilder {
    def config = [:]

    def methodMissing(String name, args) {
        if (args.length == 1) {
            config[name] = args[0]
        } else {
            throw new MissingMethodException(name, this.class, args)
        }
    }

    def propertyMissing(String name, value) {
        config[name] = value
    }
}

// Usage
def builder = new DynamicBuilder()
builder.host('localhost')
builder.port(8080)
builder.database = 'mydb'

echo builder.config
// [host: 'localhost', port: 8080, database: 'mydb']
```

## Advanced Patterns

### Builder Pattern

```groovy
class DeploymentBuilder {
    private String app
    private String env
    private String version
    private int replicas = 1

    DeploymentBuilder forApp(String app) {
        this.app = app
        return this
    }

    DeploymentBuilder toEnvironment(String env) {
        this.env = env
        return this
    }

    DeploymentBuilder withVersion(String version) {
        this.version = version
        return this
    }

    DeploymentBuilder withReplicas(int replicas) {
        this.replicas = replicas
        return this
    }

    Map build() {
        return [
            app: app,
            environment: env,
            version: version,
            replicas: replicas
        ]
    }
}

// Usage
def deployment = new DeploymentBuilder()
    .forApp('myapp')
    .toEnvironment('production')
    .withVersion('1.2.3')
    .withReplicas(5)
    .build()
```

### Pipeline-Specific Patterns

```groovy
// Retry with exponential backoff
def retryWithBackoff(int maxAttempts, Closure action) {
    for (int attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return action()
        } catch (Exception e) {
            if (attempt == maxAttempts) {
                throw e
            }
            def waitTime = Math.pow(2, attempt - 1) as int
            echo "Attempt ${attempt} failed, waiting ${waitTime}s before retry..."
            sleep(time: waitTime, unit: 'SECONDS')
        }
    }
}

// Parallel map operation
def parallelMap(List items, Closure transform) {
    def tasks = items.collectEntries { item ->
        ["Process ${item}": {
            transform(item)
        }]
    }
    return parallel(tasks)
}

// Usage
def results = parallelMap(['app1', 'app2', 'app3']) { app ->
    sh "test-${app}.sh"
}
```

## Best Practices Summary

1. **Use GStrings for interpolation** - Double quotes when you need variable expansion
2. **Prefer Groovy collections** - `.each`, `.collect`, `.findAll` over iterators
3. **Leverage safe navigation** - `?.` to avoid null checks
4. **Use closures effectively** - Keep them simple and CPS-safe
5. **Pattern matching for validation** - Regex for input validation
6. **Builder pattern for complex configs** - Fluent interfaces for readability
7. **Keep it serializable** - Remember CPS constraints in Jenkins
8. **@NonCPS for pure functions** - Heavy computation outside CPS
9. **Elvis for defaults** - `?:` operator for null coalescing
10. **Immutability when possible** - Avoid shared mutable state
