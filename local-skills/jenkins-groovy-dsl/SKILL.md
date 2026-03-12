---
name: jenkins-groovy-dsl
description: Expert guidance for Jenkins Groovy DSL programming in Jenkinsfiles and shared libraries. Use when writing or reviewing Groovy code in Jenkins pipelines, troubleshooting CPS (Continuation Passing Style) serialization issues, understanding Jenkins-specific Groovy limitations, or implementing shared library code. Covers design patterns, anti-patterns, workarounds for DSL constraints, safe coding practices, and advanced Groovy techniques specific to Jenkins automation.
license: Complete terms in LICENSE.txt
---

# Jenkins Groovy DSL Best Practices

Expert guidance for writing robust, efficient Groovy code in Jenkins pipelines and shared libraries, with special focus on CPS serialization, design limitations, and Jenkins-specific constraints.

## When to Use This Skill

- Writing Groovy code in Jenkinsfiles (Declarative or Scripted)
- Developing Jenkins shared libraries in Groovy
- Troubleshooting CPS (Continuation Passing Style) serialization errors
- Understanding `NotSerializableException` or `CpsCallableInvocation` errors
- Implementing complex logic in pipeline scripts
- Refactoring pipeline code to avoid CPS issues
- Working around Jenkins DSL limitations
- Optimizing Groovy code for Jenkins execution environment

## Critical: Understanding CPS

Jenkins pipelines run in a **Continuation Passing Style (CPS)** environment. This is the single most important concept for writing reliable Jenkins Groovy code.

### What is CPS?

CPS allows Jenkins to pause pipeline execution and resume it later (e.g., after a restart or waiting for approval). To enable this:

- Jenkins serializes the pipeline state to disk
- All variables must be serializable
- Many standard Groovy features behave differently or fail

**See [references/cps-problems.md](references/cps-problems.md) for comprehensive CPS troubleshooting**

### Quick CPS Rules

1. **Use `@NonCPS` for pure functions** - Non-CPS methods run faster but can't call CPS-transformed methods
2. **Avoid non-serializable objects** - No File, Stream, Database connections as variables
3. **Prefer simple types** - String, Integer, Boolean, List, Map are safe
4. **Iterators are dangerous** - Use `.each{}` or list comprehensions carefully
5. **Script blocks isolate CPS** - `script {}` in Declarative or `@NonCPS` in functions

## Quick Security & Safety Checklist

- [ ] No untrusted input in string interpolation (use `sh` with single quotes)
- [ ] All complex objects disposed or set to null before stage ends
- [ ] No iterators or streams stored in variables
- [ ] Closures don't capture non-serializable objects
- [ ] `@NonCPS` methods marked correctly (pure functions only)
- [ ] Try-catch blocks properly handle serialization
- [ ] No shared mutable state between stages

## Core Groovy DSL Patterns

### 1. String Interpolation (GString)

```groovy
// Groovy supports powerful string interpolation
def version = "1.2.3"
def name = "myapp"

// Single quotes - literal string
echo 'Version is ${version}'  // Prints: Version is ${version}

// Double quotes - interpolation
echo "Version is ${version}"  // Prints: Version is 1.2.3

// Multiline with interpolation
def message = """
Build ${env.BUILD_NUMBER}
Application: ${name}
Version: ${version}
"""

// ⚠️ Security: Never interpolate untrusted input
def userInput = params.BRANCH_NAME
sh "git checkout ${userInput}"  // ❌ INJECTION RISK

// ✅ CORRECT - use single quotes and shell escaping
sh "git checkout '${userInput}'"  // Still risky
// Better: validate first
if (userInput ==~ /^[a-zA-Z0-9_\-\/]+$/) {
    sh "git checkout '${userInput}'"
}
```

### 2. Safe Navigation Operator

```groovy
// Avoid NullPointerException with ?.
def result = someObject?.property?.method()

// Traditional null check
if (config != null && config.database != null) {
    echo config.database.host
}

// Groovy safe navigation
echo config?.database?.host  // Returns null if any part is null

// With Elvis operator for defaults
def host = config?.database?.host ?: 'localhost'
```

### 3. Collections and Closures

```groovy
// Lists
def environments = ['dev', 'staging', 'prod']

// Iteration (careful with CPS - see cps-problems.md)
environments.each { env ->
    echo "Deploying to ${env}"
}

// Map/filter/collect
def upperEnvs = environments.collect { it.toUpperCase() }
def prodOnly = environments.findAll { it.contains('prod') }

// Maps
def config = [
    timeout: 60,
    retries: 3,
    notify: true
]

// Access
echo config.timeout      // 60
echo config['timeout']   // 60
config.each { k, v ->
    echo "${k} = ${v}"
}
```

### 4. Closures and Delegation

```groovy
// Closures are code blocks that can be passed around
def multiplier = { x -> x * 2 }
assert multiplier(5) == 10

// Pipeline DSL uses closures heavily
pipeline {
    agent any
    stages {
        stage('Build') {  // This is a closure
            steps {       // This is also a closure
                echo 'Building'
            }
        }
    }
}

// Custom DSL-like methods
def withRetry(int times, Closure action) {
    for (int i = 0; i < times; i++) {
        try {
            action.call()
            return
        } catch (Exception e) {
            if (i == times - 1) throw e
            echo "Retry ${i + 1}/${times}"
        }
    }
}

// Usage
withRetry(3) {
    sh 'flaky-command.sh'
}
```

### 5. Exception Handling

```groovy
// Try-catch-finally
try {
    sh 'risky-command'
} catch (Exception e) {
    echo "Error: ${e.message}"
    currentBuild.result = 'FAILURE'
    throw e  // Re-throw if needed
} finally {
    cleanWs()
}

// Catching specific exceptions
try {
    timeout(time: 5, unit: 'MINUTES') {
        sh 'long-running-task'
    }
} catch (org.jenkinsci.plugins.workflow.steps.FlowInterruptedException e) {
    echo "Timeout occurred"
    currentBuild.result = 'ABORTED'
}

// ⚠️ CPS Warning: Exception handling with non-serializable objects
try {
    def file = new File('/tmp/data')  // Non-serializable
    // If pipeline suspends here, serialization fails
} catch (Exception e) {
    // Handle
}
// ✅ Solution: Use @NonCPS or script blocks
```

## Design Limitations and Workarounds

Jenkins Groovy DSL has specific constraints not present in standard Groovy.

**See [references/design-limitations.md](references/design-limitations.md) for comprehensive coverage**

### Key Limitations

1. **No class definitions in pipeline scripts** - Use shared libraries instead
2. **Limited access to Jenkins internals** - Must use approved plugin APIs
3. **Sandbox restrictions** - Many Groovy methods require admin approval
4. **No direct file I/O in pipeline** - Use `readFile()`, `writeFile()` steps
5. **CPS transformation overhead** - Some code patterns are very slow

### Common Workarounds

```groovy
// ❌ Can't define classes in pipeline
class MyHelper {
    static void doSomething() {}
}

// ✅ Use shared library instead (see shared-libraries.md)
@Library('my-library') _
MyHelper.doSomething()

// ❌ Direct file operations
def file = new File('/workspace/data.txt')
file.text = 'content'

// ✅ Use Pipeline steps
writeFile file: 'data.txt', text: 'content'
def content = readFile 'data.txt'

// ❌ Complex iteration (CPS problems)
for (def entry : map.entrySet()) {
    // Serialization issues
}

// ✅ Use Groovy collections
map.each { key, value ->
    // Works better with CPS
}
```

## Shared Library Development

For reusable Groovy code across multiple pipelines.

**See [references/shared-libraries.md](references/shared-libraries.md) for complete guide**

### Quick Shared Library Structure

```
(root)
├── vars/                  # Global variables (DSL methods)
│   ├── deployApp.groovy
│   └── buildDocker.groovy
├── src/                   # Groovy classes (regular Groovy)
│   └── org/company/
│       └── Helper.groovy
└── resources/             # Non-Groovy files
    └── config.json
```

### Example Global Variable (`vars/deployApp.groovy`)

```groovy
// This becomes available as `deployApp()` in pipelines
def call(Map config) {
    pipeline {
        agent any
        stages {
            stage('Deploy') {
                steps {
                    script {
                        echo "Deploying ${config.app} to ${config.env}"
                        sh "./deploy.sh ${config.app} ${config.env}"
                    }
                }
            }
        }
    }
}
```

### Usage in Pipeline

```groovy
@Library('my-shared-lib') _

deployApp(
    app: 'myservice',
    env: 'production'
)
```

## Groovy DSL Patterns and Idioms

**See [references/groovy-dsl-patterns.md](references/groovy-dsl-patterns.md) for extensive examples**

### Pattern Matching

```groovy
// Switch statements
def environment = params.ENV
switch(environment) {
    case 'prod':
        deploy('production')
        break
    case 'staging':
        deploy('staging')
        break
    case ~/dev-.*/:  // Regex matching
        deploy('development')
        break
    default:
        error "Unknown environment: ${environment}"
}
```

### Elvis and Null Coalescing

```groovy
// Elvis operator ?: provides default values
def timeout = params.TIMEOUT ?: 60
def branch = env.BRANCH_NAME ?: 'main'

// Chained
def host = config?.db?.host ?: env.DB_HOST ?: 'localhost'
```

### List and Map Builders

```groovy
// List comprehension
def numbers = 1..10
def evens = numbers.findAll { it % 2 == 0 }
def squares = numbers.collect { it ** 2 }

// Map building
def config = [:]
config.timeout = 60
config.retries = 3
// Or
def config = [
    timeout: 60,
    retries: 3
]

// Conditional map building
def buildConfig() {
    def cfg = [:]
    cfg.timeout = params.TIMEOUT ?: 60
    if (env.BRANCH_NAME == 'main') {
        cfg.deploy = true
    }
    return cfg
}
```

## Common Anti-Patterns to Avoid

### 1. Storing Non-Serializable Objects

```groovy
// ❌ WRONG - will cause NotSerializableException
def connection = sql.newInstance(url, user, pass)
stage('Query') {
    def results = connection.execute("SELECT * FROM users")
}
// Pipeline suspension here will FAIL - connection not serializable

// ✅ CORRECT - create and dispose in same @NonCPS or script block
@NonCPS
def queryDatabase(String query) {
    def connection = null
    try {
        connection = sql.newInstance(url, user, pass)
        return connection.execute(query)
    } finally {
        connection?.close()
    }
}
```

### 2. Complex Iteration

```groovy
// ❌ WRONG - iterator serialization issues
def iter = list.iterator()
while (iter.hasNext()) {
    def item = iter.next()
    // Process
}

// ✅ CORRECT - use Groovy each
list.each { item ->
    // Process
}

// Or classic for loop
for (int i = 0; i < list.size(); i++) {
    def item = list[i]
    // Process
}
```

### 3. Misusing @NonCPS

```groovy
// ❌ WRONG - @NonCPS calling Pipeline steps
@NonCPS
def buildAndDeploy() {
    sh 'make build'  // ERROR: Can't call Pipeline steps from @NonCPS
    sh 'make deploy'
}

// ✅ CORRECT - Keep @NonCPS for pure logic
@NonCPS
def calculateVersion(int buildNumber, String branch) {
    def base = "1.0"
    return "${base}.${buildNumber}"
}

def buildAndDeploy() {
    def version = calculateVersion(env.BUILD_NUMBER as int, env.BRANCH_NAME)
    sh "make build VERSION=${version}"
    sh "make deploy VERSION=${version}"
}
```

### 4. Shared Mutable State

```groovy
// ❌ WRONG - shared mutable map between stages
def results = [:]

stage('Test A') {
    results.testA = 'passed'  // CPS serialization issues
}

stage('Test B') {
    results.testB = 'passed'
}

// ✅ CORRECT - use immutable or rebuild each time
def testResults = []

stage('Test A') {
    testResults = testResults + ['testA': 'passed']
}

stage('Test B') {
    testResults = testResults + ['testB': 'passed']
}
```

## Performance Tips

1. **Use `@NonCPS` for heavy computation** - Bypasses CPS overhead
2. **Minimize pipeline steps** - Each step has serialization cost
3. **Batch shell commands** - One `sh` step vs many
4. **Avoid deep nesting** - CPS transformation is recursive
5. **Cache compiled scripts** - In shared libraries

## Debugging Tips

### Enable CPS Debugging

```groovy
// Show CPS transformation details
@groovy.transform.CompileStatic  // Can help identify issues
def myMethod() {
    // code
}
```

### Print Variable Types

```groovy
def debugVar(var) {
    echo "Type: ${var.getClass().name}"
    echo "Value: ${var}"
    echo "Serializable: ${var instanceof Serializable}"
}
```

### Stack Trace Analysis

When you see `NotSerializableException`:
1. Look for the class name (e.g., `java.io.File`)
2. Find where that object is created
3. Ensure it's disposed before pipeline suspension points
4. Consider moving to `@NonCPS` method

## Quick Reference

### Safe Types (Serializable)
- `String`, `Integer`, `Long`, `Boolean`, `Double`
- `List`, `Map`, `Set` (if contents are serializable)
- Most primitives and wrappers
- `java.util.Date`
- Custom classes marked `implements Serializable`

### Unsafe Types (Not Serializable)
- `File`, `FileInputStream`, `FileOutputStream`
- Database connections (SQL, JDBC)
- Network sockets
- Threads
- Most Java 8+ Streams
- Iterators in some cases
- Complex Jenkins internal objects

### When to Use `@NonCPS`
- Pure functions (no side effects)
- Complex calculations
- String/data manipulation
- No calls to Pipeline steps (`sh`, `echo`, `checkout`, etc.)
- No interaction with Jenkins runtime

### When NOT to Use `@NonCPS`
- Methods that call Pipeline steps
- Methods that need to survive pipeline restarts
- Long-running operations that should be resumable

## Additional Resources

- [CPS Problems and Solutions](references/cps-problems.md) - Comprehensive CPS troubleshooting
- [Groovy DSL Patterns](references/groovy-dsl-patterns.md) - Idiomatic Groovy for Jenkins
- [Design Limitations](references/design-limitations.md) - Jenkins DSL constraints and workarounds
- [Shared Libraries Guide](references/shared-libraries.md) - Building reusable pipeline code

## Example: Complete Groovy Pipeline

```groovy
@Library('my-shared-lib') _

// Safe helper function
@NonCPS
def parseVersion(String tag) {
    def matcher = (tag =~ /v(\d+)\.(\d+)\.(\d+)/)
    return matcher ? [
        major: matcher[0][1],
        minor: matcher[0][2],
        patch: matcher[0][3]
    ] : null
}

pipeline {
    agent { label 'docker' }

    parameters {
        string(name: 'VERSION_TAG', defaultValue: 'v1.0.0', description: 'Version tag')
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'])
    }

    stages {
        stage('Parse Version') {
            steps {
                script {
                    // Call @NonCPS function safely
                    def ver = parseVersion(params.VERSION_TAG)
                    if (!ver) {
                        error "Invalid version format: ${params.VERSION_TAG}"
                    }

                    // Store in environment for other stages
                    env.MAJOR = ver.major
                    env.MINOR = ver.minor
                    env.PATCH = ver.patch

                    echo "Building version ${env.MAJOR}.${env.MINOR}.${env.PATCH}"
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    // Safe string interpolation
                    def version = "${env.MAJOR}.${env.MINOR}.${env.PATCH}"
                    sh "make build VERSION=${version}"

                    // Safe iteration
                    def targets = ['app', 'worker', 'api']
                    targets.each { target ->
                        echo "Built ${target}"
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                expression { params.ENVIRONMENT in ['staging', 'prod'] }
            }
            steps {
                script {
                    // Using shared library (if available)
                    deployApp(
                        app: 'myservice',
                        env: params.ENVIRONMENT,
                        version: "${env.MAJOR}.${env.MINOR}.${env.PATCH}"
                    )
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```
