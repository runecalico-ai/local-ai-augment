---
name: shellcheck-configuration
description: Use when configuring ShellCheck, addressing linux shell portability issues, and analyzing shell scripts for common pitfalls and best practices.
---

# ShellCheck Configuration and Static Analysis

Comprehensive guidance for configuring and using ShellCheck to improve shell script quality, catch common pitfalls, and enforce best practices through static code analysis.

## When to Use This Skill

- Setting up linting for shell scripts in CI/CD pipelines
- Analyzing existing shell scripts for issues
- Understanding ShellCheck error codes and warnings
- Configuring ShellCheck for specific project requirements
- Integrating ShellCheck into development workflows
- Suppressing false positives and configuring rule sets
- Enforcing consistent code quality standards
- Migrating scripts to meet quality gates

## ShellCheck Fundamentals

### What is ShellCheck?

ShellCheck is a static analysis tool that analyzes shell scripts and detects problematic patterns. It supports:

- Bash, sh, dash, ksh, and other POSIX shells
- Over 100 different warnings and errors
- Configuration for target shell and flags
- Integration with editors and CI/CD systems

### Installation

```bash
# macOS with Homebrew
brew install shellcheck

# Ubuntu/Debian
apt-get install shellcheck

# From source
git clone https://github.com/koalaman/shellcheck.git
cd shellcheck
make build
make install

# Verify installation
shellcheck --version
```

## Configuration Files

### .shellcheckrc (Project Level)

Create `.shellcheckrc` in your project root:

```
# Specify target shell
shell=bash

# Enable optional checks
enable=avoid-nullary-conditions
enable=require-variable-braces

# Disable specific warnings
disable=SC1091
disable=SC2086
```

### Environment Variables

```bash
# Set default shell target
export SHELLCHECK_SHELL=bash

# Enable strict mode
export SHELLCHECK_STRICT=true

# Specify configuration file location
export SHELLCHECK_CONFIG=~/.shellcheckrc
```

## Practical Configuration Examples

### Minimal Configuration (Strict POSIX)

```bash
#!/bin/bash
# Configure for maximum portability

shellcheck \
  --shell=sh \
  --external-sources \
  --check-sourced \
  script.sh
```

### Development Configuration (Bash with Relaxed Rules)

```bash
#!/bin/bash
# Configure for Bash development

shellcheck \
  --shell=bash \
  --exclude=SC1091,SC2034 \
  --enable=all \
  script.sh
```

### CI/CD Integration Configuration

```bash
#!/bin/bash
set -Eeuo pipefail

# Analyze all shell scripts and fail on issues
find . -type f -name "*.sh" | while read -r script; do
    echo "Checking: $script"
    shellcheck \
        --shell=bash \
        --format=gcc \
        --exclude=SC1091 \
        "$script" || exit 1
done
```

### .shellcheckrc for Project

```
# Shell dialect to analyze against
shell=bash

# Enable optional checks
enable=avoid-nullary-conditions,require-variable-braces,check-unassigned-uppercase

# Disable specific warnings
# SC1091: Not following sourced files (many false positives)
disable=SC1091

# SC2034: Variable appears unused in sourced env files
disable=SC2034

# External files to source for context
external-sources=true
```

## Integration Patterns

### Pre-commit Hook Configuration

```bash
#!/bin/bash
# .git/hooks/pre-commit

#!/bin/bash
set -e

# Find all shell scripts changed in this commit
git diff --cached --name-only | grep '\.sh$' | while read -r script; do
    echo "Linting: $script"

    if ! shellcheck "$script"; then
        echo "ShellCheck failed on $script"
        exit 1
    fi
done
```

### GitHub Actions Workflow

```yaml
name: ShellCheck

on: [push, pull_request]

jobs:
  shellcheck:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run ShellCheck
        run: |
          sudo apt-get install shellcheck
          find . -type f -name "*.sh" -exec shellcheck {} \;
```

### GitLab CI Pipeline

```yaml
shellcheck:
  stage: lint
  image: koalaman/shellcheck-alpine
  script:
    - find . -type f -name "*.sh" -exec shellcheck {} \;
  allow_failure: false
```

## Handling ShellCheck Violations

### Suppressing Specific Warnings

```bash
#!/bin/bash

# Disable warning for entire line
# shellcheck disable=SC2086
for file in $(ls -la); do
    echo "$file"
done

# Disable for entire script
# shellcheck disable=SC1091,SC2034

# Disable multiple warnings (format varies)
command_that_fails() {
    # shellcheck disable=SC2015
    [ -f "$1" ] && echo "found" || echo "not found"
}

# Disable specific check for source directive
# shellcheck source=./helper.sh
source helper.sh
```

## Performance Optimization

### Checking Multiple Files

```bash
#!/bin/bash

# Sequential checking
for script in *.sh; do
    shellcheck "$script"
done

# Parallel checking (faster)
find . -name "*.sh" -print0 | \
    xargs -0 -P 4 -n 1 shellcheck
```

### Caching Results

```bash
#!/bin/bash

CACHE_DIR=".shellcheck_cache"
mkdir -p "$CACHE_DIR"

check_script() {
    local script="$1"
    local hash
    local cache_file

    hash=$(sha256sum "$script" | cut -d' ' -f1)
    cache_file="$CACHE_DIR/$hash"

    if [[ ! -f "$cache_file" ]]; then
        if shellcheck "$script" > "$cache_file" 2>&1; then
            touch "$cache_file.ok"
        else
            return 1
        fi
    fi

    [[ -f "$cache_file.ok" ]]
}

find . -name "*.sh" | while read -r script; do
    check_script "$script" || exit 1
done
```

## Output Formats

### Default Format

```bash
shellcheck script.sh

# Output:
# script.sh:1:1: warning: foo appears unused. Verify use (or export if used externally). [SC2034]
```

### GCC Format (for CI/CD)

```bash
shellcheck --format=gcc script.sh

# Output:
# script.sh:1:1: warning: foo appears unused. Verify use (or export if used externally).
```

### JSON Format (for parsing)

```bash
shellcheck --format=json script.sh

# Output:
# [{"file": "script.sh", "line": 1, "column": 1, "level": "warning", "code": 2034, "message": "..."}]
```

### Quiet Format

```bash
shellcheck --format=quiet script.sh

# Returns non-zero if issues found, no output otherwise
```

## Best Practices

1. **Run ShellCheck in CI/CD** - Catch issues before merging
2. **Configure for your target shell** - Don't analyze bash as sh
3. **Document exclusions** - Explain why violations are suppressed
4. **Address violations** - Don't just disable warnings
5. **Enable strict mode** - Use `--enable=all` with careful exclusions
6. **Update regularly** - Keep ShellCheck current for new checks
7. **Use pre-commit hooks** - Catch issues locally before pushing
8. **Integrate with editors** - Get real-time feedback during development

## Error Code References

ShellCheck's official wiki has documentation for every error code. This skill's **[references](references/)** directory provides curated detailed coverage for common issues, parser errors, quoting and array pitfalls, and selected POSIX portability codes, with [references/README.md](references/README.md) serving as the broader lookup index:

### Quick Reference: Common Error Codes

See [references/common-errors.md](references/common-errors.md) for detailed examples of the most frequently encountered errors:

- **SC2086**: Quote to prevent word splitting - Unquoted variables expand incorrectly
- **SC2181**: Check exit code directly - Use `if cmd` not `if [ $? -eq 0 ]`
- **SC2015**: `&&` `||` is not if-then-else - C may run when A is true
- **SC2016**: Single quotes don't expand variables - Use double quotes for `$var`
- **SC1091**: Not following source file - Add shellcheck source directive
- **SC2034**: Variable appears unused - Remove or export unused variables
- **SC2115**: Dangerous wildcard expansion - Use `"${var:?}"` before `rm -rf`
- **SC2164**: cd may fail - Always use `cd dir || exit`
- **SC2155**: Masked return values - Separate declaration and assignment

### Parser Errors (SC1000-1999)

See [references/parser-errors.md](references/parser-errors.md) for syntax and parsing issues:

- **SC1004**: Backslash+linefeed in single quotes - Break outside quotes
- **SC1007**: Space after = in assignment - `var=value` not `var= value`
- **SC1036**: Invalid parenthesis - Quote literals or use `$(cmd)`
- **SC1078**: Unclosed double quote - Check for missing closing quotes
- **SC1083**: Literal braces - Add semicolon or quote braces
- **SC1009**: Unterminated construct - Missing `fi`, `done`, `esac`, etc.

### POSIX Compliance (SC3000-3999)

See [references/posix-compliance.md](references/posix-compliance.md) for portability to `/bin/sh`:

- **SC3001**: Process substitution `<(cmd)` - Use temp files or pipes
- **SC3010**: `[[ ]]` test command - Use `[ ]` or `case` statement
- **SC3043**: `local` keyword - Use naming convention or subshells
- **SC3003**: `$'...'` ANSI-C quoting - Use `printf` for escape sequences
- **SC3020**: `&>` redirection - Use `> file 2>&1`
- **SC3030**: Arrays - Use positional parameters or delimited strings

### Quoting and Arrays (SC2000-2999)

See [references/quoting-arrays.md](references/quoting-arrays.md) for proper variable expansion:

- **SC2048**: Quote `$*` - Use `"$@"` for proper argument passing
- **SC2068**: Quote array expansions - Use `"${array[@]}"`
- **SC2206**: Quote array assignments - Use `mapfile` or `read -a` for splitting
- **SC2046**: Quote command substitution - Use `"$(cmd)"` to prevent splitting

### Using the References

Each reference file includes:
- **Problematic code examples** - What triggers the error
- **Correct code examples** - How to fix it properly
- **Rationale** - Why it's a problem and what can go wrong
- **Real-world scenarios** - Common use cases and solutions
- **Related codes** - Similar or connected issues
- **Best practices** - Recommendations for avoiding the issue

### Looking Up Error Codes

When ShellCheck reports an error:

1. Note the error code (e.g., SC2086)
2. Check the most relevant reference file or index:
  - SC1000-1999 parser issues → [parser-errors.md](references/parser-errors.md)
  - Common SC2000-2999 scripting, quoting, and array issues → [common-errors.md](references/common-errors.md) or [quoting-arrays.md](references/quoting-arrays.md)
  - Selected SC3000-3999 POSIX portability issues → [posix-compliance.md](references/posix-compliance.md)
  - Broader lookup across the codes covered here → [references/README.md](references/README.md)
  - For any code not documented in this skill, use https://www.shellcheck.net/wiki/SC2086
3. Read the problematic and correct code examples
4. Apply the fix to your script
5. Run ShellCheck again to verify

### Online Resources

For error codes not covered in the references:

- **ShellCheck Wiki**: https://www.shellcheck.net/wiki/SC#### (replace #### with error number)
- **ShellCheck GitHub**: https://github.com/koalaman/shellcheck
- **Full Error List**: https://www.shellcheck.net/wiki/ (sitemap with all codes)

## Resources

- **ShellCheck GitHub**: https://github.com/koalaman/shellcheck
- **ShellCheck Wiki**: https://www.shellcheck.net/wiki/
- **Error Code Reference**: https://www.shellcheck.net/
- **Skill References**: See `references/` directory for detailed error documentation
