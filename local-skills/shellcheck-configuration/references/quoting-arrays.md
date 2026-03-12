# ShellCheck Quoting and Arrays Reference

This reference covers proper quoting, word splitting, and array handling to avoid common bugs in shell scripts.

## Table of Contents

- [SC2048: Quote $* in arrays](#sc2048)
- [SC2068: Quote array expansions](#sc2068)
- [SC2206: Quote array assignments](#sc2206)
- [SC2046: Quote command substitution](#sc2046)
- [Quoting Best Practices](#quoting-best-practices)
- [Array Handling Patterns](#array-handling-patterns)

---

## SC2048

**Message:** Use `"$@"` (with quotes) to prevent whitespace problems

**Severity:** Warning

### Problematic Code

```bash
# Using $* without quotes
cp $* ~/dir

# Array with * instead of @
cp ${array[*]} ~/dir

# In loops
for arg in $*; do
    echo "$arg"
done
```

### Correct Code

```bash
# Use "$@" with quotes
cp "$@" ~/dir

# Array with @ and quotes
cp "${array[@]}" ~/dir

# In loops
for arg in "$@"; do
    echo "$arg"
done

# Or just omit 'in' clause for arguments
for arg; do  # Equivalent to: for arg in "$@"
    echo "$arg"
done
```

### Rationale

`$*` and `${array[*]}` undergo word splitting and globbing:

**Example data:**
- Arguments: `baz`, `foo bar`, `*`, `/*/*/*/*`

**With `"$@"`:** → Exact preservation
- `baz`
- `foo bar`
- `*`
- `/*/*/*/*`

**With `$*`:** → Split and expanded
- `baz`
- `foo`
- `bar`
- `file.txt`
- `otherfile.jpg`
- ...thousands of files from `/*/*/*/*`...

### $@ vs $*

```bash
# $@ - All positional parameters as separate words
# "$@" - All positional parameters as separate quoted words (BEST)
# $* - All positional parameters as separate words (after split/glob)
# "$*" - All positional parameters as single word

# Example:
set -- "arg 1" "arg 2" "arg 3"

# Wrong - splits on spaces
for arg in $@; do
    echo "$arg"
done
# Outputs: arg, 1, arg, 2, arg, 3 (6 iterations!)

# Correct - preserves spaces
for arg in "$@"; do
    echo "$arg"
done
# Outputs: arg 1, arg 2, arg 3 (3 iterations)

# Single string (rarely useful)
echo "$*"
# Outputs: arg 1 arg 2 arg 3 (one line)
```

### IFS and $*

```bash
# "$*" joins with first character of IFS
set -- "a" "b" "c"

IFS=' '
echo "$*"   # a b c

IFS=','
echo "$*"   # a,b,c

IFS=$'\n'
echo "$*"   # a
            # b
            # c

# "$@" is unaffected by IFS
IFS=','
echo "$@"   # a b c (still space-separated as separate args)
```

### Passing Arguments Through

```bash
# Pass all arguments to another command
# WRONG
wrapper() {
    command $@
}

# CORRECT
wrapper() {
    command "$@"
}

# Example showing the problem
wrapper ls -la "/path with spaces"
# Without quotes: ls sees -la, /path, with, spaces (4 args)
# With quotes: ls sees -la, /path with spaces (2 args)
```

### Arrays

```bash
# Array - use ${array[@]} not ${array[*]}
files=(file1.txt "file with spaces.txt" file3.txt)

# WRONG - word splitting
for f in ${files[*]}; do
    echo "$f"
done
# file1.txt, file, with, spaces.txt, file3.txt (5 iterations)

# CORRECT - preserves elements
for f in "${files[@]}"; do
    echo "$f"
done
# file1.txt, file with spaces.txt, file3.txt (3 iterations)
```

---

## SC2068

**Message:** Double quote array expansions to avoid re-splitting elements

**Severity:** Warning

### Problematic Code

```bash
# Unquoted $@
cp $@ ~/dir

# Unquoted array expansion
rsync ${files[@]} destination/

# In command substitution
result=$(process $@)
```

### Correct Code

```bash
# Quote $@
cp "$@" ~/dir

# Quote array expansion
rsync "${files[@]}" destination/

# In command substitution
result=$(process "$@")
```

### Rationale

Unquoted `$@` and `${array[@]}` cause:
1. **Word splitting** on IFS characters (space, tab, newline)
2. **Glob expansion** of wildcards

**Example:**

```bash
# Setup
set -- "foo bar" "*.txt" "file"
files=("doc.pdf" "my file.txt")

# Unquoted - disaster
cp $@ "${files[@]}" /dest/
# Expands to: cp foo bar README.txt doc.txt script.txt doc.pdf my file.txt /dest/
# (*.txt expanded to all .txt files, "my file.txt" became two arguments)

# Quoted - correct
cp "$@" "${files[@]}" /dest/
# Expands to: cp "foo bar" "*.txt" "file" "doc.pdf" "my file.txt" /dest/
```

### Real-World Bugs

```bash
# Bug: Delete wrong files
files=(*.log)
rm ${files[@]}  # If filename has space, deletes unexpected files

# Fix
rm "${files[@]}"

# ----

# Bug: Arguments with wildcards
script --pattern="*.txt"
# Later in script:
process $pattern  # ERROR - expands glob!

# Fix
process "$pattern"

# ----

# Bug: Paths with spaces
path="/home/user/My Documents"
cd $path  # ERROR - cd sees "/home/user/My" and "Documents"

# Fix
cd "$path"
```

### When Globbing Is Intended

If you actually want glob expansion:

```bash
# Want to expand *.txt
files="*.txt"
ls $files  # Intentionally unquoted to expand

# Or be explicit with array
files=(*.txt)
ls "${files[@]}"  # Expands when assigned, quote when using
```

But usually it's better to expand explicitly:

```bash
# Clear intent - expand glob into array
shopt -s nullglob  # Avoid literal "*.txt" if no matches
files=(*.txt)

# Use array safely
process "${files[@]}"
```

---

## SC2206

**Message:** Quote to prevent word splitting/globbing, or split robustly with mapfile or read -a

**Severity:** Warning

### Problematic Code

```bash
# Unquoted variable in array
array=( $var )

# Multiple unquoted variables
array=( $var1 $var2 $var3 )

# Command substitution
array=( $(get_items) )
```

### Correct Code

**For single element:**

```bash
# Variable should be one element
array=( "$var" )
```

**For splitting on lines:**

```bash
# Bash - mapfile
mapfile -t array <<< "$var"

# Or from command
mapfile -t array < <(get_items)

# Portable - while loop
while IFS= read -r line; do
    array+=("$line")
done <<< "$var"
```

**For splitting on words:**

```bash
# Bash - read -a
IFS=' ' read -r -a array <<< "$var"

# Ksh - read -A
IFS=' ' read -r -A array <<< "$var"

# Custom delimiter
IFS=':' read -r -a array <<< "$PATH"
```

**From command output:**

```bash
# Bash - mapfile
mapfile -t files < <(find . -name "*.txt")

# Portable - while loop
files=()
while IFS= read -r -d '' file; do
    files+=("$file")
done < <(find . -name "*.txt" -print0)
```

### Rationale

Unquoted expansion in arrays causes word splitting and globbing:

```bash
var="foo bar baz"

# Unquoted - splits into 3 elements
array=( $var )
# array=(foo bar baz)

# Quoted - single element
array=( "$var" )
# array=("foo bar baz")
```

With globs:

```bash
var="*.txt"

# Unquoted - glob expands
array=( $var )
# array=(file1.txt file2.txt file3.txt ...)

# Quoted - literal
array=( "$var" )
# array=("*.txt")
```

### Proper Splitting Techniques

```bash
# 1. Split on newlines with mapfile
output="line1
line2
line3"

mapfile -t array <<< "$output"
# array=("line1" "line2" "line3")

# ----

# 2. Split on delimiter with read
data="a:b:c:d"

IFS=':' read -r -a array <<< "$data"
# array=(a b c d)

# ----

# 3. Build array in loop
array=()
for file in *.txt; do
    [[ -f "$file" ]] && array+=("$file")
done

# ----

# 4. From command with proper null separation
mapfile -t -d '' array < <(find . -type f -print0)
```

### Multiline Input

```bash
# From heredoc
mapfile -t lines <<'EOF'
First line
Second line
Third line
EOF

# From file
mapfile -t lines < file.txt

# From command
mapfile -t processes < <(ps aux | grep myapp)
```

### Building Arrays Safely

```bash
# Start empty
files=()

# Add single elements (preserves spaces/globs)
files+=("my file.txt")
files+=("*.conf")  # Literal asterisk

# Add multiple elements
files+=("file1" "file2" "file3")

# Add from glob (expanded at assignment)
files+=(*.log)

# Add from another array
files+=("${other_array[@]}")
```

---

## SC2046

**Message:** Quote this to prevent word splitting

**Severity:** Warning

### Problematic Code

```bash
# Unquoted command substitution
ls -l $(get_file)

# In assignments
var=$(get_value)

# Multiple commands
rm $(find . -name "*.tmp")
```

### Correct Code

```bash
# Quoted
ls -l "$(get_file)"

# Assignment - quote if value might have special chars
var="$(get_value)"

# Better - use -exec or xargs
find . -name "*.tmp" -delete
# or
find . -name "*.tmp" -exec rm {} +
# or
find . -name "*.tmp" | xargs rm
```

### Rationale

Unquoted `$(...)` undergoes word splitting and globbing:

```bash
# Command returns: "file with spaces.txt"
file=$(get_filename)

# Unquoted
cat $(get_filename)
# Executes: cat file with spaces.txt
# Error: cat sees 3 files

# Quoted
cat "$(get_filename)"
# Executes: cat "file with spaces.txt"
# Correct!
```

### With Globs

```bash
# Command returns: "*.txt"
pattern=$(get_pattern)

# Unquoted - glob expands
for f in $(get_pattern); do
    echo "$f"
done
# Iterates over all .txt files

# Quoted - literal
for f in "$(get_pattern)"; do
    echo "$f"
done
# Single iteration: "*.txt"
```

### When NOT to Quote

```bash
# Intentional word splitting for commands
# DON'T do this
flags=$(get_compiler_flags)
gcc $flags main.c  # Unquoted because flags should split

# DO this instead - use array
flags=($(get_compiler_flags))  # Then immediately:
read -r -a flags <<< "$(get_compiler_flags)"  # Better
gcc "${flags[@]}" main.c
```

---

## Quoting Best Practices

### General Rules

```bash
# 1. ALWAYS quote variables and command substitutions
echo "$var"
echo "$(command)"

# 2. Use "$@" not $@ for arguments
process "$@"

# 3. Use "${array[@]}" not ${array[@]} for arrays
process "${array[@]}"

# 4. Quote in assignments if value has special chars
path="$HOME/My Documents"

# 5. Don't quote when you want word splitting (rare)
# Only if you're absolutely sure!
```

### When To Quote

```bash
# Variables
echo "$var"              # Always
path="$HOME/dir"         # Always
cd "$path"               # Always

# Command substitution
result="$(command)"      # Usually
count=$(wc -l < file)    # Even numbers!

# Parameter expansion
echo "${var#prefix}"     # Always
echo "${var:-default}"   # Always

# Arrays
"${array[@]}"            # Always
"${array[0]}"            # Always
```

### When NOT To Quote

```bash
# Arithmetic
count=$((count + 1))     # No quotes needed
if (( x > 10 )); then    # No quotes needed

# Assignment right-hand side is safe from splitting
var=$other_var           # No quotes needed (but doesn't hurt)
var=literal              # No quotes needed

# Intentional glob
files=(*.txt)            # Unquoted to expand
```

### Edge Cases

```bash
# Empty strings
var=""                   # Quote to make explicit
var=${other:-}           # Gets empty, quotes not needed but good

# Literals with special chars
echo "Price: $9.99"      # Quote to avoid $ interpretation? No - $9 ok
echo 'Price: $9.99'      # Single quote safest
echo "Price: \$9.99"     # Escape also works

# Mixed quotes
echo "He said: 'hello'"  # Single quotes inside double
echo 'Path is '$HOME     # Break string to interpolate
```

---

## Array Handling Patterns

### Creating Arrays

```bash
# Literal elements
array=("item1" "item2" "item3")

# From glob
files=(*.txt)

# Empty array
array=()

# Single element
array=("$var")

# From command (mapfile)
mapfile -t lines < file.txt

# From command (loop)
files=()
while IFS= read -r -d '' file; do
    files+=("$file")
done < <(find . -type f -print0)
```

### Accessing Arrays

```bash
# First element
echo "${array[0]}"

# Specific element
echo "${array[5]}"

# All elements (separately quoted)
echo "${array[@]}"
process "${array[@]}"

# All elements (single string)
echo "${array[*]}"

# Number of elements
echo "${#array[@]}"

# Indices
echo "${!array[@]}"
```

### Modifying Arrays

```bash
# Append one element
array+=("new item")

# Append multiple elements
array+=("item1" "item2")

# Append another array
array+=("${other_array[@]}")

# Prepend
array=("first" "${array[@]}")

# Replace element
array[3]="new value"

# Delete element (leaves gap)
unset 'array[3]'

# Delete entire array
unset array
```

### Iterating Arrays

```bash
# Iterate elements
for item in "${array[@]}"; do
    echo "$item"
done

# Iterate with index
for i in "${!array[@]}"; do
    echo "Item $i: ${array[i]}"
done

# While with array
i=0
while (( i < ${#array[@]} )); do
    echo "${array[i]}"
    ((i++))
done
```

### Array Slicing

```bash
array=(a b c d e f)

# Elements from index 2
echo "${array[@]:2}"        # c d e f

# 3 elements from index 1
echo "${array[@]:1:3}"      # b c d

# Last element
echo "${array[@]: -1}"      # f (note space before -)

# All except last
echo "${array[@]:0:${#array[@]}-1}"  # a b c d e
```

### Associative Arrays (Bash 4+)

```bash
# Declare
declare -A config

# Assign
config[host]="localhost"
config[port]=8080
config[user]="admin"

# Access
echo "${config[host]}"

# All keys
echo "${!config[@]}"

# All values
echo "${config[@]}"

# Iterate
for key in "${!config[@]}"; do
    echo "$key = ${config[$key]}"
done
```

### Common Patterns

```bash
# Check if element exists
if [[ -v array[5] ]]; then
    echo "Element 5 exists"
fi

# Check if array has elements
if (( ${#array[@]} > 0 )); then
    echo "Array is not empty"
fi

# Deduplicate array (bash 4+)
declare -A seen
unique=()
for item in "${array[@]}"; do
    [[ -v seen[$item] ]] && continue
    seen[$item]=1
    unique+=("$item")
done

# Join array with delimiter
IFS=:
joined="${array[*]}"
IFS=$' \t\n'  # Reset

# Split string into array
IFS=: read -r -a array <<< "$PATH"
```

---

## Summary

**Golden Rules:**
1. **Always quote** `"$var"` and `"$(cmd)"`
2. **Use `"$@"`** not `$@` for arguments
3. **Use `"${array[@]}"`** not `${array[@]}` for arrays
4. **Use mapfile/read -a** for intentional splitting
5. **Test with spaces** in filenames and values
6. **Test with glob characters** like `*` and `?`

**Common Mistakes:**
- `cp $@` → `cp "$@"`
- `array=( $var )` → `array=( "$var" )` or `mapfile`
- `for f in ${files[@]}` → `for f in "${files[@]}"`
- `rm $(find ...)` → `find ... -delete` or `-exec`

**Tools:**
- ShellCheck catches these issues
- Test with: `touch "file with spaces.txt" "file*.txt"`
- Use `set -x` to see expansions
