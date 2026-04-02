# Jenkins DSL Design Limitations and Workarounds

Comprehensive guide to Jenkins Pipeline DSL constraints, limitations, and proven workarounds.

## Table of Contents

- [Sandbox Restrictions](#sandbox-restrictions)
- [No Class Definitions](#no-class-definitions)
- [File System Access](#file-system-access)
- [Script Approval](#script-approval)
- [Memory and Performance](#memory-and-performance)
- [Parallel Execution Limits](#parallel-execution-limits)
- [Plugin Dependencies](#plugin-dependencies)
- [Anti-Patterns](#anti-patterns)

## Sandbox Restrictions

### What is the Sandbox?

The Jenkins Pipeline sandbox runs untrusted code with restricted access to:
- Java/Groovy standard library methods
- Jenkins internal APIs
- File system operations
- Network access
- System resources

### Whitelist vs Greylist

**Whitelisted** - Automatically approved, safe methods
**Greylisted** - Require admin approval via Script Approval

### Common Sandbox Issues

```groovy
// ❌ FAILS: Method not whitelisted
def file = new File('/tmp/data.txt')
def content = file.text  // ERROR: getters may require approval

// ✅ WORKAROUND: Use Pipeline steps
def content = readFile('/tmp/data.txt')

// ❌ FAILS: Direct Jenkins API access
import jenkins.model.Jenkins
def instance = Jenkins.getInstance()  // ERROR: Not allowed in sandbox

// ✅ WORKAROUND: Use approved plugin APIs, a trusted shared library, or script approval
@Library('my-lib@master') _
// Untrusted shared-library code still runs in the sandbox
```

### Bypassing Sandbox (When Appropriate)

**Option 1: Trusted Shared Library `src/` code**

Shared-library `src/` code still gets CPS transformation. Jenkins internal API access here requires a trusted library or equivalent approval.

```groovy
// In trusted shared library: src/org/company/Helper.groovy
package org.company

class Helper {
    static def getJenkinsVersion() {
        // Requires a trusted library because this uses Jenkins internal APIs
        return jenkins.model.Jenkins.instance.version
    }
}

// In pipeline (runs in sandbox)
@Library('my-lib') _
import org.company.Helper

def version = Helper.getJenkinsVersion()
```

**Option 2: Disable sandbox** (security risk)
```groovy
// In Jenkinsfile - only for trusted repos
@Library('my-lib') _
// Use 'Do not run in sandbox' option in job config
```

**Option 3: Script Approval**
- Attempt to run code
- Admin approves via "Manage Jenkins" → "In-process Script Approval"
- Future runs allowed

## No Class Definitions

### The Problem

```groovy
// ❌ FAILS: Cannot define classes in Pipeline scripts
class DeploymentConfig {
    String environment
    String version
}

def config = new DeploymentConfig()  // ERROR
```

### Workaround 1: Use Maps

```groovy
// ✅ Simple: Use maps instead of classes
def createConfig(String env, String ver) {
    return [
        environment: env,
        version: ver,
        validate: { cfg ->
            if (!cfg.environment || !cfg.version) {
                error "Invalid configuration"
            }
        }
    ]
}

def config = createConfig('production', '1.2.3')
config.validate(config)
```

### Workaround 2: Shared Library Classes

```groovy
// In shared library: src/org/company/DeploymentConfig.groovy
package org.company

class DeploymentConfig implements Serializable {
    String environment
    String version

    DeploymentConfig(String env, String ver) {
        this.environment = env
        this.version = ver
    }

    def validate() {
        if (!environment || !version) {
            throw new IllegalStateException('Invalid configuration')
        }
    }
}

// In pipeline
@Library('my-lib') _
import org.company.DeploymentConfig

def config = new DeploymentConfig('production', '1.2.3')
config.validate()  // Uncaught exceptions from library classes still fail the build
```

### Workaround 3: Closure-Based "Classes"

```groovy
def createDeployment(String env, String ver) {
    def state = [
        environment: env,
        version: ver
    ]

    return [
        getEnvironment: { -> state.environment },
        getVersion: { -> state.version },
        setReplicas: { n -> state.replicas = n },
        validate: {
            if (!state.environment || !state.version) {
                error "Invalid configuration"
            }
        },
        deploy: {
            echo "Deploying ${state.version} to ${state.environment}"
        }
    ]
}

def deployment = createDeployment('production', '1.2.3')
deployment.setReplicas(5)
deployment.validate()
deployment.deploy()
```

## File System Access

### The Problem

Direct file I/O is restricted or dangerous in pipelines.

```groovy
// ❌ FAILS or DANGEROUS
def file = new File('/workspace/data.txt')
file.text = 'content'  // May fail in sandbox, CPS issues

// ❌ DANGEROUS: Path traversal
def userPath = params.FILE_PATH
def file = new File(userPath)  // Security risk!
```

### Workaround: Use Pipeline Steps

```groovy
// ✅ CORRECT: Use writeFile/readFile
writeFile file: 'data.txt', text: 'content'
def content = readFile('data.txt')

// Write with encoding
writeFile file: 'data.txt', text: 'content', encoding: 'UTF-8'

// Read JSON
def jsonText = readFile('config.json')
def config = readJSON(text: jsonText)

// Or use readJSON directly
def config = readJSON(file: 'config.json')

// Write JSON
def data = [name: 'app', version: '1.2.3']
writeJSON(file: 'output.json', json: data)

// Read YAML
def yaml = readYaml(file: 'config.yaml')

// Write YAML
writeYaml(file: 'output.yaml', data: data)
```

### File Listing

```groovy
// ❌ WRONG: Direct file system access
def dir = new File('/workspace')
def files = dir.listFiles()

// ✅ CORRECT: Use findFiles step
def files = findFiles(glob: '**/*.java')
files.each { file ->
    echo "Found: ${file.name} (${file.length} bytes)"
}

// Or use sh with output
def fileList = sh(
    script: 'find . -name "*.java"',
    returnStdout: true
).trim().split('\n')
```

### File Existence Check

```groovy
// ❌ WRONG
def file = new File('config.json')
if (file.exists()) {
    // ...
}

// ✅ CORRECT
def exists = fileExists('config.json')
if (exists) {
    def config = readJSON(file: 'config.json')
}
```

## Script Approval

### Handling Unapproved Methods

**Strategy 1: Wait for Admin Approval**
1. Run pipeline
2. Note error: "Scripts not permitted to use method X"
3. Admin approves via "Manage Jenkins" → "In-process Script Approval"
4. Re-run pipeline

**Strategy 2: Use Approved Alternatives**

```groovy
// ❌ May need approval
def date = new Date()
def formatted = date.format('yyyy-MM-dd')

// ✅ Often approved
def formatted = new Date().format('yyyy-MM-dd')

// Or use shell
def date = sh(script: 'date +%Y-%m-%d', returnStdout: true).trim()
```

**Strategy 3: Move to Shared Library**

Code in `src/` is still CPS-transformed. Untrusted libraries remain sandboxed; trusted libraries can encapsulate restricted operations.

```groovy
// In shared library: src/org/company/Util.groovy
package org.company

class Util {
    static def getCurrentDate() {
        return new Date().format('yyyy-MM-dd HH:mm:ss')
    }
}

// In pipeline
@Library('my-lib') _
import org.company.Util

echo Util.getCurrentDate()
```

If this still hits a sandbox restriction, use script approval or move the helper into a trusted library.

### Pre-Approving Methods

Admins can pre-approve method signatures:

1. Go to "Manage Jenkins" → "In-process Script Approval"
2. Add to whitelist: `method java.util.Date format java.lang.String`
3. All pipelines can now use this method

## Memory and Performance

### The Problem

Pipelines run in Jenkins master JVM, consuming memory and CPU.

### Limitation 1: Large Data Structures

```groovy
// ❌ DANGEROUS: Large data in memory
def logLines = sh(
    script: 'cat huge-log-file.log',
    returnStdout: true
).split('\n')  // May cause OOM

// ✅ BETTER: Process in chunks or externally
sh '''
    cat huge-log-file.log | grep ERROR > errors.log
    wc -l errors.log
'''

// Or use @NonCPS for processing
@NonCPS
def processLargeFile(String content) {
    // Process efficiently
    return content.split('\n')
        .findAll { it.contains('ERROR') }
        .take(100)  // Limit results
}
```

### Limitation 2: Long-Running Computation

```groovy
// ❌ BAD: CPU-intensive work on master
def result = 0
for (int i = 0; i < 1000000; i++) {
    result += complexCalculation(i)  // Blocks Jenkins master
}

// ✅ BETTER: Offload to agent
node('compute-agent') {
    def result = sh(
        script: './expensive-computation.sh',
        returnStdout: true
    ).trim()
}

// Or use @NonCPS for efficiency
@NonCPS
def performCalculations(int count) {
    def result = 0
    for (int i = 0; i < count; i++) {
        result += i * i
    }
    return result
}
```

### Limitation 3: Too Many Pipeline Steps

```groovy
// ❌ INEFFICIENT: Many separate steps
def files = findFiles(glob: '**/*.log')
files.each { file ->
    sh "process ${file.name}"  // 1000s of steps = slow
}

// ✅ EFFICIENT: Batch operations
def fileList = findFiles(glob: '**/*.log')
    .collect { it.name }
    .join(' ')
sh "process-all.sh ${fileList}"

// Or single shell script
sh '''
    for file in *.log; do
        process "$file"
    done
'''
```

## Parallel Execution Limits

### The Problem

Too many parallel branches can overwhelm Jenkins.

```groovy
// ❌ DANGEROUS: 1000s of parallel branches
def tasks = [:]
(1..1000).each { i ->
    tasks["task-${i}"] = {
        sh "process-${i}.sh"
    }
}
parallel tasks  // May exhaust threads
```

### Workaround 1: Batch Parallel Execution

```groovy
// ✅ BETTER: Process in batches
def items = (1..1000).toList()
def batchSize = 10

for (int i = 0; i < items.size(); i += batchSize) {
    def batch = items[i..Math.min(i + batchSize - 1, items.size() - 1)]

    def tasks = batch.collectEntries { item ->
        ["task-${item}": {
            sh "process-${item}.sh"
        }]
    }

    parallel tasks
}
```

### Workaround 2: Throttle Plugin

```groovy
// ✅ Use throttle plugin to limit concurrency
throttle(['my-resource']) {
    parallel {
        stage('Task 1') { /* ... */ }
        stage('Task 2') { /* ... */ }
        stage('Task 3') { /* ... */ }
    }
}
```

### Workaround 3: Matrix Builds (Declarative)

```groovy
// ✅ Declarative matrix for controlled parallelism
pipeline {
    agent none
    stages {
        stage('Test') {
            matrix {
                axes {
                    axis {
                        name 'PLATFORM'
                        values 'linux', 'windows', 'mac'
                    }
                    axis {
                        name 'BROWSER'
                        values 'chrome', 'firefox', 'safari'
                    }
                }
                agent { label "${PLATFORM}" }
                stages {
                    stage('Run Test') {
                        steps {
                            sh "test-${BROWSER}.sh"
                        }
                    }
                }
            }
        }
    }
}
```

## Plugin Dependencies

### The Problem

Pipelines depend on plugins, which may not be installed or compatible.

```groovy
// ❌ FAILS if Docker Pipeline Plugin not installed
pipeline {
    agent {
        docker {
            image 'maven:3.8-jdk-11'  // Requires plugin
        }
    }
}
```

### Workaround 1: Check Plugin Availability

```groovy
// ✅ Graceful degradation
def hasDockerPlugin() {
    try {
        // Try to use docker-specific syntax
        return true
    } catch (Exception e) {
        return false
    }
}

if (hasDockerPlugin()) {
    docker.image('maven:3.8').inside {
        sh 'mvn clean install'
    }
} else {
    // Fallback: Use agent with Maven pre-installed
    node('maven') {
        sh 'mvn clean install'
    }
}
```

### Workaround 2: Document Requirements

```groovy
// Add comment at top of Jenkinsfile
/*
 * Required Plugins:
 * - Pipeline: 2.6+
 * - Docker Pipeline: 1.24+
 * - Kubernetes: 1.29+
 */

// Or check programmatically (in shared library)
// Trusted library or approved signatures required: uses Jenkins internal APIs
@NonCPS
def checkPlugins(List required) {
    def pm = jenkins.model.Jenkins.instance.pluginManager
    required.each { pluginName ->
        if (!pm.getPlugin(pluginName)?.isEnabled()) {
            error "Required plugin not installed: ${pluginName}"
        }
    }
}
```

### Workaround 3: Conditional Plugin Usage

```groovy
// Detect available features
def canUseKubernetes = false
try {
    // This will fail if plugin not available
    podTemplate(label: 'test') {}
    canUseKubernetes = true
} catch (Exception e) {
    echo "Kubernetes plugin not available"
}

if (canUseKubernetes) {
    podTemplate(containers: [containerTemplate(name: 'maven', image: 'maven:3.8')]) {
        // ...
    }
} else {
    node('maven') {
        // Fallback
    }
}
```

## Anti-Patterns

### Anti-Pattern 1: Implicit Global State with Side Effects

Sequential stages can pass serializable values safely, but hidden side effects make pipelines harder to reason about and become especially risky when reused in `parallel`.

```groovy
// ❌ BAD: helper mutates outer pipeline state as a side effect
def buildState = [:]
def remember = { key, value ->
    buildState[key] = value
}

stage('Build') {
    remember('image', "app:${env.BUILD_NUMBER}")
}

stage('Deploy') {
    sh "deploy --image ${buildState.image}"
}

// ✅ GOOD: make the handoff explicit with serializable state
def buildState = [:]

stage('Build') {
    buildState = [image: "app:${env.BUILD_NUMBER}"]
}

stage('Deploy') {
    sh "deploy --image ${buildState.image}"
}
```

### Anti-Pattern 2: Overusing script {} Blocks

```groovy
// ❌ BAD: Everything in script blocks (defeats purpose of Declarative)
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                script {
                    // 100 lines of Groovy
                    def x = 1
                    def y = 2
                    // ...
                }
            }
        }
    }
}

// ✅ GOOD: Use Declarative features, move logic to functions
def buildVersion() {
    // Complex logic here
    return "1.2.3"
}

pipeline {
    agent any
    environment {
        VERSION = buildVersion()
    }
    stages {
        stage('Build') {
            steps {
                sh "make build VERSION=${VERSION}"
            }
        }
    }
}
```

### Anti-Pattern 3: Hardcoded Values

```groovy
// ❌ BAD: Hardcoded configuration
stage('Deploy') {
    sh 'deploy.sh production us-east-1 my-app-v1.2.3'
}

// ✅ GOOD: Parameterized
pipeline {
    agent any
    parameters {
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'production'])
        choice(name: 'REGION', choices: ['us-east-1', 'us-west-2', 'eu-west-1'])
        string(name: 'VERSION', defaultValue: '1.2.3')
    }
    stages {
        stage('Deploy') {
            steps {
                script {
                    def version = params.VERSION?.trim()
                    if (!version || !(version ==~ /^[0-9A-Za-z._-]+$/)) {
                        error 'Invalid VERSION parameter'
                    }

                    withEnv([
                        "DEPLOY_ENV=${params.ENVIRONMENT}",
                        "DEPLOY_REGION=${params.REGION}",
                        "DEPLOY_VERSION=my-app-v${version}"
                    ]) {
                        sh 'deploy.sh "$DEPLOY_ENV" "$DEPLOY_REGION" "$DEPLOY_VERSION"'
                    }
                }
            }
        }
    }
}
```

### Anti-Pattern 4: Catching All Exceptions Without Re-throwing

```groovy
// ❌ BAD: Swallowing errors
stage('Build') {
    try {
        sh 'make build'
    } catch (Exception e) {
        echo "Build failed, but continuing..."
        // ERROR: Pipeline continues as if nothing happened
    }
}

// ✅ GOOD: Handle specifically or re-throw
stage('Build') {
    try {
        sh 'make build'
    } catch (Exception e) {
        echo "Build failed: ${e.message}"
        currentBuild.result = 'FAILURE'
        throw e  // Fail the pipeline
    }
}

// Or handle specific failures
stage('Build') {
    try {
        sh 'make build'
    } catch (Exception e) {
        if (e.message.contains('out of memory')) {
            echo "OOM error - cleaning up and retrying"
            sh 'make clean'
            sh 'make build'
        } else {
            throw e
        }
    }
}
```

### Anti-Pattern 5: Not Using Timeouts

```groovy
// ❌ BAD: No timeout, may hang forever
stage('Deploy') {
    input message: 'Deploy to production?'
    sh 'deploy.sh'
}

// ✅ GOOD: Always timeout interactive/risky operations
stage('Deploy') {
    timeout(time: 10, unit: 'MINUTES') {
        input message: 'Deploy to production?'
    }
    timeout(time: 1, unit: 'HOURS') {
        sh 'deploy.sh'
    }
}

// Or at pipeline level
pipeline {
    agent any
    options {
        timeout(time: 2, unit: 'HOURS')  // Entire pipeline
    }
    // ...
}
```

### Anti-Pattern 6: Ignoring Return Values

```groovy
// ❌ BAD: Ignoring failures
sh 'test.sh'  // Fails silently if return code != 0
sh 'deploy.sh'

// ✅ GOOD: Check results
def testResult = sh(script: 'test.sh', returnStatus: true)
if (testResult != 0) {
    error "Tests failed with status ${testResult}"
}

// Or use returnStdout
def version = sh(script: 'git describe --tags', returnStdout: true).trim()
echo "Deploying version: ${version}"
```

### Anti-Pattern 7: Massive Jenkinsfiles

```groovy
// ❌ BAD: 1000+ line Jenkinsfile
// Everything in one file, hard to maintain

// ✅ GOOD: Use shared libraries
@Library('my-shared-lib') _

// Jenkinsfile becomes simple
buildAndDeploy(
    app: 'myapp',
    environment: params.ENVIRONMENT,
    version: params.VERSION
)

// Complex logic in shared library: vars/buildAndDeploy.groovy
```

## Best Practices Summary

### Do's

1. **Use shared libraries** for complex logic and classes
2. **Use Pipeline steps** for file I/O (readFile, writeFile)
3. **Use @NonCPS** for heavy computation
4. **Parameterize** everything that varies
5. **Add timeouts** to prevent hangs
6. **Batch operations** instead of many small steps
7. **Handle errors** explicitly
8. **Check prerequisites** (plugins, tools)
9. **Document requirements** in comments
10. **Test in lower environments** first

### Don'ts

1. **Don't define classes** in pipeline scripts (use shared libraries)
2. **Don't use direct file I/O** (use Pipeline steps)
3. **Don't store non-serializable** objects in variables
4. **Don't create unlimited parallel** branches
5. **Don't hardcode** values (use parameters)
6. **Don't swallow exceptions** without re-throwing
7. **Don't run heavy computation** on master
8. **Don't use large data** in CPS context
9. **Don't ignore return values**
10. **Don't create massive Jenkinsfiles** (modularize)

### When You Hit a Limitation

1. **Check documentation** - Plugin or Jenkins docs may have solutions
2. **Use shared libraries** - `src/` helps structure reusable code, but restricted APIs still depend on trusted vs untrusted library settings
3. **Script approval** - Admin can whitelist methods
4. **Fallback to shell** - `sh` step is very flexible
5. **Ask for help** - Jenkins community is active
