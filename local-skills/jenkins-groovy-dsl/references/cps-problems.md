# CPS (Continuation Passing Style) Problems and Solutions

Comprehensive guide to understanding and resolving Jenkins CPS serialization issues.

## Table of Contents

- [Understanding CPS](#understanding-cps)
- [How CPS Works in Jenkins](#how-cps-works-in-jenkins)
- [Common CPS Errors](#common-cps-errors)
- [Serialization Requirements](#serialization-requirements)
- [Problem Patterns and Solutions](#problem-patterns-and-solutions)
- [The @NonCPS Annotation](#the-noncps-annotation)
- [Advanced Troubleshooting](#advanced-troubleshooting)

## Understanding CPS

### What is Continuation Passing Style?

CPS is a programming style where control flow is passed explicitly through continuation functions. Jenkins uses CPS to make pipelines **resumable** - they can pause, serialize to disk, and resume after:

- Jenkins restart
- Node disconnection
- Waiting for input/approval
- Resource availability

### The Price of Resumability

To serialize pipeline state, Jenkins must:

1. **Transform Groovy code** - Convert to CPS style automatically
2. **Serialize all variables** - Save to disk at suspension points
3. **Track execution state** - Remember where to resume

This creates unique constraints not present in normal Groovy programs.

## How CPS Works in Jenkins

### CPS Transformation

```groovy
// Your code (what you write)
def result = calculateValue()
echo "Result: ${result}"
deployApp(result)

// What Jenkins actually runs (simplified)
calculateValue().then { result ->
    echo("Result: ${result}").then {
        deployApp(result).then {
            // continue
        }
    }
}
```

Every step becomes a continuation. Between steps, Jenkins can serialize the state.

### Suspension Points

Pipeline can suspend at:

- Any Pipeline step (`sh`, `echo`, `sleep`, etc.)
- `input` steps waiting for user approval
- Resource allocation (`lock`, node acquisition)
- Certain plugin operations

**Critical**: All variables in scope must be serializable at suspension points.

## Common CPS Errors

### NotSerializableException

**Error message:**
```
java.io.NotSerializableException: java.io.FileInputStream
    at org.jboss.marshalling.river.RiverMarshaller.doWriteObject
    ...
```

**Cause:** Non-serializable object in scope at suspension point.

**Example:**
```groovy
// ❌ WRONG
def file = new File('/tmp/data.txt')
def content = file.text
stage('Process') {
    // Suspension point - tries to serialize 'file'
    sh 'process data'
}
```

**Solution:**
```groovy
// ✅ CORRECT - don't store File object
def content = readFile('/tmp/data.txt')  // Returns String
stage('Process') {
    sh 'process data'
}

// OR use @NonCPS if no pipeline steps
@NonCPS
def readDataFile() {
    def file = new File('/tmp/data.txt')
    try {
        return file.text
    } finally {
        // No need to close file, handled by try-with-resources in real code
    }
}
```

### CpsCallableInvocation

**Error message:**
```
org.jenkinsci.plugins.workflow.cps.CpsCallableInvocation
Expected a symbol but got CpsCallableInvocation
```

**Cause:** Calling non-CPS code from CPS context incorrectly, or complex iteration.

**Example:**
```groovy
// ❌ WRONG
def items = [1, 2, 3]
def iterator = items.iterator()
while (iterator.hasNext()) {
    echo iterator.next()
}
```

**Solution:**
```groovy
// ✅ CORRECT
def items = [1, 2, 3]
items.each { item ->
    echo item.toString()
}

// OR classic for loop
for (int i = 0; i < items.size(); i++) {
    echo items[i].toString()
}
```

### MissingPropertyException

**Error message:**
```
groovy.lang.MissingPropertyException: No such property: result
```

**Cause:** Variable scope issues in closures or CPS transformation.

**Example:**
```groovy
// ❌ WRONG - scope issue
def result
parallel(
    'task1': {
        result = sh(script: 'echo task1', returnStdout: true)
    },
    'task2': {
        result = sh(script: 'echo task2', returnStdout: true)
    }
)
echo result  // Which task's result?
```

**Solution:**
```groovy
// ✅ CORRECT - proper scoping
def results = [:]
parallel(
    'task1': {
        results['task1'] = sh(script: 'echo task1', returnStdout: true)
    },
    'task2': {
        results['task2'] = sh(script: 'echo task2', returnStdout: true)
    }
)
echo "Task1: ${results.task1}, Task2: ${results.task2}"
```

## Serialization Requirements

### Serializable Types (Safe)

These types are safe to use in pipeline variables:

**Primitives and Wrappers:**
- `String`, `Integer`, `Long`, `Short`, `Byte`
- `Boolean`, `Character`
- `Float`, `Double`
- `BigInteger`, `BigDecimal`

**Collections (if contents are serializable):**
- `ArrayList`, `LinkedList`
- `HashMap`, `TreeMap`, `LinkedHashMap`
- `HashSet`, `TreeSet`
- Arrays of serializable types

**Common Java Classes:**
- `java.util.Date`
- `java.util.UUID`
- `java.net.URL`
- `java.util.regex.Pattern`

**Jenkins Objects:**
- Most Pipeline step results (if explicitly serializable)
- Environment variables (`env.*`)
- Build parameters (`params.*`)

### Non-Serializable Types (Dangerous)

**Never store these in pipeline variables:**

**I/O Classes:**
- `java.io.File`
- `java.io.FileInputStream/FileOutputStream`
- `java.io.BufferedReader/BufferedWriter`
- `java.nio.file.Path` (sometimes)

**Network/Database:**
- `java.sql.Connection`
- `java.net.Socket`
- `org.apache.http.client.HttpClient`
- Database connections (JDBC, etc.)

**Concurrency:**
- `java.lang.Thread`
- `java.util.concurrent.ExecutorService`
- `java.util.concurrent.locks.Lock`

**Java 8+ Features:**
- `java.util.stream.Stream`
- Some lambda expressions
- `java.util.Optional` (context-dependent)

**Iterators:**
- `Iterator`, `ListIterator`
- Some `Iterable` implementations

## Problem Patterns and Solutions

### Pattern 1: File Operations

```groovy
// ❌ PROBLEM
def file = new File('/workspace/config.json')
def json = new JsonSlurper().parse(file)
stage('Deploy') {
    // ERROR: 'file' not serializable
    sh "deploy --config ${file.absolutePath}"
}

// ✅ SOLUTION 1: Use pipeline steps
def jsonText = readFile('config.json')
def json = new JsonSlurper().parseText(jsonText)
stage('Deploy') {
    sh "deploy --config config.json"
}

// ✅ SOLUTION 2: Use @NonCPS
@NonCPS
def parseConfigFile(String path) {
    def file = new File(path)
    return new JsonSlurper().parse(file)
}

def json = parseConfigFile('/workspace/config.json')
stage('Deploy') {
    sh "deploy --config /workspace/config.json"
}
```

### Pattern 2: Database Queries

```groovy
// ❌ PROBLEM
def sql = Sql.newInstance(jdbcUrl, user, pass)
stage('Query') {
    def results = sql.rows("SELECT * FROM users")
    // ERROR: 'sql' connection not serializable
}

// ✅ SOLUTION: Create and close in @NonCPS
@NonCPS
def queryDatabase(String jdbcUrl, String user, String pass, String query) {
    def sql = null
    try {
        sql = Sql.newInstance(jdbcUrl, user, pass)
        return sql.rows(query)
    } finally {
        sql?.close()
    }
}

stage('Query') {
    def results = queryDatabase(jdbcUrl, user, pass, "SELECT * FROM users")
    echo "Found ${results.size()} users"
}
```

### Pattern 3: HTTP Requests

```groovy
// ❌ PROBLEM
def client = new HttpClient()
stage('API Call') {
    def response = client.get('https://api.example.com/data')
    // ERROR: 'client' not serializable
}

// ✅ SOLUTION 1: Use httpRequest plugin
stage('API Call') {
    def response = httpRequest(
        url: 'https://api.example.com/data',
        authentication: 'api-credentials'
    )
    echo "Status: ${response.status}"
}

// ✅ SOLUTION 2: Use curl or wget
stage('API Call') {
    def response = sh(
        script: 'curl -s https://api.example.com/data',
        returnStdout: true
    ).trim()
    echo response
}

// ✅ SOLUTION 3: @NonCPS wrapper
@NonCPS
def makeHttpRequest(String url) {
    def connection = new URL(url).openConnection()
    try {
        connection.setRequestMethod('GET')
        return connection.inputStream.text
    } finally {
        connection.disconnect()
    }
}

stage('API Call') {
    def data = makeHttpRequest('https://api.example.com/data')
    echo data
}
```

### Pattern 4: Complex Iteration

```groovy
// ❌ PROBLEM
def map = [a: 1, b: 2, c: 3]
def iter = map.entrySet().iterator()
while (iter.hasNext()) {
    def entry = iter.next()
    // CPS problems with iterator
    stage("Process ${entry.key}") {
        sh "process ${entry.value}"
    }
}

// ✅ SOLUTION 1: Use .each
def map = [a: 1, b: 2, c: 3]
map.each { key, value ->
    stage("Process ${key}") {
        sh "process ${value}"
    }
}

// ✅ SOLUTION 2: Classic for loop
def items = ['a', 'b', 'c']
for (int i = 0; i < items.size(); i++) {
    def item = items[i]
    stage("Process ${item}") {
        sh "process ${item}"
    }
}

// ✅ SOLUTION 3: @NonCPS if no pipeline steps
@NonCPS
def processItems(Map items) {
    def results = []
    items.each { key, value ->
        // Pure computation only
        results << "${key}=${value}"
    }
    return results
}

def map = [a: 1, b: 2, c: 3]
def processed = processItems(map)
stage('Deploy') {
    processed.each { item ->
        sh "echo ${item}"
    }
}
```

### Pattern 5: Closures Capturing Non-Serializable Objects

```groovy
// ❌ PROBLEM
def file = new File('/tmp/config')
def processor = { ->
    return file.text  // Closure captures 'file'
}
stage('Process') {
    def content = processor()
    // ERROR: Closure captured non-serializable 'file'
    sh "process ${content}"
}

// ✅ SOLUTION 1: Don't capture, pass as parameter
def processor = { File f ->
    return f.text
}
def content = processor(new File('/tmp/config'))
stage('Process') {
    sh "process ${content}"
}

// ✅ SOLUTION 2: Capture serializable value
def filePath = '/tmp/config'
def processor = { ->
    return readFile(filePath)  // Captures String, not File
}
stage('Process') {
    def content = processor()
    sh "process ${content}"
}
```

### Pattern 6: Java Streams

```groovy
// ❌ PROBLEM
def stream = list.stream()
    .filter { it > 5 }
    .map { it * 2 }
stage('Process') {
    // ERROR: Stream not serializable
    def result = stream.collect(Collectors.toList())
}

// ✅ SOLUTION: Use Groovy collections
def result = list
    .findAll { it > 5 }
    .collect { it * 2 }
stage('Process') {
    sh "process ${result.join(',')}"
}

// OR @NonCPS
@NonCPS
def processStream(List items) {
    return items.stream()
        .filter { it > 5 }
        .map { it * 2 }
        .collect(Collectors.toList())
}

def result = processStream(list)
stage('Process') {
    sh "process ${result.join(',')}"
}
```

## The @NonCPS Annotation

### What @NonCPS Does

`@NonCPS` tells Jenkins **not** to apply CPS transformation to a method. This means:

**Advantages:**
- Runs much faster (no CPS overhead)
- Can use non-serializable objects safely
- Full Groovy language features available
- No serialization of local variables

**Limitations:**
- **Cannot call Pipeline steps** (`sh`, `echo`, `node`, etc.)
- Cannot call other CPS-transformed methods
- Not resumable if Jenkins restarts
- Runs to completion or fails (no suspension)

### When to Use @NonCPS

Use `@NonCPS` for:

1. **Pure functions** - No side effects, only computation
2. **Data transformation** - Parsing, formatting, calculations
3. **Complex logic** - Algorithms, validations
4. **Working with non-serializable objects** - File I/O, database queries
5. **Performance-critical code** - Avoid CPS overhead

**Do NOT use @NonCPS for:**

1. Methods that call Pipeline steps
2. Methods that need to survive Jenkins restarts
3. Long-running operations that should be interruptible

### @NonCPS Examples

```groovy
// ✅ GOOD: Pure function
@NonCPS
def calculateChecksum(String data) {
    return java.security.MessageDigest
        .getInstance('SHA-256')
        .digest(data.bytes)
        .encodeHex()
        .toString()
}

// ✅ GOOD: Data transformation
@NonCPS
def parseJsonFile(String filePath) {
    def file = new File(filePath)
    return new groovy.json.JsonSlurper().parse(file)
}

// ✅ GOOD: Complex logic
@NonCPS
def validateDeploymentConfig(Map config) {
    if (!config.environment) {
        throw new IllegalArgumentException("Missing 'environment'")
    }
    if (config.environment == 'prod' && !config.approver) {
        throw new IllegalArgumentException("Production requires approver")
    }
    return true
}

// ❌ BAD: Calling Pipeline steps
@NonCPS
def buildAndTest() {
    sh 'make build'  // ERROR: Cannot call Pipeline steps
    sh 'make test'
}

// ❌ BAD: Calling other CPS methods
@NonCPS
def deploy() {
    deployToEnvironment('production')  // ERROR if deployToEnvironment is CPS
}
```

### @NonCPS Best Practices

```groovy
// Pattern: Separate logic from execution
@NonCPS
def buildDeployCommand(Map config) {
    // Pure logic - builds command string
    def cmd = "deploy.sh"
    cmd += " --env ${config.env}"
    cmd += " --version ${config.version}"
    if (config.dryRun) {
        cmd += " --dry-run"
    }
    return cmd
}

// CPS method calls the @NonCPS logic and executes
def deploy(Map config) {
    def command = buildDeployCommand(config)
    sh command
}

// Usage
deploy(env: 'staging', version: '1.2.3', dryRun: false)
```

## Advanced Troubleshooting

### Debugging Serialization Issues

**Method 1: Add logging**
```groovy
def debugVariable(name, value) {
    echo "Variable '${name}':"
    echo "  Class: ${value.getClass().name}"
    echo "  Serializable: ${value instanceof Serializable}"
    echo "  Value: ${value}"
}

def myVar = someFunction()
debugVariable('myVar', myVar)
```

**Method 2: Test serialization**
```groovy
@NonCPS
def testSerialization(obj) {
    try {
        def baos = new ByteArrayOutputStream()
        def oos = new ObjectOutputStream(baos)
        oos.writeObject(obj)
        oos.close()
        return "Serializable: ${baos.size()} bytes"
    } catch (Exception e) {
        return "NOT Serializable: ${e.message}"
    }
}

def myVar = someFunction()
echo testSerialization(myVar)
```

### Finding Suspension Points

Add logging to track where pipeline suspends:

```groovy
def stage1() {
    echo "=== Stage 1 START ==="
    echo "About to call sh"
    sh 'make build'  // Suspension point
    echo "After sh call"
    echo "=== Stage 1 END ==="
}
```

If you see "About to call sh" but not "After sh call" in logs after restart, that's where it suspended.

### Handling Unavoidable Non-Serializable Objects

**Strategy 1: Recreate after suspension**
```groovy
def getConnection() {
    // Helper to recreate connection
    return Sql.newInstance(jdbcUrl, user, pass)
}

def sql = getConnection()
def results = sql.rows("SELECT * FROM users")
sql.close()

stage('Process') {
    // Suspension point - 'sql' already closed and null
    sh "process data"
}

// Need connection again? Recreate
sql = getConnection()
def moreResults = sql.rows("SELECT * FROM products")
sql.close()
```

**Strategy 2: Extract data immediately**
```groovy
// Don't store the connection, just the data
def userData = null
def sql = Sql.newInstance(jdbcUrl, user, pass)
try {
    userData = sql.rows("SELECT * FROM users")  // Returns serializable List<Map>
} finally {
    sql.close()
}

stage('Process') {
    // Safe: userData is a List<Map>, fully serializable
    echo "Processing ${userData.size()} users"
    userData.each { user ->
        sh "process-user ${user.id}"
    }
}
```

### Parallel Execution and Serialization

A shared `Map` is not the problem by itself. The failure mode here is concurrent mutation across `parallel` branches, which is brittle even when the values are serializable.

```groovy
// ❌ PROBLEM: parallel branches mutate the same shared map
def results = [:]
parallel(
    'task1': {
        results.task1 = sh(script: 'echo task1', returnStdout: true).trim()
    },
    'task2': {
        results.task2 = sh(script: 'echo task2', returnStdout: true).trim()
    }
)

// ✅ SOLUTION: keep branch output local, then merge after parallel
parallel(
    'task1': {
        def output = sh(script: 'echo task1', returnStdout: true).trim()
        writeFile file: 'task1.result', text: output
    },
    'task2': {
        def output = sh(script: 'echo task2', returnStdout: true).trim()
        writeFile file: 'task2.result', text: output
    }
)

def results = [
    task1: readFile('task1.result').trim(),
    task2: readFile('task2.result').trim()
]

@NonCPS
def queryInNonCPS(String sql) {
    def conn = getDbConnection()
    try {
        return conn.query(sql)
    } finally {
        conn.close()
    }
}
```

## Summary

### CPS Quick Checklist

Before writing pipeline code, ask:

- [ ] Will this variable be in scope at a Pipeline step call?
- [ ] Is every variable serializable?
- [ ] Am I using iterators or streams that might not serialize?
- [ ] Do I have non-serializable objects (File, Connection, etc.)?
- [ ] Should this be @NonCPS? (pure function, no Pipeline steps)
- [ ] Am I capturing non-serializable objects in closures?
- [ ] Could this code suspend and resume successfully?

### Golden Rules

1. **Use serializable types only** - String, Integer, List, Map of safe types
2. **@NonCPS for pure functions** - No Pipeline steps, runs to completion
3. **Dispose resources immediately** - Don't store File, Connection, etc.
4. **Test suspension points** - Assume pipeline can pause anywhere
5. **Prefer Groovy collections** - Over Java 8 streams
6. **Extract data, not objects** - Get the data, close the resource
7. **When in doubt, check serializability** - Use debug methods

### Common Error Quick Fixes

| Error | Quick Fix |
|-------|-----------|
| `NotSerializableException` | Remove non-serializable variable or use `@NonCPS` |
| `CpsCallableInvocation` | Replace iterator with `.each` or for loop |
| `MissingPropertyException` | Check variable scope in closures |
| Pipeline steps fail in `@NonCPS` | Remove `@NonCPS` or move steps outside |
| Slow execution | Use `@NonCPS` for heavy computation |
| Data lost after restart | Ensure data is serializable, not in `@NonCPS` |
