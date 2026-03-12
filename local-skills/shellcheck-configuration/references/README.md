# ShellCheck Error Code Reference Index

This directory contains comprehensive documentation for ShellCheck error codes with detailed examples of problematic code, correct solutions, and rationale.

## Reference Files

### [common-errors.md](common-errors.md)
**Most frequently encountered ShellCheck errors**

Covers the top errors you'll see in real-world scripts:
- SC2086: Quote to prevent word splitting
- SC2181: Check exit code directly
- SC2015: && || is not if-then-else
- SC2016: Single quotes don't expand
- SC1091: Not following source files
- SC2034: Variable appears unused
- SC2115: Dangerous wildcard expansion
- SC2164: cd may fail
- SC2155: Masked return values

**Best for:** Beginners learning shell scripting, fixing the most common issues

---

### [parser-errors.md](parser-errors.md)
**Syntax and parsing errors (SC1000-1999)**

Covers syntax issues that prevent script parsing:
- SC1004: Backslash+linefeed in single quotes
- SC1007: Space after = in assignment
- SC1036: Invalid parenthesis placement
- SC1078: Unclosed double quotes
- SC1083: Literal braces needing semicolons
- SC1009: Unterminated constructs (if/for/while)

**Best for:** Debugging syntax errors, understanding shell grammar

---

### [posix-compliance.md](posix-compliance.md)
**POSIX portability issues (SC3000-3999)**

Covers bash-specific features that don't work in POSIX sh:
- SC3001: Process substitution <(cmd)
- SC3010: [[ ]] test command
- SC3043: local keyword
- SC3003: $'...' ANSI-C quoting
- SC3020: &> redirection shortcut
- SC3030: Arrays

**Best for:** Writing portable scripts, targeting /bin/sh or multiple shells

---

### [quoting-arrays.md](quoting-arrays.md)
**Quoting, word splitting, and array handling**

Covers proper quoting to avoid bugs:
- SC2048: Quote $* (use "$@")
- SC2068: Quote array expansions
- SC2206: Quote array assignments
- SC2046: Quote command substitution
- Plus comprehensive quoting best practices and array patterns

**Best for:** Understanding quoting rules, working with arrays safely

---

## Quick Lookup by Error Code

### SC1000-1999 (Parser Errors)
| Code | Description | File |
|------|-------------|------|
| SC1004 | Backslash+linefeed in single quotes | parser-errors.md |
| SC1007 | Space after = in assignment | parser-errors.md |
| SC1036 | Invalid parenthesis | parser-errors.md |
| SC1078 | Unclosed double quote | parser-errors.md |
| SC1083 | Literal braces | parser-errors.md |
| SC1009 | Unterminated construct | parser-errors.md |
| SC1091 | Not following source | common-errors.md |

### SC2000-2999 (Common Issues)
| Code | Description | File |
|------|-------------|------|
| SC2015 | && \|\| is not if-then-else | common-errors.md |
| SC2016 | Single quotes don't expand | common-errors.md |
| SC2034 | Variable appears unused | common-errors.md |
| SC2046 | Quote command substitution | quoting-arrays.md |
| SC2048 | Quote $* | quoting-arrays.md |
| SC2068 | Quote array expansions | quoting-arrays.md |
| SC2086 | Quote to prevent word splitting | common-errors.md |
| SC2115 | Dangerous wildcard expansion | common-errors.md |
| SC2155 | Masked return values | common-errors.md |
| SC2164 | cd may fail | common-errors.md |
| SC2181 | Check exit code directly | common-errors.md |
| SC2206 | Quote array assignments | quoting-arrays.md |

### SC3000-3999 (POSIX Compliance)
| Code | Description | File |
|------|-------------|------|
| SC3001 | Process substitution <(cmd) | posix-compliance.md |
| SC3003 | $'...' ANSI-C quoting | posix-compliance.md |
| SC3010 | [[ ]] test command | posix-compliance.md |
| SC3020 | &> redirection | posix-compliance.md |
| SC3030 | Arrays | posix-compliance.md |
| SC3043 | local keyword | posix-compliance.md |

---

## How to Use These References

### When You See a ShellCheck Error

1. **Note the error code** (e.g., "SC2086")
2. **Find the reference file:**
   - SC1000-1999 → parser-errors.md
   - SC2000-2999 → common-errors.md or quoting-arrays.md
   - SC3000-3999 → posix-compliance.md
3. **Read the section** for that error code
4. **Compare** problematic vs correct code examples
5. **Understand the rationale** for why it's an issue
6. **Apply the fix** to your script
7. **Re-run ShellCheck** to verify

### Learning Path

**Beginner:** Start with common-errors.md
- Learn the most important errors first
- Focus on SC2086, SC2181, SC2016
- Practice quoting variables and checking exit codes

**Intermediate:** Add quoting-arrays.md
- Master proper quoting patterns
- Learn array handling
- Understand word splitting and globbing

**Advanced:** Study posix-compliance.md and parser-errors.md
- Write portable POSIX scripts
- Debug complex syntax issues
- Understand shell grammar deeply

### Quick Reference Card

```bash
# Top 5 Most Common Fixes

# 1. Quote variables (SC2086)
echo "$var"              # not: echo $var

# 2. Check exit codes directly (SC2181)
if command; then         # not: command; if [ $? -eq 0 ]; then

# 3. Use if-then-else (SC2015)
if [ test ]; then        # not: [ test ] && action || other
    action
else
    other
fi

# 4. Quote array expansions (SC2068)
process "$@"             # not: process $@
process "${array[@]}"    # not: process ${array[@]}

# 5. Handle cd failures (SC2164)
cd dir || exit           # not: cd dir
```

---

## Additional Resources

### Online References
- **ShellCheck Wiki**: https://www.shellcheck.net/wiki/
- **Error Code Lookup**: https://www.shellcheck.net/wiki/SC#### (replace #### with code)
- **ShellCheck GitHub**: https://github.com/koalaman/shellcheck

### Shell Scripting Resources
- **Bash Manual**: https://www.gnu.org/software/bash/manual/
- **POSIX Shell Spec**: https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html
- **BashFAQ**: https://mywiki.wooledge.org/BashFAQ
- **Bash Pitfalls**: https://mywiki.wooledge.org/BashPitfalls

### Testing Your Scripts
```bash
# Run ShellCheck on a script
shellcheck script.sh

# Check all shell scripts in directory
find . -name "*.sh" -exec shellcheck {} \;

# With specific shell (for POSIX compliance)
shellcheck --shell=sh script.sh

# Enable all optional checks
shellcheck --enable=all script.sh

# Exclude specific warnings
shellcheck --exclude=SC2086,SC2181 script.sh
```

---

## Contributing

Found an error in the documentation or have a suggestion? The error code examples are based on the official ShellCheck wiki at https://www.shellcheck.net/wiki/.

For questions about ShellCheck itself, visit the GitHub repository:
https://github.com/koalaman/shellcheck

---

## Document Information

**Last Updated:** January 2026
**ShellCheck Version:** Compatible with v0.7.0+
**Coverage:** ~50 most common error codes with detailed examples
**Source:** https://www.shellcheck.net/wiki/

Each reference file includes:
- Problematic code examples (what triggers the error)
- Correct code examples (how to fix it)
- Rationale (why it's a problem)
- Real-world scenarios and use cases
- Related error codes
- Best practices and recommendations
