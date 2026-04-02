# ShellCheck Common Error Codes Reference

This reference provides detailed information about the most frequently encountered ShellCheck error codes, including problematic examples and correct solutions.

## Table of Contents

- [SC2086: Quote to prevent word splitting](#sc2086)
- [SC2181: Check exit code directly](#sc2181)
- [SC2015: && || is not if-then-else](#sc2015)
- [SC2016: Single quotes don't expand](#sc2016)
- [SC1091: Not following source](#sc1091)
- [SC2034: Variable appears unused](#sc2034)
- [SC2115: Dangerous wildcard expansion](#sc2115)
- [SC2164: cd may fail](#sc2164)
- [SC2155: Masked return values](#sc2155)
- [SC2009: Use pgrep instead of ps | grep](#sc2009)
- [SC2012: Use find instead of ls](#sc2012)
- [SC2116: Remove useless echo](#sc2116)
- [SC2162: Use read -r](#sc2162)
- [SC2230: Use command -v instead of which](#sc2230)
- [SC2236: Use -n instead of ! -z](#sc2236)

---

## SC2086

**Message:** Double quote to prevent globbing and word splitting

**Severity:** Warning

### Problematic Code

```bash
# Unquoted variable expansion
echo $1
for i in $*; do
    echo "$i"
done

# Command with unquoted args
find . -name $pattern

# Building paths
cp $src/$file $dest/$file
```

### Correct Code

```bash
# Quoted variable expansion
echo "$1"
for i in "$@"; do
    echo "$i"
done

# Command with quoted args
find . -name "$pattern"

# Building paths (entire expression quoted)
cp "$src/$file" "$dest/$file"
```

### Rationale

Unquoted variables undergo:
1. **Word splitting** - splits on IFS (spaces, tabs, newlines)
2. **Glob expansion** - expands wildcards like `*`, `?`, `[...]`

This causes unexpected behavior when:
- Variables contain spaces: `file="my document.txt"` → becomes two arguments
- Variables contain globs: `pattern="*.txt"` → expands to matching files
- Variables are empty: may cause syntax errors

### Proper Quoting Patterns

```bash
# Minimal quoting (good)
"$HOME"/"$dir"/bin/"$file"

# Canonical quoting (preferred)
"$HOME/$dir/bin/$file"

# Command substitution also needs quoting
echo "Variable: $var and command: $(date)"
echo "Both quoted: $var and $(date)"
```

### Exceptions

When you intentionally want word splitting, use an array instead:

```bash
# DON'T do this
options="-j 5 -B -d"
make $options file

# DO this instead
options=(-j 5 -B -d)
make "${options[@]}" file
```

For optional arguments:

```bash
# DON'T do this
debug=""
[[ $1 == "--trace" ]] && debug="-x"
bash $debug script  # Fails when debug is empty

# DO this
debug=""
[[ $1 == "--trace" ]] && debug="yes"
bash ${debug:+"-x"} script
```

### Related Codes
- SC2048: Use `"$@"` instead of `$*`
- SC2068: Double quote array expansions

---

## SC2181

**Message:** Check exit code directly with e.g. `if mycmd;`, not indirectly with `$?`

**Severity:** Style

### Problematic Code

```bash
# Checking $? after command
make mytarget
if [ $? -ne 0 ]; then
    echo "Build failed"
fi

# In a loop
while true; do
    ping -c1 example.com
    if [ $? -eq 0 ]; then
        break
    fi
done
```

### Correct Code

```bash
# Check command directly
if ! make mytarget; then
    echo "Build failed"
fi

# In a loop
while ! ping -c1 example.com; do
    sleep 1
done

# With output capture
if ! output=$(make mytarget); then
    echo "Build failed"
    echo "Output was: $output"
fi
```

### Rationale

Checking `$?` is redundant and error-prone:

1. **Decoupled check**: Inserting innocent commands breaks it
   ```bash
   make mytarget
   echo "make finished"  # Oops! Now checking echo's exit code
   if [ $? -ne 0 ]; then
       echo "This never runs"
   fi
   ```

2. **Incompatible with `set -e`**: Script may exit before the check
   ```bash
   set -e
   make mytarget  # If this fails, script exits here
   if [ $? -ne 0 ]; then  # Never reached
       echo "Never runs"
   fi
   ```

3. **Can't access $? later**: Test command overwrites it
   ```bash
   # Wrong - can't get original $?
   if make mytarget; then
       echo "Success"
   else
       echo "Failed with: $?"  # This is now 0!
   fi
   ```

### Solaris 10 Bourne Shell Exception

The default Solaris 10 shell doesn't support `!`, so use:

```bash
# For Solaris 10 /bin/sh
if make mytarget; then
    :  # success case (: is no-op)
else
    echo "Build failed"
fi
```

### Related Codes
- SC2320: `$?` refers to echo/printf
- SC2319: `$?` refers to condition, not command

---

## SC2015

**Message:** Note that `A && B || C` is not if-then-else. C may run when A is true

**Severity:** Warning

### Problematic Code

```bash
# Looks like if-then-else but isn't
[[ $dryrun ]] && echo "Would delete file" || rm file

# Another example
[[ -f "$file" ]] && cat "$file" || echo "File not found"

# With commands that may fail
command1 && echo "Success" || echo "Failure"
```

### Correct Code

```bash
# Use proper if-then-else
if [[ $dryrun ]]; then
    echo "Would delete file"
else
    rm file
fi

# For the file check
if [[ -f "$file" ]]; then
    cat "$file"
else
    echo "File not found"
fi

# When you need output capture
if result=$(command1); then
    echo "Success: $result"
else
    echo "Failure"
fi
```

### Rationale

The pattern `A && B || C` means:
- Run B if A succeeds
- Run C if A OR B fails

**C runs when B fails, even if A succeeded!**

Example of the problem:

```bash
# If stdout is closed, echo fails and file gets deleted!
[[ $dryrun ]] && echo "Would delete" || rm file

# Running with closed stdout
script --dryrun >&-  # File gets deleted despite $dryrun being set!
```

### How It's Evaluated

Think of it as left-associative:

```bash
( ([[ $dryrun ]] && echo "Would delete") || rm file )
```

Execution flow:
1. If `[[ $dryrun ]]` succeeds → run echo
2. If echo fails → run rm (even though $dryrun was true!)

### When To Use `&& ||`

It's acceptable when you intentionally want C to run if either A or B fails:

```bash
# Retry logic - try command1, if it fails try command2
command1 || command2

# Provide default value
value="${input:-default}"

# Chain multiple fallbacks
cmd1 || cmd2 || cmd3 || echo "All failed"
```

### Related Codes
- SC2312: Consider invoking command separately to avoid masking return value

---

## SC2016

**Message:** Expressions don't expand in single quotes, use double quotes for that

**Severity:** Info

### Problematic Code

```bash
# Variable in single quotes
name="World"
echo 'Hello $name'  # Outputs: Hello $name

# Command substitution in single quotes
echo 'Current dir: $(pwd)'  # Outputs: Current dir: $(pwd)

# Backticks in single quotes
echo 'Today is `date`'  # Outputs: Today is `date`
```

### Correct Code

```bash
# Use double quotes for expansion
name="World"
echo "Hello $name"  # Outputs: Hello World

# Command substitution
echo "Current dir: $(pwd)"  # Outputs: Current dir: /home/user

# With backticks (though $() is preferred)
echo "Today is $(date)"
```

### Rationale

Single quotes preserve **everything** literally:
- `$var` stays as literal `$var`
- `$(cmd)` stays as literal `$(cmd)`
- `\n` stays as literal `\n` (not newline)

Double quotes allow expansion of:
- Variables: `$var`, `${var}`
- Command substitution: `$(cmd)`, `` `cmd` ``
- Arithmetic: `$((expr))`

But preserve literal:
- Spaces, newlines
- Most special characters

### Mixing Quotes

When you need both literal and expanded parts:

```bash
# Mix single and double quotes
dialog --msgbox "File $file may not contain: "'`&;"\#%$' 10 70

# Or escape within double quotes
echo "PATH=\$PATH:/usr/local/bin" >> ~/.bashrc
```

### Legitimate Uses of Single Quotes

```bash
# When you truly want literal dollar signs
# shellcheck disable=SC2016
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc

# For envsubst templates
# shellcheck disable=SC2016
envsubst '${SERVICE_HOST}:${SERVICE_PORT}' config.template > config

# For PS4 trace prompts (expands during trace, not now)
# shellcheck disable=SC2016
PS4='+$BASH_SOURCE:$LINENO:$FUNCNAME: '
```

### When To Disable This Warning

In your `.shellcheckrc`:

```
# If you frequently use literal $ in scripts
disable=SC2016
```

Or for specific instances:

```bash
# shellcheck disable=SC2016
echo 'Literal $variable here'
```

### Related Codes
- SC1003: Escaping single quotes
- SC2026: Nested quote issues

---

## SC1091

**Message:** Not following: (error message here)

**Severity:** Info

### Problematic Code

```bash
# Source file not found by ShellCheck
source somefile

# Source with relative path
source ../lib/functions.sh

# Source from variable (see SC1090 instead)
source "$CONFIG_DIR/settings.conf"
```

### Correct Code

**If file is in your repository:**

```bash
# Tell ShellCheck where to find it
# shellcheck source=somefile
source somefile

# Or with path relative to script
# shellcheck source=../lib/functions.sh
source ../lib/functions.sh
```

**If file is external or generated:**

```bash
# Disable following for external files
# shellcheck source=/dev/null
source /usr/share/myapp/config

# shellcheck source=/dev/null
source generated_file.sh
```

### Rationale

ShellCheck can't follow the source because:

1. **File not provided**: Not included on command line
2. **No -x flag**: Need `shellcheck -x script.sh` or `external-sources=true` in `.shellcheckrc`
3. **File permissions**: Can't read the file
4. **Path issues**: File doesn't exist at specified location
5. **Dynamic path**: Variable path (different error - SC1090)

### Using `-x` Flag

Enable following sourced files:

```bash
# Command line
shellcheck -x script.sh

# Or in .shellcheckrc
external-sources=true
```

### Multiple Source Locations

```bash
# Provide multiple files to ShellCheck
shellcheck -x main.sh lib/*.sh

# Or use source directive
# shellcheck source=lib/common.sh
source lib/common.sh
```

### Best Practices

```bash
# 1. Use consistent paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib/functions.sh
source "$SCRIPT_DIR/lib/functions.sh"

# 2. Check file existence
if [[ -f "$config_file" ]]; then
    # shellcheck source=/dev/null
    source "$config_file"
fi

# 3. Use absolute paths when possible
# shellcheck source=/etc/myapp/config.sh
source /etc/myapp/config.sh
```

### .shellcheckrc Configuration

```bash
# Enable external sources globally
external-sources=true

# Set source path hints
source-path=SCRIPTDIR
source-path=lib
source-path=/usr/share/myapp
```

### Related Codes
- SC1090: Can't follow non-constant source

---

## SC2034

**Message:** Variable appears unused. Verify it or export it

**Severity:** Warning

### Problematic Code

```bash
# Typo in variable name
foo=42
echo "$FOO"  # Should be $foo

# Variable assigned but never used
name="John"
age=30
echo "Age: $age"  # name is never used

# Variable used only in indirection
config_file="/etc/app.conf"
setting_name="config_file"
echo "${!setting_name}"  # ShellCheck can't track indirect refs
```

### Correct Code

```bash
# Fix typo
foo=42
echo "$foo"

# Remove unused variable
age=30
echo "Age: $age"

# Export if used by child processes
export CONFIG_FILE="/etc/app.conf"
./child_script.sh  # Can access $CONFIG_FILE

# Use underscore for intentionally unused
read _ last _ zip _ _ <<< "$data"
echo "$last, $zip"
```

### Rationale

Unused variables often indicate:
- **Typos**: `$VAR` vs `$var`
- **Dead code**: Variables no longer needed
- **Logic errors**: Forgot to use the variable
- **Confusion**: `local let foo=42` declares variable `let`, not a local let statement

### Dummy Variables

For variables you need to assign but won't use:

```bash
# Single underscore for throwaway
read _ last _ zip _ _ <<< "$str"
echo "$last, $zip"

# Underscore prefix (ShellCheck 0.7.2+)
read _first last _email zip _lat _lng <<< "$str"
echo "$last, $zip"

# Named but disabled warning
# shellcheck disable=SC2034  # Unused for readability
read first last email zip lat lng <<< "$str"
echo "$last, $zip"
```

### Indirection False Positives

ShellCheck intentionally doesn't track indirect references:

```bash
# All generate SC2034 even though used indirectly
foo=42
name=foo

echo "${!name}"        # Indirect expansion
echo "$((name))"       # Arithmetic indirection
eval "echo \$name"     # eval indirection
declare -n ref=foo; echo "$ref"  # nameref
```

**This is intentional.** Use arrays or disable the warning:

```bash
# Better: Use associative array
declare -A config
config[foo]=42
echo "${config[foo]}"

# Or ignore the warning
# shellcheck disable=SC2034
foo=42
name=foo
echo "${!name}"
```

### Variables Used Externally

```bash
# Used by child processes
export BUILD_DIR="/tmp/build"
export CC="gcc"
make  # Uses exported variables

# Used by sourced files
LIB_VERSION="1.2.3"
source lib/common.sh  # Uses $LIB_VERSION

# Used in heredocs
cat <<EOF
Version: $VERSION
Author: $AUTHOR
EOF
```

### Related Codes
- SC2153: Possible misspelling
- SC2163: Exporting with $

---

## SC2115

**Message:** Use `"${var:?}"` to ensure this never expands to `/*`

**Severity:** Warning

### Problematic Code

```bash
# Dangerous - if $STEAMROOT is empty, deletes everything!
rm -rf "$STEAMROOT/"*

# Also dangerous
rm -rf $BUILD_DIR/*
rm -rf ${PREFIX}/bin/*

# In cleanup scripts
rm -rf "$TMPDIR/"*
```

### Correct Code

```bash
# Use :? to fail if variable is unset/empty
rm -rf "${STEAMROOT:?}/"*

# With custom error message
rm -rf "${STEAMROOT:?STEAMROOT not set}/"*

# Or use :- for default value
rm -rf "${BUILD_DIR:-/tmp/build}/"*

# Validate before using
if [[ -n "$TMPDIR" ]]; then
    rm -rf "$TMPDIR/"*
else
    echo "Error: TMPDIR not set" >&2
    exit 1
fi
```

### Rationale

If the variable is empty, the command becomes:

```bash
# Original intent
rm -rf "/usr/local/steam/"*

# If $STEAMROOT is empty
rm -rf "/"*  # DELETES EVERYTHING ON SYSTEM!
```

This has caused real-world disasters:
- [Steam for Linux bug #3671](https://github.com/ValveSoftware/steam-for-linux/issues/3671)
- Countless production database wipes
- Accidental `/` deletions

### Parameter Expansion Operators

```bash
# :? - Fail if unset or empty
"${var:?}"
"${var:?Error: var not set}"

# :- - Use default if unset or empty
"${var:-/default/path}"

# := - Assign default if unset or empty
"${var:=/default/path}"

# :+ - Use alternate value if set
"${var:+/alternate/path}"
```

### With Command Substitution

For commands that might fail:

```bash
# DON'T do this - command failure gives empty string
rm -rf "$(get_build_dir)/"*

# DO this - assign and validate
build_dir=$(get_build_dir) || {
    echo "Error: Could not determine build dir" >&2
    exit 1
}
rm -rf "${build_dir:?}/"*
```

### Real-World Safe Patterns

```bash
# Safe cleanup function
cleanup() {
    local dir="${1:?cleanup requires directory}"
    [[ "$dir" == "/"* ]] || dir="$PWD/$dir"
    [[ "$dir" != "/" ]] || { echo "Cannot clean root!" >&2; return 1; }
    rm -rf "$dir"
}

# Safe build directory
BUILD_DIR="${BUILD_DIR:?BUILD_DIR must be set}"
[[ -d "$BUILD_DIR" ]] || mkdir -p "$BUILD_DIR"
rm -rf "${BUILD_DIR:?}/"*

# Temporary directory cleanup
cleanup_temp() {
    local temp="${TMPDIR:-${TMP:-/tmp}}/myapp.$$"
    [[ -d "$temp" ]] && rm -rf "${temp:?}"
}
```

### Alternative: Validate First

```bash
# Explicit validation
validate_dir() {
    local dir="$1"
    [[ -n "$dir" ]] || { echo "Error: Directory empty" >&2; return 1; }
    [[ "$dir" != "/" ]] || { echo "Error: Cannot use root" >&2; return 1; }
    [[ -d "$dir" ]] || { echo "Error: Not a directory: $dir" >&2; return 1; }
}

if validate_dir "$BUILD_DIR"; then
    rm -rf "$BUILD_DIR/"*
fi
```

### Related Codes
- SC2115: Missing variable check before rm -rf

---

## SC2164

**Message:** Use `cd ... || exit` in case cd fails

**Severity:** Warning

### Problematic Code

```bash
# In scripts
cd generated_files
rm -r *.c  # If cd failed, deletes *.c from current dir!

# In functions
func() {
    cd "$1"
    do_something  # Runs in wrong directory if cd fails
}

# Build scripts
cd "$BUILD_DIR"
make clean  # Cleans wrong directory if cd fails
```

### Correct Code

```bash
# Exit on failure (scripts)
cd generated_files || exit
rm -r *.c

# Return on failure (functions)
func() {
    cd "$1" || return
    do_something
}

# With error message
cd "$BUILD_DIR" || {
    echo "Error: Cannot access build directory" >&2
    exit 1
}
make clean

# Conditional handling
if cd "$target_dir"; then
    echo "Processing files in $target_dir"
    process_files
else
    echo "Warning: Could not access $target_dir" >&2
fi
```

### Rationale

`cd` can fail for many reasons:
- Directory doesn't exist
- No permissions
- Path is actually a file
- Broken symlink
- Path too long
- Network mount timeout

If `cd` fails and you continue, **you're operating in the wrong directory:**

```bash
# Disaster waiting to happen
cd /data/temp/build_12345
rm -rf *  # If cd failed, this runs in current directory!
```

### Common Failure Handling Patterns

```bash
# 1. Exit immediately (scripts)
cd "$dir" || exit
cd "$dir" || exit 1  # With explicit exit code

# 2. Return from function
myfunc() {
    cd "$1" || return
    cd "$2" || return 1  # With exit code
}

# 3. Exit with message
cd "$dir" || {
    echo "Failed to cd to $dir" >&2
    exit 1
}

# 4. Conditional logic
if cd "$dir"; then
    echo "Success"
    do_work
else
    echo "Failed to cd to $dir" >&2
    exit 1
fi

# 5. Subshell (returns to original dir)
(cd "$dir" && make) || exit 1

# 6. Pushd/popd alternative
pushd "$dir" || exit
do_work
popd
```

### Using set -e

With `set -e`, scripts exit on any error:

```bash
#!/bin/bash
set -e  # Exit on error

cd "$dir"  # Will exit if this fails
rm -rf *   # Only runs if cd succeeded
```

However, ShellCheck still warns because `set -e` doesn't always work as expected and can be disabled in certain contexts.

### Subshells and Command Substitution

In subshells, use `&&` or explicit exit:

```bash
# Subshell
(cd "$dir" || exit; make)

# Command substitution
result=$(cd "$dir" && make)
```

### When ShellCheck Doesn't Warn

ShellCheck suppresses this warning when `cd` is already in a conditional:

```bash
# No warning - already handled
cd "$dir" || exit
cd "$dir" && make

# No warning - in condition
if cd "$dir"; then
    make
fi

while cd "$dir"; do
    work
done
```

### Related Codes
- SC2103: Use subshell to avoid cd back

---

## SC2155

**Message:** Declare and assign separately to avoid masking return values

**Severity:** Warning

### Problematic Code

```bash
# With local
local result=$(make build)
if [[ $? -eq 0 ]]; then  # $? is from 'local', not 'make'!
    echo "Build succeeded"
fi

# With export
export config=$(load_config)
# Can't detect if load_config failed

# With readonly
readonly version=$(get_version)
# Version might be empty if get_version failed
```

### Correct Code

```bash
# Separate declaration and assignment
local result
result=$(make build)
if [[ $? -eq 0 ]]; then  # Now $? is from 'make'
    echo "Build succeeded"
fi

# Or check directly
local result
if result=$(make build); then
    echo "Build succeeded: $result"
fi

# With export
config=$(load_config) || exit 1
export config

# With readonly
version=$(get_version) || {
    echo "Error: Cannot determine version" >&2
    exit 1
}
readonly version
```

### Rationale

When you combine declaration and assignment, the exit code is from the **declaration**, not the command:

```bash
# What you think happens
local foo=$(mycmd)  # $? = exit code of mycmd

# What actually happens
local foo=$(mycmd)  # $? = exit code of 'local' (always 0)
```

Example demonstrating the problem:

```bash
# Function appears to work
f() {
    local foo=$(false) && echo "error was hidden"
}
f
# Output: "error was hidden"  (wrong!)

# Separated version works correctly
f() {
    local foo
    foo=$(false) && echo "error was hidden"
}
f
# Output: (nothing - false returned 1, && didn't run)
```

### Impact on Error Handling

This breaks multiple error-handling patterns:

```bash
# set -e doesn't work
set -e
local result=$(failing_command)  # Doesn't exit!
echo "Script continues"

# Conditional doesn't work
if local result=$(failing_command); then  # Always true!
    echo "This always runs"
fi

# $? is useless
local result=$(failing_command)
if [[ $? -ne 0 ]]; then  # $? is 0 from 'local'
    echo "Never runs"
fi
```

### Correct Patterns

```bash
# 1. Declare and assign separately
local result
result=$(command)

# 2. Check in conditional
local result
if result=$(command); then
    echo "Success"
fi

# 3. Use || for error handling
local result
result=$(command) || {
    echo "Command failed" >&2
    return 1
}

# 4. Explicitly ignore errors
local result
result=$(command) || true
```

### Dash Shell Bug

Dash has additional problems with combined declare/assign:

```bash
# Fails in dash 0.5.8-2.10
f() {
    local e=$1
}
f "1 2"
# Error: local: 2: bad variable name

# Also fails
export g=$(printf '%s' "foo 2")
# Error: export: 2: bad variable name
```

**Solution:** Quote the right side or separate:

```bash
# Quote right side
local e="$1"

# Or separate
local e
e="$1"
```

### Exception: Literal Values

ShellCheck doesn't warn for literal assignments:

```bash
# No warning - no command to fail
export PATH="/usr/local/bin:$PATH"
local count=0
readonly MAX_RETRY=3
```

### Exception: Read-only Declarations

ShellCheck doesn't warn for `local -r` because the alternative is cumbersome:

```bash
# ShellCheck doesn't warn (even though it masks return)
local -r foo=$(cmd)

# Alternative is too verbose
local foo
foo=$(cmd)
local -r foo  # Error: foo is already set
```

Enable `check-extra-masked-returns` directive to see these warnings.

### Related Codes
- SC2312: Command substitution masks return value
- SC2310: Function in condition disables errexit

---

---

## SC2009

**Message:** Consider using `pgrep` instead of grepping `ps` output

**Severity:** Info

### Problematic Code

```bash
# Grepping ps output
ps aux | grep -v grep | grep "$service" > /dev/null

# Getting PIDs from ps
pid=$(ps aux | grep myapp | grep -v grep | awk '{print $2}')

# Checking if process is running
if ps aux | grep -q "[m]yapp"; then
    echo "Running"
fi
```

### Correct Code

```bash
# Use pgrep directly
pgrep -f "$service" > /dev/null

# Getting PIDs
pid=$(pgrep myapp)

# Checking if process is running
if pgrep -q myapp; then
    echo "Running"
fi

# Get process info safely
for pid in $(pgrep '^python$'); do
    user=$(ps -o user= -p "$pid")
    echo "Process $pid is run by $user"
done
```

### Rationale

`pgrep` is safer and more reliable than parsing `ps` output:
- Matches only the command name, not other fields
- No need for `grep -v grep` tricks
- Supports filtering by user, group, terminal
- Returns PIDs directly
- Avoids false matches (e.g., username containing search term)

### Common Issues with ps | grep

```bash
# Problem: Matches grep itself
ps aux | grep myapp
# Shows: both myapp AND the grep command

# Problem: Matches unrelated fields
# If username is "pythondev", this matches it too
ps aux | grep python | cut -f2 -d' '

# Problem: Fragile parsing
# ps output format varies by system and locale
ps aux | awk '{print $2}' | grep pattern
```

### pgrep Options

```bash
# Match full command line
pgrep -f "myapp --config"

# Match exact command name
pgrep -x myapp

# Filter by user
pgrep -u username processname

# Count processes
pgrep -c myapp

# Show process names too
pgrep -l myapp
```

### Exceptions

`pgrep` is not POSIX. Ignore this if targeting POSIX userlands.

Also ignore if matching criteria `pgrep` doesn't support:

```bash
# pgrep doesn't support filtering by nice value
# shellcheck disable=SC2009
ps -axo nice=,pid= | grep -v '^  0'
```

---

## SC2012

**Message:** Use `find` instead of `ls` to better handle non-alphanumeric filenames

**Severity:** Info

### Problematic Code

```bash
# Counting files
numfiles=$(ls -1 | wc -l)

# Processing ls output
for file in $(ls *.txt); do
    cat "$file"
done

# Filtering files
ls -l | grep "$USER" | grep '\.txt$'
```

### Correct Code

```bash
# Counting files with array
files=(*.txt)
numfiles=${#files[@]}

# Or with find
numfiles=$(find . -maxdepth 1 -name "*.txt" | wc -l)

# Processing files with glob
for file in *.txt; do
    [[ -f "$file" ]] || continue  # Skip if no matches
    cat "$file"
done

# Filtering with find
find . -maxdepth 1 -name "*.txt" -user "$USER"
```

### Rationale

`ls` is designed for human consumption, not parsing:
- Output format varies by system and locale
- Time format changes based on age
- May hide or "clean up" special characters
- Different output when stdout is a terminal vs pipe

**Example of the problem:**

```bash
$ ls -l
-rw-r----- 1 me me 0 Feb  5 20:11 foo?bar
-rw-r----- 1 me me 0 Feb  5  2011 foo?bar
-rw-r----- 1 me me 0 Feb  5 20:11 foo?bar
```

Three files with seemingly identical names! The actual filenames contain different special characters that `ls` shows as `?`.

### Replacing ls with find

```bash
# List files
ls *.txt
# Becomes
find . -maxdepth 1 -name "*.txt"

# Or just
*.txt  # In for loops

# List recursively
ls -R
# Becomes
find .

# Only filenames (not full paths)
find . -maxdepth 1 -name "*.txt" -printf '%P\n'  # GNU find
find . -maxdepth 1 -name "*.txt" | sed 's|^\./||'  # Portable
```

### Other Alternatives

```bash
# Get file count from stat/wc
wc -c < file  # File size
stat -f %z file  # BSD
stat -c %s file  # GNU

# Use globs directly
shopt -s nullglob  # Bash: empty array if no matches
files=(*.txt)
```

---

## SC2116

**Message:** Useless echo? Instead of `cmd $(echo foo)`, just use `cmd foo`

**Severity:** Style

### Problematic Code

```bash
# Echo in command substitution
greeting=$(echo "Hello, $name")

# Nested echo
tar czf "$(echo "$(date +%F).tar.gz")" *

# Assignment with echo
value=$(echo "$var")
```

### Correct Code

```bash
# Direct assignment
greeting="Hello, $name"

# Direct command
tar czf "$(date +%F).tar.gz" *

# Direct value
value="$var"
```

### Rationale

Using `echo` just to capture its output is like mailing yourself a postcard - you already have the value!

The pattern `$(echo value)` is the same as just `value`.

### Legitimate Uses (that look wrong)

Sometimes echo has a purpose:

```bash
# Expanding globs (but use arrays instead!)
glob="*.png"
files="$(echo $glob)"  # Expands glob
# Better:
files=(*.png)

# Expanding escapes (but use printf!)
unexpanded='var\tvalue'
expanded="$(echo "$var")"  # Some shells expand \t
# Better:
expanded=$(printf '%b' "$var")
```

### Better Alternatives

```bash
# Glob expansion - use arrays
shopt -s nullglob
files=(*.png)

# Join array elements
printf '%s\n' "${files[@]}"
# Or with delimiter
IFS=:; echo "${files[*]}"; IFS=$' \t\n'

# Escape sequence expansion - use printf
printf 'Line 1\nLine 2\n'
```

---

## SC2162

**Message:** `read` without `-r` will mangle backslashes

**Severity:** Info

### Problematic Code

```bash
# Reading user input
echo "Enter path:"
read path

# Reading file
while read line; do
    echo "$line"
done < file.txt

# Reading into array
IFS=: read -a parts <<< "$PATH"
```

### Correct Code

```bash
# Always use -r
echo "Enter path:"
read -r path

# Reading file safely
while IFS= read -r line; do
    echo "$line"
done < file.txt

# Reading into array
IFS=: read -r -a parts <<< "$PATH"
```

### Rationale

Without `-r`, `read` treats backslash as an escape character:
- `\n` becomes `n` (not newline)
- `\t` becomes `t` (not tab)
- `\\` becomes `\`
- `\<space>` includes the space in the field

This is rarely what you want when reading file paths, user input, or data.

### Examples of Problems

```bash
# Without -r
echo 'C:\Users\name' | while read path; do
    echo "$path"
done
# Outputs: C:Usersname (backslashes removed!)

# With -r
echo 'C:\Users\name' | while IFS= read -r path; do
    echo "$path"
done
# Outputs: C:\Users\name (correct!)
```

### Why IFS= Too?

Even with `-r`, leading and trailing whitespace is stripped:

```bash
# Without IFS=
echo "  data  " | while read -r line; do
    echo "[$line]"
done
# Outputs: [data] (spaces gone!)

# With IFS=
echo "  data  " | while IFS= read -r line; do
    echo "[$line]"
done
# Outputs: [  data  ] (preserved!)
```

### The Safe Pattern

```bash
# Reading files: Always use IFS= read -r
while IFS= read -r line; do
    process "$line"
done < file.txt

# Reading command output
while IFS= read -r line; do
    process "$line"
done < <(command)
```

---

## SC2230

**Message:** `which` is non-standard. Use builtin `command -v` instead

**Severity:** Info (Optional check: `deprecate-which`)

### Problematic Code

```bash
# Checking if command exists
if which docker > /dev/null; then
    echo "Docker installed"
fi

# Getting command path
editor=$(which vim)
```

### Correct Code

```bash
# Check if command exists
if command -v docker > /dev/null; then
    echo "Docker installed"
fi

# Or use hash for existence check
if hash docker 2>/dev/null; then
    echo "Docker installed"
fi

# Getting command path
editor=$(command -v vim)
```

### Rationale

`which` is an external, non-standard tool that varies by system. `command -v` is:
- POSIX standard builtin
- Uses the same lookup mechanism as the shell
- Faster (no external process)
- More reliable

### Differences

```bash
# which - external command
# - Only finds executables in PATH
# - Doesn't find builtins, functions, aliases
# - Behavior varies by system

# command -v - shell builtin
# - Finds executables, builtins, functions, aliases
# - Shows what would actually run
# - POSIX standard
```

### Checking Command Existence

```bash
# Just checking if exists - use hash
if hash docker 2>/dev/null; then
    echo "Docker available"
fi

# Need path for executable - use command -v
docker_bin=$(command -v docker)

# Check multiple commands
if hash docker git make 2>/dev/null; then
    echo "All tools available"
fi
```

### Caveats

`command -v` includes builtins, aliases, and functions:

```bash
# Alias exists
alias ll='ls -la'
command -v ll  # Outputs: alias ll='ls -la'

# Function exists
myfunc() { echo "hi"; }
command -v myfunc  # Outputs: myfunc

# Builtin
command -v echo  # Outputs: echo
```

If you only want executables, use `type -P` (bash) or filter output.

---

## SC2236

**Message:** Use `-n` instead of `! -z`

**Severity:** Style

### Problematic Code

```bash
# Double negative checking if set
if [ ! -z "$JAVA_HOME" ]; then
    echo "JAVA_HOME is set"
fi

# Double negative checking if empty
if [ ! -n "$var" ]; then
    echo "var is empty"
fi
```

### Correct Code

```bash
# Positive test - has value
if [ -n "$JAVA_HOME" ]; then
    echo "JAVA_HOME is set"
fi

# Positive test - is empty
if [ -z "$var" ]; then
    echo "var is empty"
fi
```

### Rationale

Avoid double negatives for clarity:

```bash
# These are identical - choose the positive form
[ ! -z "$var" ]  # NOT is empty = has value
[ -n "$var" ]    # Has value

# These are identical - choose the positive form
[ ! -n "$var" ]  # NOT has value = is empty
[ -z "$var" ]    # Is empty
```

### Quick Reference

| Expression | Meaning | Better As |
|------------|---------|-----------|
| `[ ! -z "$var" ]` | NOT empty | `[ -n "$var" ]` |
| `[ ! -n "$var" ]` | NOT non-empty | `[ -z "$var" ]` |

### Related Operators

```bash
# String tests
-z string   # True if empty
-n string   # True if non-empty
string      # True if non-empty (same as -n)

# Examples
[ -z "" ]      # True
[ -n "text" ]  # True
[ "text" ]     # True (same as -n)
```

**Important:** Always quote variables:

```bash
[ -n "$var" ]   # Correct
[ -n $var ]     # Wrong - expands to [ -n ] if empty
```

---

## Quick Reference: Additional Common Errors

Below are additional common ShellCheck errors with brief descriptions. For detailed examples, visit the [ShellCheck Wiki](https://www.shellcheck.net/wiki/).

### Quoting and Expansion (SC2001-2099)

| Code | Issue | Quick Fix |
|------|-------|-----------|
| SC2001 | See if you can use `${variable//search/replace}` | Use parameter expansion instead of sed |
| SC2002 | Useless cat | Use `< file` or `cmd file` directly |
| SC2003 | expr is antiquated | Use `$((..))` or `${..}` |
| SC2005 | Useless echo | Remove unnecessary echo |
| SC2006 | Use `$(...)` instead of backticks | Modern syntax |
| SC2007 | Use `$((..))` instead of `$[..]` | Deprecated syntax |
| SC2013 | To read lines, use while read loop | Don't iterate over command output with for |
| SC2014 | This expands once before find runs | Quote variables in -exec |
| SC2028 | echo won't expand escape sequences | Use printf |
| SC2035 | Use `./*glob*` or `-- *glob*` | Protect filenames starting with dash |
| SC2053 | Quote rhs of = in [[ ]] | Prevent glob matching |
| SC2064 | Use single quotes | Trap expansion timing |
| SC2065 | This is interpreted as a shell file redirection | Escape < or > in tests |
| SC2066 | Since double-quoted, won't word split | Remove quotes or use array |
| SC2076 | Don't quote rhs of =~ | Regex should be unquoted |
| SC2088 | Tilde does not expand in quotes | Use $HOME |
| SC2089 | Quotes/backslashes treated literally | Use array |
| SC2090 | Quotes/backslashes not respected | Use array |

### Command Issues (SC2100-2199)

| Code | Issue | Quick Fix |
|------|-------|-----------|
| SC2103 | Use subshell to avoid cd back | `( cd dir && cmd )` |
| SC2104 | In functions, use return | Not break |
| SC2105 | break only valid in loops | Remove or fix context |
| SC2119 | Use `func "$@"` if $1 should mean script's $1 | Pass arguments |
| SC2120 | Function references arguments but none passed | Pass arguments when calling |
| SC2121 | Use `var=value` not set | Assignment syntax |
| SC2126 | Consider `grep -c` | Instead of grep \| wc |
| SC2143 | Use `grep -q` | Instead of `[ -n $(grep ..) ]` |
| SC2144 | -e doesn't work with globs | Use for loop |
| SC2145 | Argument mixes string and array | Use * or separate |
| SC2148 | Add shebang | Tips depend on target shell |
| SC2153 | Possible misspelling | Check variable name |
| SC2154 | var is referenced but not assigned | Check for typos or source file |
| SC2163 | Use export var | Not export $var |
| SC2166 | Prefer `[ p ] && [ q ]` | Instead of `[ p -a q ]` |
| SC2168 | local only valid in functions | Move or remove |
| SC2169 | In dash, ... not supported | Use bash or POSIX alternative |
| SC2170 | Invalid number for -eq | Use = for strings |
| SC2178 | Variable was array but now string | Check assignments |
| SC2179 | Use `array+=("item")` | To append to arrays |

### File Operations (SC2200-2299)

| Code | Issue | Quick Fix |
|------|-------|-----------|
| SC2185 | Some finds don't have default path | Specify `.` |
| SC2186 | tempfile is deprecated | Use mktemp |
| SC2196 | egrep is deprecated | Use `grep -E` |
| SC2197 | fgrep is deprecated | Use `grep -F` |
| SC2188 | Redirection doesn't have a command | Move to command or use true |
| SC2216 | Piping to rm | rm doesn't read stdin |
| SC2217 | Redirecting to echo | echo doesn't read stdin |
| SC2219 | Prefer `(( expr ))` | Instead of let |
| SC2220 | Invalid flags not handled | Add `*)` case |
| SC2221 | Pattern overrides later one | Check case statement |
| SC2223 | Default assignment may cause DoS | Quote in case |
| SC2224 | mv has no destination | Check arguments |
| SC2225 | cp has no destination | Check arguments |
| SC2229 | This doesn't read var | Remove $ or use ${var?} |
| SC2232 | Can't use sudo with builtins | Use `sudo sh -c` |
| SC2235 | Use `{ .. }` instead of `( .. )` | Avoid subshell |
| SC2237 | Use `[ -n .. ]` | Instead of `! [ -z .. ]` |
| SC2238 | Redirecting to/from command name | Use pipes/xargs or quote |

---

## Best Practices Summary

1. **Always quote variables**: `"$var"` not `$var`
2. **Check commands directly**: `if cmd; then` not `if [ $? -eq 0 ]; then`
3. **Use proper conditionals**: `if-then-else` not `&& ||`
4. **Handle cd failures**: `cd dir || exit`
5. **Validate dangerous operations**: `"${var:?}"` before `rm -rf`
6. **Separate declare and assign**: `local var; var=$(cmd)`
7. **Follow sourced files**: Use `# shellcheck source=path`
8. **Remove unused variables**: Or use `_` prefix for dummies
9. **Use modern tools**: `pgrep` not `ps | grep`, `find` not `ls`
10. **Read safely**: Always use `IFS= read -r`
11. **Prefer builtins**: `command -v` not `which`
12. **Avoid double negatives**: `[ -n "$var" ]` not `[ ! -z "$var" ]`
