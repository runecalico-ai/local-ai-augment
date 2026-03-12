# Script to append remaining POSIX compliance error codes

$filePath = "c:\Users\1027586\.copilot\skills\shellcheck-configuration\references\posix-compliance.md"

$content = @'

## SC3014

**Message:** In POSIX sh, == in place of = is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# Using C-style equality
if [ "$1" == "-n" ]; then
    dry_run=1
fi

# In test command
test "$var" == "value" && echo "match"
```

### Correct Code

```bash
#!/bin/sh
# POSIX single equals
if [ "$1" = "-n" ]; then
    dry_run=1
fi

# Single = in test
test "$var" = "value" && echo "match"
```

### Rationale

`==` for equality is a C-language convention supported by Bash/ksh but not POSIX sh or dash. Always use single `=` for string comparison in `[` `]` and `test` commands for portability.

### Examples

```bash
# ❌ Bad - Double equals (Bash-specific)
[ "$OS" == "Linux" ]
[ "$count" == "0" ]

# ✅ Good - Single equals (POSIX)
[ "$OS" = "Linux" ]
[ "$count" = "0" ]
```

### Exceptions

In `[[` `]]` (Bash), both `=` and `==` work, but `[[` `]]` itself isn't POSIX. For POSIX compliance, use `[` `]` with single `=`.

### Related Codes

- [SC3010](#sc3010) - `[[ ]]` not in POSIX
- [SC2007](common-errors.md) - Use `$((..))` for arithmetic

---

## SC3037

**Message:** In POSIX sh, echo flags are undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# echo with flags is not portable
echo -n "Enter name: "
echo -e "Line1\nLine2"
echo -ne "Tab:\tBar"
```

### Correct Code

```bash
#!/bin/sh
# Use printf - it's standardized and portable
printf '%s' "Enter name: "
printf '%s\n' "Line1" "Line2"
printf 'Tab:\tBar'
```

### Rationale

`echo` behavior varies across systems - some support `-n`, `-e`, some don't, and some interpret backslashes by default. `printf` has standardized, consistent behavior across all POSIX shells.

### Examples

```bash
# ❌ Bad - Non-portable echo usage
echo -n "Loading..."
echo -e "Red:\033[31m"
echo -ne "Progress: $percent%\r"

# ✅ Good - Portable printf
printf '%s' "Loading..."
printf 'Red:\033[31m\n'
printf 'Progress: %s%%\r' "$percent"
```

### Exceptions

Plain `echo` without flags is generally portable (though backslash handling varies). For maximum portability, always use `printf`.

### Related Codes

- [SC2028](common-errors.md) - echo doesn't interpret escapes, use printf
- [SC3143] - echo with command substitution

---

## SC3044

**Message:** In POSIX sh, declare is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# Bash-specific commands not in POSIX
declare var="value"
declare -r READONLY="constant"
declare -a array
typeset count=0
let result=5+3
```

### Correct Code

```bash
#!/bin/sh
# Plain assignment (POSIX)
var="value"

# Read-only variable
READONLY="constant"
readonly READONLY

# Arrays not in POSIX - use positional params
set -- item1 item2 item3

# Arithmetic with expr or $(( ))
result=$((5 + 3))
```

### Rationale

Commands like `declare`, `typeset`, `let`, `local` (in global scope), `pushd`, `popd`, `shopt`, `mapfile`, and others are Bash/ksh extensions. POSIX sh doesn't support them. Use standard variable assignment and arithmetic expansion instead.

### Examples

```bash
# ❌ Bad - Bash-specific built-ins
declare -i number=42
let counter++
typeset -l lowercase="HELLO"
mapfile -t lines < file.txt

# ✅ Good - POSIX alternatives
number=42
counter=$((counter + 1))
lowercase=$(echo "HELLO" | tr '[:upper:]' '[:lower:]')
while IFS= read -r line; do lines="$lines$line "; done < file.txt
```

### Exceptions

If your script is gated on `$BASH_VERSION` checks, you can ignore this warning.

### Related Codes

- [SC3043](#sc3043) - `local` outside functions
- [SC3045](#sc3045) - Built-in command flags

---

## SC3045

**Message:** In POSIX sh, some-command-with-flag is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# Bash-specific flags for built-in commands
read -e -p "Name: " username   # libreadline editing
export -f myfunction            # Export functions
ulimit -v 1000000               # Virtual memory limit
wait -n                         # Wait for next job
printf -v var "format"          # Assign to variable
```

### Correct Code

```bash
#!/bin/sh
# POSIX alternatives
printf 'Name: '; read -r username
# Functions can't be exported in POSIX sh
ulimit -m 1000000               # Use portable flags
wait                            # Wait for all jobs
var=$(printf "format")          # Command substitution
```

### Rationale

Built-in commands like `read`, `export`, `ulimit`, `wait`, and `printf` accept different flags depending on the shell. Flags that work in Bash may not exist in dash/sh. External commands (`grep`, `sed`) are consistent across shells.

### Examples

```bash
# ❌ Bad - Bash-specific built-in flags
read -e -i "default" var
export -n VARNAME
ulimit -v 500000
printf -v output '%s\n' "$var"

# ✅ Good - POSIX-compatible usage
read -r var
export VARNAME
ulimit -d 500000  # Or omit unsupported limits
output=$(printf '%s\n' "$var")
```

### Exceptions

If code is gated on shell version checks, ignore this warning.

### Related Codes

- [SC3044](#sc3044) - Bash-specific commands
- [SC2162](common-errors.md#sc2162) - read without -r

---

## SC3046

**Message:** In POSIX sh, source in place of . is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# Bash-specific source command
source mylib.sh
source ./functions.sh
source ~/.profile
```

### Correct Code

```bash
#!/bin/sh
# POSIX dot command
. mylib.sh
. ./functions.sh
. ~/.profile
```

### Rationale

`source` is a Bash/ksh alias for the POSIX `.` (dot) command. They're functionally identical, but only `.` is guaranteed to work in all POSIX shells. The dot command sources/executes a file in the current shell context.

### Examples

```bash
# ❌ Bad - Bash-specific source
source config.sh
source "file with spaces.sh"

# ✅ Good - POSIX dot command
. config.sh
. "file with spaces.sh"
```

### Exceptions

If targeting only Bash/ksh, `source` is clearer and more searchable than `.`.

### Related Codes

- [SC1091](#sc1091) - File not specified as input

---

## SC3054

**Message:** In POSIX sh, array references are undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# Arrays not in POSIX
var=(foo bar baz)
echo "${var[1]}"
echo "${#var[@]}"
for item in "${var[@]}"; do
    echo "$item"
done
```

### Correct Code

```bash
#!/bin/sh
# Use positional parameters
set -- foo bar baz
echo "$2"
echo "$#"
for item in "$@"; do
    echo "$item"
done

# Or space-separated string
var="foo bar baz"
for item in $var; do  # Note: breaks on spaces in items
    echo "$item"
done
```

### Rationale

Arrays (indexed and associative) are Bash/ksh features not in POSIX sh. Positional parameters (`$1`, `$2`, etc., accessible via `$@`) are the POSIX alternative for simple lists. Complex data structures require workarounds or switching to Bash.

### Examples

```bash
# ❌ Bad - Array syntax
files=(*.txt)
echo "${files[0]}"
paths=(/usr/bin /usr/local/bin)

# ✅ Good - POSIX alternatives
set -- *.txt
echo "$1"
# For paths with spaces, use separate variables or delimited string
path1="/usr/bin"
path2="/usr/local/bin"
```

### Exceptions

For complex data structures, consider switching to `#!/bin/bash` or using external tools (awk, Python).

### Related Codes

- [SC2068](quoting-arrays.md#sc2068) - Unquoted `$@`
- [SC2048](quoting-arrays.md#sc2048) - Unquoted `$*`

---

## SC3060

**Message:** In POSIX sh, string replacement is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# Parameter expansion string replacement
echo "${var//foo/bar}"
echo "${filename%.txt}.md"
echo "${path##*/}"
```

### Correct Code

```bash
#!/bin/sh
# Use sed for substitution
echo "$var" | sed 's/foo/bar/g'

# Use external tools for path manipulation
basename "$path"
dirname "$path"

# For simple prefix/suffix removal, sometimes case/expr works
# But often sed/awk is cleaner
echo "$filename" | sed 's/\.txt$/.md/'
```

### Rationale

Advanced parameter expansion (`${var//pattern/replacement}`, `${var#pattern}`, `${var%pattern}`) is a Bash/ksh feature. POSIX sh only supports basic expansion. Use `sed`, `awk`, `basename`, `dirname`, or `expr` for string manipulation.

### Examples

```bash
# ❌ Bad - Bash parameter expansion
url="${url//http:/https:}"
name="${fullname%% *}"
extension="${filename##*.}"

# ✅ Good - POSIX alternatives
url=$(echo "$url" | sed 's|http:|https:|g')
name=$(echo "$fullname" | sed 's/ .*//')
extension=$(echo "$filename" | sed 's/.*\.//')
# Or: extension=$(basename "$filename" | sed 's/^.*\.//')
```

### Exceptions

Basic expansion `${var}`, `${var:-default}`, `${var:=default}` are POSIX-compliant.

### Related Codes

- [SC3003](#sc3003) - `${var/pattern/string}` not POSIX
- [SC2295] - Expansions in single quotes

---

## Quick Reference: All POSIX Compliance Error Codes

### Syntax and Operators (SC3000-3019)

| Code | Message | Severity |
|------|---------|----------|
| SC3001 | In POSIX sh, `&>` redirection is undefined | Warning |
| SC3002 | In POSIX sh, `\o` in `$".."` is not special | Warning |
| SC3003 | In POSIX sh, `${var/pattern/string}` is undefined | Warning |
| SC3004 | In POSIX sh, `${#var[@]}` is undefined | Warning |
| SC3005 | In POSIX sh, `${!var[@]}` is undefined | Warning |
| SC3006 | In POSIX sh, `[[ ]]` is undefined | Warning |
| SC3007 | In POSIX sh, `<&` redirection is undefined | Warning |
| SC3008 | In POSIX sh, `|&` is undefined | Warning |
| SC3009 | In POSIX sh, `;&` in case is undefined | Warning |
| SC3010 | In POSIX sh, `[[ ]]` is undefined | Warning |
| SC3011 | In POSIX sh, here-strings (`<<<`) are undefined | Warning |
| SC3012 | In POSIX sh, `\x` in `$".."` is not special | Warning |
| SC3013 | In POSIX sh, `$".."` is undefined | Warning |
| SC3014 | In POSIX sh, `==` in place of `=` is undefined | Warning |
| SC3015 | In POSIX sh, `=~` is undefined | Warning |
| SC3016 | In POSIX sh, process substitution (`<()`) is undefined | Warning |
| SC3017 | In POSIX sh, `${array[x]:y:z}` is undefined | Warning |
| SC3018 | In POSIX sh, arithmetic `for` loops are undefined | Warning |
| SC3019 | In POSIX sh, `${array:offset:len}` is undefined | Warning |

### Commands and Built-ins (SC3020-3049)

| Code | Message | Severity |
|------|---------|----------|
| SC3020 | In POSIX sh, `local` is undefined | Warning |
| SC3021 | In POSIX sh, `+=` is undefined | Warning |
| SC3022 | In POSIX sh, `[[ -v ]]` is undefined | Warning |
| SC3023 | In POSIX sh, `[[ -z ]]` (regex) is undefined | Warning |
| SC3024 | In POSIX sh, `-o pipefail` is undefined | Warning |
| SC3025 | In POSIX sh, `set -o` long options are undefined | Warning |
| SC3026 | In POSIX sh, `-ot` is undefined | Warning |
| SC3027 | In POSIX sh, `\$'"..."'` is undefined | Warning |
| SC3028 | In POSIX sh, `BASH_*` variables are undefined | Warning |
| SC3029 | In POSIX sh, `!` negation outside `[[` is undefined | Warning |
| SC3030 | In POSIX sh, `function` keyword is undefined | Warning |
| SC3031 | In POSIX sh, `>&2` with command is undefined | Warning |
| SC3032 | In POSIX sh, `{1..10}` brace expansion is undefined | Warning |
| SC3033 | In POSIX sh, `{a,b}` brace expansion is undefined | Warning |
| SC3034 | In POSIX sh, non-decimal integer literals are undefined | Warning |
| SC3035 | In POSIX sh, `$RANDOM` is undefined | Warning |
| SC3036 | In POSIX sh, nameref / `declare -n` is undefined | Warning |
| SC3037 | In POSIX sh, echo flags (`-n`, `-e`) are undefined | Warning |
| SC3038 | In POSIX sh, `printf -v` is undefined | Warning |
| SC3039 | In POSIX sh, `(( ))` is undefined | Warning |
| SC3040 | In POSIX sh, `$((x++))` is undefined | Warning |
| SC3041 | In POSIX sh, `${!var}` is undefined | Warning |
| SC3042 | In POSIX sh, `echo "$((x))"` may differ | Warning |
| SC3043 | In POSIX sh, `local` is undefined | Warning |
| SC3044 | In POSIX sh, `declare/typeset/let` are undefined | Warning |
| SC3045 | In POSIX sh, built-in command flags may differ | Warning |
| SC3046 | In POSIX sh, `source` in place of `.` is undefined | Warning |

### Arrays and Advanced Features (SC3050-3099)

| Code | Message | Severity |
|------|---------|----------|
| SC3050 | In POSIX sh, `${var:+x}` is undefined | Info |
| SC3051 | In POSIX sh, `${!prefix@}` is undefined | Warning |
| SC3052 | In POSIX sh, `((..))` is undefined | Warning |
| SC3053 | In POSIX sh, `[[ .. ]]` is undefined | Warning |
| SC3054 | In POSIX sh, array references are undefined | Warning |
| SC3055 | In POSIX sh, indirect expansion (`${!var}`) is undefined | Warning |
| SC3056 | In POSIX sh, `nameref` is undefined | Warning |
| SC3057 | In POSIX sh, `!` in parameter expansion is undefined | Warning |
| SC3058 | In POSIX sh, `^` in parameter expansion is undefined | Warning |
| SC3059 | In POSIX sh, `,` in parameter expansion is undefined | Warning |
| SC3060 | In POSIX sh, string replacement (`${v//p/s}`) is undefined | Warning |
| SC3061 | In POSIX sh, `@@` modifier is undefined | Warning |

---

## Best Practices for POSIX Compliance

1. **Use correct shebang** - `#!/bin/sh` for POSIX, `#!/bin/bash` for bash
2. **Test with dash** - Debian's /bin/sh, strict POSIX
3. **Avoid bashisms** - No `[[`, `local`, `$'...'`, `&>`, etc.
4. **Use shellcheck** - Catches POSIX violations
5. **Document requirements** - State what shells are supported
6. **Consider tradeoffs** - POSIX portability vs code readability
7. **Use `# shellcheck disable=SC3000-SC4000`** - If targeting bash only
8. **Prefer `printf` over `echo`** - Consistent behavior across shells
9. **Use `.` instead of `source`** - POSIX compatibility
10. **Test with dash/sh** - Verify portability before deployment
11. **Use single `=` in tests** - Avoid `==` for compatibility
12. **Avoid Bash arrays** - Use positional params or external tools
13. **Quote variables** - Prevents word splitting issues
14. **Use `$((..))` for arithmetic** - Avoid `let` and `expr` when possible
'@

Add-Content -Path $filePath -Value $content
Write-Host "Successfully appended POSIX compliance error codes to posix-compliance.md" -ForegroundColor Green
