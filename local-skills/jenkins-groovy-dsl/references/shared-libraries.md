# Jenkins Shared Libraries Guide

Complete guide to creating reusable, maintainable Jenkins shared library code in Groovy.

## Table of Contents

- [Shared Library Structure](#shared-library-structure)
- [Global Variables (vars/)](#global-variables-vars)
- [Source Classes (src/)](#source-classes-src)
- [Resources](#resources)
- [Loading Libraries](#loading-libraries)
- [Best Practices](#best-practices)
- [Advanced Patterns](#advanced-patterns)
- [Testing Shared Libraries](#testing-shared-libraries)

## Shared Library Structure

### Directory Layout

```
my-shared-library/
├── vars/                      # Global variables (DSL methods)
│   ├── buildApp.groovy       # Becomes buildApp() in pipelines
│   ├── deployToK8s.groovy    # Becomes deployToK8s() in pipelines
│   └── notifySlack.groovy    # Becomes notifySlack() in pipelines
├── src/                       # Groovy classes (standard Groovy)
│   └── org/
│       └── company/
│           ├── BuildConfig.groovy
│           ├── DeploymentHelper.groovy
│           └── Utils.groovy
├── resources/                 # Non-Groovy files
│   ├── templates/
│   │   ├── deployment.yaml
│   │   └── Dockerfile.template
│   └── scripts/
│       └── setup.sh
└── README.md                  # Documentation
```

### Three Key Directories

1. **`vars/`** - Global pipeline variables (DSL-style methods available in pipelines)
2. **`src/`** - Regular Groovy classes (runs outside sandbox, full Groovy features)
3. **`resources/`** - Static files (templates, scripts, configs)

## Global Variables (vars/)

### Basic Global Variable

Each `.groovy` file in `vars/` becomes a globally accessible method.

**File: `vars/sayHello.groovy`**
```groovy
// Simple call() method - becomes sayHello() in pipelines
def call(String name = 'World') {
    echo "Hello, ${name}!"
}
```

**Usage in Pipeline:**
```groovy
@Library('my-lib') _

sayHello()           // Output: Hello, World!
sayHello('Jenkins')  // Output: Hello, Jenkins!
```

### Global Variable with Multiple Methods

**File: `vars/docker.groovy`**
```groovy
// call() is the default method
def call(String imageName, String tag = 'latest') {
    build(imageName, tag)
    push(imageName, tag)
}

// Additional methods
def build(String imageName, String tag) {
    echo "Building ${imageName}:${tag}"
    sh "docker build -t ${imageName}:${tag} ."
}

def push(String imageName, String tag) {
    echo "Pushing ${imageName}:${tag}"
    sh "docker push ${imageName}:${tag}"
}

def login(String registry, String credentialsId) {
    withCredentials([usernamePassword(
        credentialsId: credentialsId,
        usernameVariable: 'USER',
        passwordVariable: 'PASS'
    )]) {
        sh "echo \$PASS | docker login -u \$USER --password-stdin ${registry}"
    }
}
```

**Usage:**
```groovy
@Library('my-lib') _

// Call default method
docker('myapp', '1.2.3')

// Or call specific methods
docker.login('registry.example.com', 'docker-creds')
docker.build('myapp', '1.2.3')
docker.push('myapp', '1.2.3')
```

### Pipeline Template (vars/)

**File: `vars/standardPipeline.groovy`**
```groovy
def call(Map config) {
    pipeline {
        agent any

        options {
            timeout(time: config.timeout ?: 60, unit: 'MINUTES')
            timestamps()
            buildDiscarder(logRotator(numToKeepStr: '10'))
        }

        environment {
            APP_NAME = config.appName
            VERSION = config.version ?: '1.0.0'
        }

        stages {
            stage('Checkout') {
                steps {
                    checkout scm
                }
            }

            stage('Build') {
                steps {
                    script {
                        if (config.buildCommand) {
                            sh config.buildCommand
                        } else {
                            sh 'make build'
                        }
                    }
                }
            }

            stage('Test') {
                when {
                    expression { config.runTests != false }
                }
                steps {
                    sh config.testCommand ?: 'make test'
                }
            }

            stage('Deploy') {
                when {
                    expression { config.deploy == true }
                }
                steps {
                    script {
                        deployToK8s(
                            app: config.appName,
                            environment: config.environment,
                            version: config.version
                        )
                    }
                }
            }
        }

        post {
            always {
                cleanWs()
            }
            failure {
                script {
                    if (config.notifyOnFailure) {
                        notifySlack(
                            status: 'FAILURE',
                            channel: config.slackChannel
                        )
                    }
                }
            }
        }
    }
}
```

**Usage:**
```groovy
@Library('my-lib') _

standardPipeline(
    appName: 'myapp',
    version: '1.2.3',
    environment: 'production',
    buildCommand: 'npm run build',
    testCommand: 'npm test',
    deploy: true,
    notifyOnFailure: true,
    slackChannel: '#deployments'
)
```

### Helper Functions (vars/)

**File: `vars/retry.groovy`**
```groovy
def call(int attempts = 3, Closure body) {
    for (int i = 1; i <= attempts; i++) {
        try {
            body()
            return  // Success
        } catch (Exception e) {
            if (i == attempts) {
                throw e  // Last attempt failed
            }
            echo "Attempt ${i} failed, retrying..."
            sleep(time: i, unit: 'SECONDS')
        }
    }
}

def withBackoff(int maxAttempts = 3, Closure body) {
    for (int i = 1; i <= maxAttempts; i++) {
        try {
            return body()
        } catch (Exception e) {
            if (i == maxAttempts) {
                throw e
            }
            def waitTime = Math.pow(2, i - 1) as int
            echo "Attempt ${i} failed, waiting ${waitTime}s..."
            sleep(time: waitTime, unit: 'SECONDS')
        }
    }
}
```

**Usage:**
```groovy
@Library('my-lib') _

retry(5) {
    sh 'flaky-command.sh'
}

retry.withBackoff(4) {
    sh 'api-call.sh'
}
```

## Source Classes (src/)

### Standard Groovy Classes

Code in `src/` runs **outside the sandbox** with full Groovy and Jenkins API access.

**File: `src/org/company/BuildConfig.groovy`**
```groovy
package org.company

class BuildConfig implements Serializable {
    String appName
    String version
    String environment
    int replicas = 3
    Map<String, String> envVars = [:]

    BuildConfig(String app, String ver, String env) {
        this.appName = app
        this.version = ver
        this.environment = env
    }

    def validate() {
        if (!appName) {
            throw new IllegalArgumentException("appName is required")
        }
        if (!version || !version.matches(/\d+\.\d+\.\d+/)) {
            throw new IllegalArgumentException("Invalid version format: ${version}")
        }
        if (!(environment in ['dev', 'staging', 'production'])) {
            throw new IllegalArgumentException("Invalid environment: ${environment}")
        }
        return true
    }

    def getImageTag() {
        return "${appName}:${version}"
    }

    def getNamespace() {
        return "${environment}-${appName}"
    }
}
```

**Usage in Pipeline:**
```groovy
@Library('my-lib') _
import org.company.BuildConfig

def config = new BuildConfig('myapp', '1.2.3', 'production')
config.replicas = 5
config.envVars = [
    DATABASE_URL: 'postgres://db:5432',
    CACHE_ENABLED: 'true'
]

if (config.validate()) {
    echo "Deploying ${config.imageTag} to ${config.namespace}"
}
```

### Utility Classes

**File: `src/org/company/Utils.groovy`**
```groovy
package org.company

class Utils implements Serializable {

    static def parseVersion(String tag) {
        def matcher = (tag =~ /v?(\d+)\.(\d+)\.(\d+)/)
        if (!matcher) {
            throw new IllegalArgumentException("Invalid version: ${tag}")
        }
        return [
            major: matcher[0][1] as int,
            minor: matcher[0][2] as int,
            patch: matcher[0][3] as int,
            full: "${matcher[0][1]}.${matcher[0][2]}.${matcher[0][3]}"
        ]
    }

    static def validateEmail(String email) {
        return email ==~ /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$/
    }

    static def sanitizeBranchName(String branch) {
        return branch
            .toLowerCase()
            .replaceAll(/[^a-z0-9\-]/, '-')
            .replaceAll(/-+/, '-')
            .replaceAll(/^-|-$/, '')
    }

    static def getCurrentTimestamp() {
        return new Date().format('yyyy-MM-dd-HHmmss')
    }

    static def readJsonResource(def steps, String resourcePath) {
        def content = steps.libraryResource(resourcePath)
        return new groovy.json.JsonSlurper().parseText(content)
    }
}
```

**Usage:**
```groovy
@Library('my-lib') _
import org.company.Utils

def version = Utils.parseVersion('v1.2.3')
echo "Major: ${version.major}, Minor: ${version.minor}, Patch: ${version.patch}"

def safeBranch = Utils.sanitizeBranchName('feature/JIRA-123-new-feature')
echo "Safe branch: ${safeBranch}"  // feature-jira-123-new-feature

def timestamp = Utils.getCurrentTimestamp()
echo "Build timestamp: ${timestamp}"
```

### Service Classes

**File: `src/org/company/SlackNotifier.groovy`**
```groovy
package org.company

class SlackNotifier implements Serializable {
    def steps
    String webhookUrl
    String defaultChannel

    SlackNotifier(steps, String webhook, String channel = '#builds') {
        this.steps = steps
        this.webhookUrl = webhook
        this.defaultChannel = channel
    }

    def notify(Map params) {
        def channel = params.channel ?: defaultChannel
        def status = params.status ?: 'UNKNOWN'
        def message = params.message ?: "Build ${status}"

        def color = getColorForStatus(status)
        def emoji = getEmojiForStatus(status)

        def payload = [
            channel: channel,
            text: "${emoji} ${message}",
            attachments: [[
                color: color,
                fields: [
                    [title: 'Job', value: steps.env.JOB_NAME, short: true],
                    [title: 'Build', value: "#${steps.env.BUILD_NUMBER}", short: true],
                    [title: 'Status', value: status, short: true],
                    [title: 'Duration', value: steps.currentBuild.durationString, short: true]
                ]
            ]]
        ]

        steps.httpRequest(
            url: webhookUrl,
            httpMode: 'POST',
            contentType: 'APPLICATION_JSON',
            requestBody: groovy.json.JsonOutput.toJson(payload)
        )
    }

    private def getColorForStatus(String status) {
        switch (status) {
            case 'SUCCESS': return 'good'
            case 'FAILURE': return 'danger'
            case 'UNSTABLE': return 'warning'
            default: return '#808080'
        }
    }

    private def getEmojiForStatus(String status) {
        switch (status) {
            case 'SUCCESS': return ':white_check_mark:'
            case 'FAILURE': return ':x:'
            case 'UNSTABLE': return ':warning:'
            default: return ':question:'
        }
    }
}
```

**Usage:**
```groovy
@Library('my-lib') _
import org.company.SlackNotifier

def slack = new SlackNotifier(this, env.SLACK_WEBHOOK, '#deployments')

pipeline {
    // ...
    post {
        always {
            script {
                slack.notify(
                    status: currentBuild.result ?: 'SUCCESS',
                    message: "Deployment of ${env.APP_NAME} completed"
                )
            }
        }
    }
}
```

## Resources

### Accessing Resource Files

**File: `resources/templates/deployment.yaml`**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{APP_NAME}}
  namespace: {{NAMESPACE}}
spec:
  replicas: {{REPLICAS}}
  template:
    spec:
      containers:
      - name: {{APP_NAME}}
        image: {{IMAGE}}
        env:
        - name: ENVIRONMENT
          value: {{ENVIRONMENT}}
```

**Using in vars/ or src/:**
```groovy
// In vars/deployToK8s.groovy
def call(Map config) {
    // Read template from resources/
    def template = libraryResource('templates/deployment.yaml')

    // Replace placeholders
    def manifest = template
        .replace('{{APP_NAME}}', config.app)
        .replace('{{NAMESPACE}}', config.namespace)
        .replace('{{REPLICAS}}', config.replicas.toString())
        .replace('{{IMAGE}}', config.image)
        .replace('{{ENVIRONMENT}}', config.environment)

    // Write to workspace
    writeFile file: 'deployment.yaml', text: manifest

    // Apply
    sh 'kubectl apply -f deployment.yaml'
}
```

### JSON Configuration Files

**File: `resources/config/environments.json`**
```json
{
  "dev": {
    "region": "us-east-1",
    "instanceType": "t3.small",
    "replicas": 1
  },
  "staging": {
    "region": "us-east-1",
    "instanceType": "t3.medium",
    "replicas": 2
  },
  "production": {
    "region": "us-west-2",
    "instanceType": "t3.large",
    "replicas": 5
  }
}
```

**Using:**
```groovy
// In src/org/company/ConfigLoader.groovy
package org.company

class ConfigLoader {
    static def loadEnvironmentConfig(steps, String environment) {
        def json = steps.libraryResource('config/environments.json')
        def config = new groovy.json.JsonSlurper().parseText(json)
        return config[environment]
    }
}

// Usage
@Library('my-lib') _
import org.company.ConfigLoader

def envConfig = ConfigLoader.loadEnvironmentConfig(this, 'production')
echo "Region: ${envConfig.region}"
echo "Instance Type: ${envConfig.instanceType}"
echo "Replicas: ${envConfig.replicas}"
```

## Loading Libraries

### Dynamic Loading

```groovy
// Load from default branch
@Library('my-lib') _

// Load from specific version
@Library('my-lib@v1.2.3') _

// Load from branch
@Library('my-lib@develop') _

// Load from commit SHA
@Library('my-lib@a1b2c3d4') _

// Load multiple libraries
@Library(['lib1', 'lib2@v1.0', 'lib3@main']) _

// Import specific classes
@Library('my-lib') import org.company.Utils
@Library('my-lib') import org.company.*
```

### Implicit Loading (Global Libraries)

Configure in Jenkins → Manage Jenkins → Configure System → Global Pipeline Libraries

- **Load implicitly**: Library available in all pipelines without `@Library`
- **Allow default version to be overridden**: Pipelines can specify version
- **Include @Library changes in job recent changes**: Show library changes in build

### Runtime Loading

```groovy
// Load library dynamically during pipeline execution
library identifier: 'my-lib@main', retriever: modernSCM([
    $class: 'GitSCMSource',
    remote: 'https://github.com/company/jenkins-lib.git'
])

// Now use library functions
deployApp(app: 'myapp', env: 'production')
```

## Best Practices

### 1. Always Implement Serializable

```groovy
// ✅ CORRECT
class MyClass implements Serializable {
    // All fields should also be serializable
    String name
    int count
    List<String> items
}

// ❌ WRONG
class MyClass {
    // Missing Serializable
}
```

### 2. Pass Pipeline Context to Classes

```groovy
// ✅ CORRECT - pass 'steps' context
class Helper implements Serializable {
    def steps

    Helper(steps) {
        this.steps = steps
    }

    def deploy() {
        steps.sh 'deploy.sh'
        steps.echo 'Deployed!'
    }
}

// Usage
def helper = new Helper(this)
helper.deploy()
```

### 3. Use Static Methods for Utilities

```groovy
// ✅ GOOD - no state, pure functions
class Utils {
    static def parseVersion(String ver) {
        // Logic here
    }

    static def formatDate(Date date) {
        return date.format('yyyy-MM-dd')
    }
}

// Usage - no instantiation needed
def version = Utils.parseVersion('1.2.3')
```

### 4. Validate Input Parameters

```groovy
def call(Map params) {
    // Validate required params
    if (!params.appName) {
        error "Parameter 'appName' is required"
    }

    // Validate types
    if (!(params.replicas instanceof Integer)) {
        error "Parameter 'replicas' must be an integer"
    }

    // Validate values
    if (!(params.environment in ['dev', 'staging', 'production'])) {
        error "Invalid environment: ${params.environment}"
    }

    // Set defaults
    params.timeout = params.timeout ?: 60
    params.retries = params.retries ?: 3

    // Continue with validated params
}
```

### 5. Provide Documentation

```groovy
/**
 * Deploys application to Kubernetes cluster.
 *
 * @param params Map with the following keys:
 *   - app (required): Application name
 *   - environment (required): Target environment (dev/staging/production)
 *   - version (required): Application version
 *   - replicas (optional): Number of replicas (default: 3)
 *   - timeout (optional): Deployment timeout in minutes (default: 10)
 *
 * Example:
 *   deployToK8s(
 *       app: 'myapp',
 *       environment: 'production',
 *       version: '1.2.3',
 *       replicas: 5
 *   )
 */
def call(Map params) {
    // Implementation
}
```

### 6. Handle Errors Gracefully

```groovy
def call(Map params) {
    try {
        validateParams(params)
        deploy(params)
    } catch (IllegalArgumentException e) {
        error "Configuration error: ${e.message}"
    } catch (Exception e) {
        echo "Deployment failed: ${e.message}"
        echo "Stack trace: ${e.printStackTrace()}"
        throw e
    }
}
```

### 7. Use Builders for Complex Configuration

```groovy
class DeploymentBuilder implements Serializable {
    private Map config = [:]

    DeploymentBuilder forApp(String app) {
        config.app = app
        return this
    }

    DeploymentBuilder toEnvironment(String env) {
        config.environment = env
        return this
    }

    DeploymentBuilder withVersion(String version) {
        config.version = version
        return this
    }

    DeploymentBuilder withReplicas(int replicas) {
        config.replicas = replicas
        return this
    }

    Map build() {
        validate()
        return config
    }

    private def validate() {
        if (!config.app) error "App name required"
        if (!config.environment) error "Environment required"
        if (!config.version) error "Version required"
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

## Advanced Patterns

### Factory Pattern

```groovy
package org.company

class DeployerFactory implements Serializable {
    static def createDeployer(steps, String type) {
        switch (type) {
            case 'kubernetes':
                return new KubernetesDeployer(steps)
            case 'aws':
                return new AWSDeployer(steps)
            case 'docker':
                return new DockerDeployer(steps)
            default:
                throw new IllegalArgumentException("Unknown deployer type: ${type}")
        }
    }
}

// Usage
def deployer = DeployerFactory.createDeployer(this, 'kubernetes')
deployer.deploy(app: 'myapp', version: '1.2.3')
```

### Mixin/Trait Pattern

```groovy
trait Loggable {
    def log(String level, String message) {
        def timestamp = new Date().format('yyyy-MM-dd HH:mm:ss')
        echo "[${timestamp}] [${level}] ${message}"
    }

    def info(String message) { log('INFO', message) }
    def warn(String message) { log('WARN', message) }
    def error(String message) { log('ERROR', message) }
}

class Deployer implements Loggable, Serializable {
    def steps

    Deployer(steps) {
        this.steps = steps
    }

    def deploy(Map config) {
        info("Starting deployment of ${config.app}")
        // ...
        info("Deployment successful")
    }
}
```

### Strategy Pattern

```groovy
interface NotificationStrategy {
    def notify(Map params)
}

class SlackNotification implements NotificationStrategy, Serializable {
    def steps
    SlackNotification(steps) { this.steps = steps }

    def notify(Map params) {
        steps.echo "Sending Slack notification to ${params.channel}"
        // Slack logic
    }
}

class EmailNotification implements NotificationStrategy, Serializable {
    def steps
    EmailNotification(steps) { this.steps = steps }

    def notify(Map params) {
        steps.echo "Sending email to ${params.recipients}"
        // Email logic
    }
}

class Notifier implements Serializable {
    def steps
    NotificationStrategy strategy

    Notifier(steps, NotificationStrategy strategy) {
        this.steps = steps
        this.strategy = strategy
    }

    def send(Map params) {
        strategy.notify(params)
    }
}

// Usage
def notifier = new Notifier(this, new SlackNotification(this))
notifier.send(channel: '#builds', message: 'Build complete')
```

## Testing Shared Libraries

### Unit Testing with Spock

**File: `test/groovy/org/company/UtilsSpec.groovy`**
```groovy
package org.company

import spock.lang.Specification

class UtilsSpec extends Specification {

    def "parseVersion should parse valid version string"() {
        when:
        def result = Utils.parseVersion('v1.2.3')

        then:
        result.major == 1
        result.minor == 2
        result.patch == 3
        result.full == '1.2.3'
    }

    def "parseVersion should throw on invalid version"() {
        when:
        Utils.parseVersion('invalid')

        then:
        thrown(IllegalArgumentException)
    }

    def "sanitizeBranchName should convert to lowercase and replace invalid chars"() {
        expect:
        Utils.sanitizeBranchName(input) == output

        where:
        input                           || output
        'feature/JIRA-123'             || 'feature-jira-123'
        'Feature_New_Feature'          || 'feature-new-feature'
        'hotfix/fix@urgent'            || 'hotfix-fix-urgent'
    }
}
```

### Integration Testing

Use Jenkins Pipeline Unit Testing Framework:

```groovy
import com.lesfurets.jenkins.unit.BasePipelineTest

class DeployTest extends BasePipelineTest {

    @Test
    void testDeploy() {
        def script = loadScript("vars/deployToK8s.groovy")
        script.call(
            app: 'testapp',
            environment: 'staging',
            version: '1.0.0'
        )

        assertJobStatusSuccess()
    }
}
```

## Summary

### Key Takeaways

1. **vars/** for DSL-style methods accessible in all pipelines
2. **src/** for full Groovy classes with unrestricted access
3. **resources/** for templates and static files
4. Always implement `Serializable` in classes
5. Pass pipeline context (`this`) to classes that need it
6. Validate inputs and provide clear error messages
7. Document your library functions
8. Version your shared libraries
9. Test your shared library code
10. Use builders and patterns for complex configurations

### Directory Decision Guide

**Use vars/ when:**
- Creating pipeline DSL methods
- Building pipeline templates
- Need direct access to pipeline steps
- Simple helper functions

**Use src/ when:**
- Creating reusable classes
- Complex business logic
- Need full Groovy/Java features
- Utility functions and services

**Use resources/ when:**
- Templates (YAML, Dockerfile, etc.)
- Configuration files (JSON, properties)
- Scripts (shell, Python, etc.)
- Static assets
