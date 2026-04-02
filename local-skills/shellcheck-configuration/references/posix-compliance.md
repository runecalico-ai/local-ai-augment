# ShellCheck POSIX Compliance Reference

This reference documents common POSIX compatibility issues (SC3000-3999 range) for shell scripts targeting `/bin/sh` or maximum portability.

## Table of Contents

- [SC3001: Process substitution](#sc3001)
- [SC3010: [[ ]] test command](#sc3010)
- [SC3043: local keyword](#sc3043)
- [SC3003: $'...' syntax](#sc3003)
- [SC3020: &> redirection](#sc3020)
- [SC3030: Arrays](#sc3030)
- [SC3011: Here-strings](#sc3011)
- [SC3014: == in test expressions](#sc3014)
- [SC3037: echo flags](#sc3037)
- [SC3044: declare / typeset / let](#sc3044)
- [SC3045: Built-in command flags](#sc3045)
- [SC3046: source vs .](#sc3046)
- [SC3054: Array references](#sc3054)
- [SC3060: String replacement](#sc3060)

---

## Overview

POSIX sh is the standard shell specification. These codes help ensure scripts work across different shells (sh, dash, ash, ksh, bash) by avoiding bash-specific features.

### When to Care About POSIX

- Scripts with `#!/bin/sh` shebang
- Targeting multiple Unix systems
- Embedded systems (BusyBox, Alpine Linux)
- Debian/Ubuntu (where /bin/sh is dash)
- Maximum portability required

### When You Can Ignore

- Script explicitly uses `#!/bin/bash` or `#!/bin/ksh`
- Only runs on systems where sh=bash
- Already using bash-specific features
- Add `# shellcheck disable=SC3000-SC4000` to disable all

---

## SC3001

**Message:** In POSIX sh, process substitution is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh

# Process substitution <(cmd)
while IFS= read -r line; do
    echo "$line"
done < <(generate_data)

# Multiple process substitutions
diff <(sort file1) <(sort file2)

# As command argument
program --input <(preprocess data.txt)
```

### Correct Code

**Option 1: Change shebang to bash**

```bash
#!/bin/bash

# Now process substitution is supported
while IFS= read -r line; do
    echo "$line"
done < <(generate_data)
```

**Option 2: Use temporary files**

```bash
#!/bin/sh

# Create temporary file
tmp="$(mktemp)"
generate_data > "$tmp"

while IFS= read -r line; do
    echo "$line"
done < "$tmp"

rm "$tmp"
```

**Option 3: Use pipes when possible**

```bash
#!/bin/sh

# If command reads from stdin, use pipe
generate_data | while IFS= read -r line; do
    echo "$line"
done
```

**Option 4: Named pipes for streaming**

```bash
#!/bin/sh

# Create named pipe
fifo="$(mktemp -u)"
mkfifo "$fifo"

# Producer in background
generate_data > "$fifo" &

# Consumer
while IFS= read -r line; do
    echo "$line"
done < "$fifo"

rm "$fifo"
```

### Rationale

Process substitution `<(cmd)` and `>(cmd)` are bash/ksh extensions. They create temporary files and file descriptors that look like filenames.

POSIX sh (including dash, ash) does not support this syntax.

### Common Use Cases and Alternatives

```bash
# Bash: Compare command outputs
diff <(cmd1) <(cmd2)

# POSIX: Use temp files
tmp1=$(mktemp) tmp2=$(mktemp)
cmd1 > "$tmp1"
cmd2 > "$tmp2"
diff "$tmp1" "$tmp2"
rm "$tmp1" "$tmp2"

# ----

# Bash: Multiple inputs
program <(input1) <(input2)

# POSIX: Use pipes or temp files
input1 > tmp1
input2 > tmp2
program tmp1 tmp2
rm tmp1 tmp2

# ----

# Bash: While reading command output
while read line; do
    echo "$line"
done < <(find . -name "*.txt")

# POSIX: Use pipe (but creates subshell)
find . -name "*.txt" | while read -r line; do
    echo "$line"
done

# POSIX: Or temp file (preserves variables)
find . -name "*.txt" > tmp
while read -r line; do
    echo "$line"
done < tmp
rm tmp
```

### Caveat: Pipes Create Subshells

```bash
# Problem: Variables set in loop are lost
total=0
find . -type f | while read -r file; do
    total=$((total + 1))
done
echo "$total"  # Still 0! (subshell)

# POSIX solution: Use temp file
total=0
find . -type f > tmp
while read -r file; do
    total=$((total + 1))
done < tmp
echo "$total"  # Correct count
rm tmp
```

---

## SC3010

**Message:** In POSIX sh, `[[ ]]` is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh

# Double bracket test
if [[ -f "$file" ]]; then
    cat "$file"
fi

# Pattern matching
if [[ "$str" == pattern* ]]; then
    echo "Match"
fi

# Regex matching
if [[ "$email" =~ ^[a-z]+@[a-z]+\.[a-z]+$ ]]; then
    echo "Valid email"
fi

# Logical operators
if [[ -f "$file" && -r "$file" ]]; then
    echo "File exists and is readable"
fi
```

### Correct Code

**Use `[ ]` (test command) instead**

```bash
#!/bin/sh

# Single bracket test
if [ -f "$file" ]; then
    cat "$file"
fi

# Pattern matching with case
case "$str" in
    pattern*) echo "Match" ;;
esac

# Regex matching with grep/expr
if echo "$email" | grep -Eq '^[a-z]+@[a-z]+\.[a-z]+$'; then
    echo "Valid email"
fi

# Logical operators - use separate tests
if [ -f "$file" ] && [ -r "$file" ]; then
    echo "File exists and is readable"
fi
```

### Rationale

`[[ ]]` is a bash/ksh keyword with enhanced features:
- Pattern matching with `==`
- Regex matching with `=~`
- Logical operators `&&` and `||`
- No word splitting or globbing

POSIX sh only has `[ ]` (test command) and `test`.

### Differences Between `[ ]` and `[[ ]]`

```bash
# Feature comparison
# | Feature              | [ ]        | [[ ]]      |
# |----------------------|------------|------------|
# | POSIX                | Yes        | No         |
# | Word splitting       | Yes        | No         |
# | Glob expansion       | Yes        | No         |
# | Pattern matching     | No         | Yes        |
# | Regex matching       | No         | Yes (=~)   |
# | && and || operators  | No         | Yes        |
# | -a and -o operators  | Yes (deprecated) | No   |

# Bash [[ ]]
[[ $var == pattern* ]]              # Pattern match
[[ $var =~ regex ]]                 # Regex match
[[ -f $file && -r $file ]]          # Logical AND
[[ $a > $b ]]                       # String comparison (safe)

# POSIX [ ]
case $var in pattern*) true;; esac  # Pattern match
echo "$var" | grep -q "regex"       # Regex match
[ -f "$file" ] && [ -r "$file" ]    # Logical AND
[ "$a" \> "$b" ]                    # String comparison (escaped)
```

### Pattern Matching Alternatives

```bash
# Bash [[
if [[ "$filename" == *.txt ]]; then
    echo "Text file"
fi

# POSIX case
case "$filename" in
    *.txt) echo "Text file" ;;
esac

# ----

# Bash [[
if [[ "$str" != prefix* ]]; then
    echo "Doesn't start with prefix"
fi

# POSIX case
case "$str" in
    prefix*) ;;
    *) echo "Doesn't start with prefix" ;;
esac
```

### Regex Matching Alternatives

```bash
# Bash [[
if [[ "$email" =~ ^[a-z]+@[a-z]+\.[a-z]+$ ]]; then
    echo "Valid email"
fi

# POSIX grep
if echo "$email" | grep -Eq '^[a-z]+@[a-z]+\.[a-z]+$'; then
    echo "Valid email"
fi

# POSIX expr (basic regex)
if expr "$email" : '[a-z]*@[a-z]*\.[a-z]*$' >/dev/null; then
    echo "Valid email"
fi
```

### Logical Operators

```bash
# Bash [[
if [[ -f "$file" && -r "$file" ]]; then
    echo "Exists and readable"
fi

# POSIX - separate tests
if [ -f "$file" ] && [ -r "$file" ]; then
    echo "Exists and readable"
fi

# POSIX - nested if
if [ -f "$file" ]; then
    if [ -r "$file" ]; then
        echo "Exists and readable"
    fi
fi

# AVOID deprecated -a operator
# [ -f "$file" -a -r "$file" ]  # Deprecated in POSIX
```

### Quoting Differences

```bash
# [[ ]] doesn't do word splitting (bash)
var="file with spaces.txt"
[[ -f $var ]]              # Works (no quotes needed)

# [ ] does word splitting (POSIX)
var="file with spaces.txt"
[ -f $var ]                # FAILS - sees multiple arguments
[ -f "$var" ]              # Works - must quote
```

---

## SC3043

**Message:** In POSIX sh, `local` is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh

myfunc() {
    local i=0
    local temp
    temp=$(date)
    echo "$temp"
}

# Local with type modifiers
process() {
    local -r CONST=42
    local -a array
}
```

### Correct Code

**Option 1: Use naming convention**

```bash
#!/bin/sh

myfunc() {
    # Prefix with function name to avoid conflicts
    _myfunc_i=0
    _myfunc_temp=$(date)
    echo "$_myfunc_temp"
}
```

**Option 2: Use subshell**

```bash
#!/bin/sh

myfunc() (  # Note: ( not { means subshell
    # Variables are local to subshell
    i=0
    temp=$(date)
    echo "$temp"
)  # Subshell ends, variables disappear
```

**Option 3: Switch to bash**

```bash
#!/bin/bash

myfunc() {
    local i=0
    local temp
    temp=$(date)
    echo "$temp"
}
```

### Rationale

`local` is widely supported (bash, ksh, dash, BusyBox ash) but **not in POSIX**. The POSIX spec doesn't define it.

For maximum portability to exotic or old systems, avoid `local`.

### Naming Convention Strategies

```bash
# Strategy 1: Function name prefix
calculate_total() {
    _calculate_total_sum=0
    _calculate_total_count=0
    # ...
}

# Strategy 2: Double underscore prefix
calculate_total() {
    __sum=0
    __count=0
    # ...
}

# Strategy 3: Single underscore (for private)
calculate_total() {
    _sum=0
    _count=0
    # ...
}
```

### Subshell Approach

```bash
# Function as subshell (note parentheses)
calculate() (
    # All variables are local to subshell
    sum=0
    for num in "$@"; do
        sum=$((sum + num))
    done
    echo "$sum"
)

result=$(calculate 1 2 3 4 5)

# Limitations:
# - Can't modify parent shell variables
# - Slightly slower (creates new process)
# - Can't use return to set exit code
# - Output must be captured or piped
```

### When To Use Each Approach

```bash
# Use local (if bash/ksh/dash are guaranteed)
myfunc() {
    local temp=$(mktemp)
    # ...
}

# Use naming convention (maximum portability)
myfunc() {
    _myfunc_temp=$(mktemp)
    # ...
}

# Use subshell (for read-only functions)
myfunc() (
    temp=$(mktemp)
    cat "$1" > "$temp"
    process "$temp"
    rm "$temp"
)
```

### Reality Check

In practice, `local` works on almost all modern systems:
- Works: bash, ksh, zsh, dash, BusyBox ash, mksh
- Doesn't work: Original Bourne shell, some embedded systems

If you're only targeting modern Linux/Unix, `local` is safe to use. Add this to ignore:

```bash
# shellcheck disable=SC3043  # local is widely supported
```

---

## SC3003

**Message:** In POSIX sh, `$'...'` is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh

# ANSI-C quoting
echo $'Hello\nWorld'

# Tab character
IFS=$'\t'

# Escape sequences
message=$'Line 1\nLine 2\tTabbed'
```

### Correct Code

**Option 1: Use printf**

```bash
#!/bin/sh

# Generate newline with printf
printf 'Hello\nWorld\n'

# Or capture output
message=$(printf 'Line 1\nLine 2\tTabbed')

# For IFS, use actual tab
IFS='	'  # This is a real tab character
# Or generate it
IFS=$(printf '\t')
```

**Option 2: Use literal characters**

```bash
#!/bin/sh

# Literal newline in string
message='Line 1
Line 2	Tabbed'

# Real tab in code (type Ctrl-V then Tab)
IFS='	'
```

**Option 3: Use echo (unreliable)**

```bash
#!/bin/sh

# May work but not portable
message=$(echo "Line 1\nLine 2\tTabbed")
```

### Rationale

`$'...'` is ANSI-C quoting, a bash/ksh extension that interprets:
- `\n` as newline
- `\t` as tab
- `\x##` as hex character
- `\###` as octal character
- etc.

POSIX sh treats `$'...'` as literal string `$...`.

### Escape Sequence Alternatives

```bash
# Bash $'...'
newline=$'\n'
tab=$'\t'
backslash=$'\\'
quote=$'\''
bell=$'\a'

# POSIX printf
newline=$(printf '\n')
tab=$(printf '\t')
backslash=$(printf '\\')
quote=$(printf "'")
bell=$(printf '\a')

# POSIX embedded in strings
printf 'Line 1\nLine 2\n'  # printf interprets escapes
```

### Common Use Cases

```bash
# Case 1: Newlines in strings
# Bash
msg=$'Line 1\nLine 2'

# POSIX
msg='Line 1
Line 2'
# or
msg=$(printf 'Line 1\nLine 2')

# ----

# Case 2: IFS with special chars
# Bash
IFS=$'\n'

# POSIX - literal newline
IFS='
'
# or
IFS=$(printf '\n')

# ----

# Case 3: Control characters
# Bash
clear=$'\033[2J'

# POSIX
clear=$(printf '\033[2J')
```

### Printf Is Your Friend

```bash
# printf interprets escapes in POSIX
printf 'Tab:\there\n'
printf 'Newline:\nhere\n'
printf 'Backslash:\\ \n'
printf 'Quote:\'\n'

# Hex and octal
printf '\x41\n'    # Prints 'A'
printf '\101\n'    # Prints 'A'

# Variables with escapes
var="name"
printf 'Hello %s\n' "$var"
```

---

## SC3020

**Message:** In POSIX sh, `&>` is undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh

# Redirect stdout and stderr
command &> output.txt

# Append both
command &>> output.txt

# Redirect to null
command &> /dev/null
```

### Correct Code

```bash
#!/bin/sh

# POSIX: Redirect stderr to stdout, then stdout to file
command > output.txt 2>&1

# Append both
command >> output.txt 2>&1

# Redirect to null
command > /dev/null 2>&1

# Alternative order (stderr first)
command 2>&1 > output.txt  # Different! stdout to file, stderr to terminal
```

### Rationale

`&>` and `&>>` are bash shortcuts for redirecting both stdout and stderr. POSIX sh requires explicit redirection.

### Understanding Redirection Order

```bash
# Order matters!

# CORRECT: Both to file
command > file 2>&1
# 1. stdout goes to file
# 2. stderr goes to wherever stdout goes (file)

# WRONG: Only stdout to file
command 2>&1 > file
# 1. stderr goes to wherever stdout currently goes (terminal)
# 2. stdout goes to file
# Result: stdout in file, stderr on terminal

# ----

# Pipe both
# Bash
command &> >(other_command)

# POSIX
command 2>&1 | other_command
```

### Common Redirection Patterns

```bash
# Silent execution (discard all output)
# Bash
command &> /dev/null

# POSIX
command > /dev/null 2>&1

# ----

# Log both to file
# Bash
command &>> logfile

# POSIX
command >> logfile 2>&1

# ----

# Separate files for stdout and stderr
# Bash and POSIX (same)
command > stdout.txt 2> stderr.txt

# ----

# stderr to file, stdout to terminal
command 2> errors.txt

# stdout to file, stderr to terminal
command > output.txt
```

### Piping stderr

```bash
# Send stderr through pipe
# Bash
command 2>&1 | grep error

# POSIX (same)
command 2>&1 | grep error

# ----

# Swap stdout and stderr
# Bash and POSIX (complex)
command 3>&1 1>&2 2>&3 3>&-
# 1. Save stdout to fd 3
# 2. Send stdout to stderr
# 3. Send stderr to saved stdout (fd 3)
# 4. Close fd 3
```

---

## SC3030

**Message:** In POSIX sh, arrays are undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh

# Array declaration
files=(file1.txt file2.txt file3.txt)

# Array access
echo "${files[0]}"
echo "${files[@]}"

# Array assignment
config[key]="value"
```

### Correct Code

**Option 1: Use positional parameters**

```bash
#!/bin/sh

# Set positional parameters
set -- file1.txt file2.txt file3.txt

# Access
echo "$1"      # First
echo "$@"      # All
shift          # Remove first

# Count
echo "$#"

# Iterate
for file in "$@"; do
    echo "$file"
done
```

**Option 2: Use delimited strings**

```bash
#!/bin/sh

# Space-delimited (careful with spaces in values)
files="file1.txt file2.txt file3.txt"

# Newline-delimited (safer)
files='file1.txt
file2.txt
file3.txt'

# Iterate
for file in $files; do  # Intentionally unquoted
    echo "$file"
done

# Or with IFS
IFS='
'
for file in $files; do
    echo "$file"
done
```

**Option 3: Use multiple variables**

```bash
#!/bin/sh

file1="file1.txt"
file2="file2.txt"
file3="file3.txt"

# Process each
process_file "$file1"
process_file "$file2"
process_file "$file3"
```

**Option 4: Switch to bash**

```bash
#!/bin/bash

# Now arrays work
files=(file1.txt file2.txt file3.txt)
echo "${files[0]}"
```

### Rationale

Arrays (indexed and associative) are bash/ksh features, not in POSIX sh.

### Positional Parameters as Arrays

```bash
#!/bin/sh

# Initialize
set -- value1 value2 value3

# Access by position
first="$1"
second="$2"

# All values
all="$@"          # Word splits
all_quoted="$*"   # Single string

# Count
count=$#

# Iterate
for item in "$@"; do
    echo "$item"
done

# Shift (remove first)
shift
echo "$1"  # Now value2

# Append (add to end)
set -- "$@" new_value

# Prepend (add to beginning)
set -- new_value "$@"
```

### Building Lists

```bash
#!/bin/sh

# Build a list of files
files=""
for f in *.txt; do
    files="$files $f"
done

# Iterate over list
for f in $files; do  # Intentionally unquoted
    process "$f"
done

# ----

# Newline-separated (handles spaces in names)
files=""
for f in *.txt; do
    files="${files}${files:+$newline}$f"
done

# Set IFS for iteration
oldIFS=$IFS
IFS='
'
for f in $files; do
    process "$f"
done
IFS=$oldIFS
```

### Associative Array Alternatives

```bash
# Bash associative array
declare -A config
config[host]="localhost"
config[port]="8080"
echo "${config[host]}"

# POSIX - use separate variables
config_host="localhost"
config_port="8080"
echo "$config_host"

# POSIX - use eval (careful!)
key="host"
value="localhost"
eval "config_$key='$value'"
eval "echo \$config_$key"

# POSIX - use case
get_config() {
    case "$1" in
        host) echo "localhost" ;;
        port) echo "8080" ;;
        *) return 1 ;;
    esac
}
host=$(get_config host)
```

---

## Best Practices for POSIX Compliance

1. **Use correct shebang**: `#!/bin/sh` for POSIX, `#!/bin/bash` for bash
2. **Test with dash**: Debian's /bin/sh, strict POSIX
3. **Avoid bashisms**: No `[[`, `local`, `$'...'`, `&>`, etc.
4. **Use shellcheck**: Catches POSIX violations
5. **Document requirements**: State what shells are supported
6. **Consider tradeoffs**: POSIX portability vs code readability
7. **Use `# shellcheck disable=SC3000-SC4000`**: If targeting bash only

### Quick Reference: POSIX vs Bash

| Feature | Bash | POSIX Alternative |
|---------|------|-------------------|
| `[[ ]]` | Yes | `[ ]` or `case` |
| `local` | Yes | Naming convention |
| `$'...'` | Yes | `printf` or literal |
| `&>` | Yes | `> file 2>&1` |
| `arrays` | Yes | Positional parameters |
| `<(cmd)` | Yes | Temp files or pipes |
| `==` in test | Yes | `=` |
| `function` keyword | Yes | `name()` only |

---

## SC3011

**Message:** In POSIX sh, here-strings are undefined

**Severity:** Warning

### Problematic Code

```bash
#!/bin/sh
# Here-string not in POSIX
wc <<< "$1"

# Also used with read
read -r line <<< "some text"
```

### Correct Code

```bash
#!/bin/sh
# Use here-document instead
wc << EOF
$1
EOF

# For read, use echo and pipe
echo "some text" | read -r line

# Or use printf
printf '%s\n' "some text" | read -r line
```

### Rationale

Here-strings (`<<<`) are a Bash extension not available in POSIX sh or dash. They must be replaced with here-documents, echo/printf pipes, or temp files for portability.

### Examples

```bash
# ❌ Bad - Bash-specific here-strings
grep "pattern" <<< "$haystack"
while read line; do echo "$line"; done <<< "$multiline"

# ✅ Good - POSIX alternatives
echo "$haystack" | grep "pattern"
printf '%s\n' "$multiline" | while read line; do echo "$line"; done
```

### Exceptions

If your script requires Bash features, change the shebang to `#!/bin/bash` or use `# shellcheck disable=SC3000-SC4000`.

### Related Codes

- [SC3001](#sc3001) - `&>` redirection
- [SC3010](#sc3010) - `[[` `]]` conditional

---

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
- [SC2007 quick reference](common-errors.md#quick-reference-additional-common-errors) - Use `$((..))` for arithmetic

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

- [SC2028 quick reference](common-errors.md#quick-reference-additional-common-errors) - echo doesn't interpret escapes, use printf
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

## Quick Reference: Codes Covered in This Document

This quick reference is intentionally limited to the ShellCheck POSIX compatibility codes documented in detail above. For the full SC3000-SC3999 catalog, use the official ShellCheck wiki instead of a hand-maintained summary table here.

| Code | Detailed section |
|------|------------------|
| [SC3001](#sc3001) | Process substitution |
| [SC3003](#sc3003) | `$'...'` syntax |
| [SC3010](#sc3010) | `[[ ]]` test command |
| [SC3011](#sc3011) | Here-strings |
| [SC3014](#sc3014) | `==` in test expressions |
| [SC3020](#sc3020) | `&>` redirection |
| [SC3030](#sc3030) | Arrays |
| [SC3037](#sc3037) | `echo` flags |
| [SC3043](#sc3043) | `local` keyword |
| [SC3044](#sc3044) | `declare` / `typeset` / `let` |
| [SC3045](#sc3045) | Built-in command flags |
| [SC3046](#sc3046) | `source` vs `.` |
| [SC3054](#sc3054) | Array references |
| [SC3060](#sc3060) | String replacement |

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
