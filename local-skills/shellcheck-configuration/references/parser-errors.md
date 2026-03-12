# ShellCheck Parser Error Codes Reference

This reference documents common parser errors (SC1000-1999 range) that indicate syntax problems in shell scripts.

## Table of Contents

- [SC1004: Backslash+linefeed in single quotes](#sc1004)
- [SC1007: Space after = in assignment](#sc1007)
- [SC1036: Invalid parenthesis](#sc1036)
- [SC1078: Unclosed double quote](#sc1078)
- [SC1083: Literal braces](#sc1083)
- [SC1009: Unterminated string](#sc1009)

---

## SC1004

**Message:** This backslash+linefeed is literal. Break outside single quotes if you just want to break the line

**Severity:** Info (Retired after v0.7.2)

### Problematic Code

```bash
# Backslash in single quotes doesn't continue line
var='This is long \
piece of text'

# This creates a string with literal \ and newline
echo 'Line 1 \
Line 2'
```

### Correct Code

```bash
# Break line by closing and reopening quotes
var='This is a long '\
'piece of text'

# Or use double quotes if you want escaped content
var="This is a long \
piece of text"

# For multi-line with actual newlines, no backslash needed
var='This is a multi-line string
with an embedded linefeed'
```

### Rationale

In single quotes, **everything** is literal:
- `\n` is literally backslash-n, not newline
- `\t` is literally backslash-t, not tab
- `\` followed by newline is literally backslash-newline

Only double quotes and unquoted strings allow line continuation with backslash.

### Comparison

```bash
# Single quotes - all literal
echo 'foo\nbar'      # Outputs: foo\nbar
echo 'foo\
bar'                  # Outputs: foo\ (newline) bar

# Double quotes - escapes work
echo "foo\nbar"      # Outputs: foo\nbar (literal \n, not newline in bash)
echo "foo\
bar"                  # Outputs: foobar (line continuation)

# Unquoted - escapes work
echo foo\
bar                   # Outputs: foobar (line continuation)
```

### Multi-line Strings

```bash
# Single quotes - actual newlines preserved
message='Error: Something went wrong
Please try again
Check the logs for details'

# Heredoc - for large blocks
cat <<'EOF'
This is a multi-line
heredoc with literal
content preserved
EOF

# Array with multiple lines
files=(
    'file1.txt'
    'file2.txt'
    'file3.txt'
)
```

### When Literal Backslash-Newline Is Intended

For sed, awk, or other tools that need literal backslash-newline:

```bash
# Disable warning when intentional
# shellcheck disable=SC1004
sed 's/foo\
/bar/'
```

---

## SC1007

**Message:** Remove space after `=` if trying to assign a value (or for empty string, use `var=""`)

**Severity:** Warning

### Problematic Code

```bash
# Space after = runs command with empty env var
LANGUAGE= nl         # Runs 'nl' command with LANGUAGE=""

# Looks like assignment but isn't
DEBUG= true          # Runs 'true' command with DEBUG=""

# Common mistake
PATH= /usr/local/bin # Runs '/usr/local/bin' with PATH=""
```

### Correct Code

```bash
# To assign value - no spaces
LANGUAGE=nl

# To run command with empty environment variable
LANGUAGE='' nl
# or
LANGUAGE="" nl

# Multiple env vars with command
DEBUG=1 VERBOSE=1 ./script.sh

# Assignment in script
PATH=/usr/local/bin
```

### Rationale

Shell syntax is:
- `VAR=value` - Assignment
- `VAR=value command` - Set VAR for command only
- `VAR= command` - Set VAR to empty string for command

The space makes a huge difference:

```bash
# This assigns "nl" to LANGUAGE
LANGUAGE=nl

# This runs nl command with LANGUAGE set to empty
LANGUAGE= nl

# Real-world example - different behavior!
PATH=/bin command         # Sets PATH and runs command
PATH= /bin/command        # Runs /bin/command with empty PATH (likely fails!)
```

### Common Confusion

```bash
# WRONG - runs 'echo' with empty DEBUG
DEBUG= echo "Starting"

# RIGHT - assigns empty string to DEBUG
DEBUG=""
echo "Starting"

# Or assign and use on one line
DEBUG="" echo "Starting"  # Still wrong! Runs echo with DEBUG=""

# Correct way to assign and use
DEBUG=""
echo "Starting: $DEBUG"
```

### Empty Assignments

```bash
# Be explicit for empty strings (except IFS)
var=""          # Preferred - clear intent
var=            # ShellCheck warns

# Exception: IFS with read is idiomatic
IFS= read -r line    # OK - common pattern
IFS="" read -r line  # Also works but less common

# Environment variables for commands
LANG='' command      # Clear - empty LANG
LANG= command        # ShellCheck warns, but common
```

### Environment Variable Patterns

```bash
# Set multiple variables for one command
CC=gcc CXX=g++ CFLAGS="-O2" make

# Empty variables to unset for command
HOME='' command              # Command sees HOME as empty
PATH='' env | grep PATH      # Shows PATH is empty for env

# Combining with existing values
PATH="$HOME/bin:$PATH" command
```

### Related Codes
- SC2086: Quote to prevent word splitting
- SC1068: Don't put spaces around =

---

## SC1036

**Message:** `(` is invalid here. Did you forget to escape it?

**Severity:** Error

### Problematic Code

```bash
# Unquoted literal parentheses
echo (foo) bar

# Missing $ for command substitution
echo Today is (date)

# Trying to call function with arguments like other languages
process_data(item, 42)

# Arithmetic without $$
result = (5 + 3)
```

### Correct Code

```bash
# Quote literal parentheses
echo "(foo) bar"

# Use $ for command substitution
echo "Today is $(date)"

# Shell functions don't use parentheses for calls
process_data item 42

# Use $(( )) for arithmetic
result=$((5 + 3))

# Or use subshell
( cd /tmp && make )
```

### Rationale

Parentheses in shell have specific meanings:
- `( cmd )` - Subshell (must be a complete command)
- `$(cmd)` - Command substitution
- `(( expr ))` - Arithmetic expression (bash/ksh)
- `func()` - Function definition only

They cannot appear randomly in unquoted contexts.

### Common Mistakes

```bash
# 1. Test results - use quotes
echo (PASS) Test succeeded     # ERROR
echo "(PASS) Test succeeded"   # OK

# 2. Function calls - shell doesn't work like C/Python
calculate(x, y)                # ERROR
calculate "$x" "$y"            # OK

# 3. Tuples/arrays - shell has different syntax
pair=(first, second)           # ERROR
pair=(first second)            # OK - array

# 4. Math - need $((
value = (10 + 20)              # ERROR
value=$((10 + 20))             # OK
```

### Subshells vs Command Substitution

```bash
# Subshell - runs in separate process, no output capture
( cd /tmp; ls )     # Changes dir in subshell only

# Command substitution - captures output
files=$(cd /tmp; ls)  # Saves output to variable

# Combining both
result=$( (cd /tmp && make) )  # Subshell inside substitution
```

### Arrays and Parentheses

```bash
# Array assignment - parentheses are special
array=(one two three)          # OK - array syntax
array=( one two three )        # OK - spaces don't matter
array = (one two three)        # ERROR - space before =

# Associative arrays
declare -A map=([key]="value") # OK
map[key]=value                 # OK
map(key)=value                 # ERROR
```

### Bash Eval Exception

Some commands accept assignment-like syntax with parentheses:

```bash
# These work in bash (quirk)
eval foo=(bar)
export foo=(bar)

# But prefer quoting to avoid relying on quirks
eval "foo=(bar)"      # Better - works reliably
export "foo=(bar)"    # Better - explicit
```

### Related Codes
- SC1088: Invalid use of parentheses
- SC1073: Couldn't parse expression

---

## SC1078

**Message:** Did you forget to close this double-quoted string?

**Severity:** Error

### Problematic Code

```bash
# Missing closing quote
echo "Hello world

# Nested quotes incorrectly
echo "She said "hello" to me"

# Multiline with missing quote
message="This is a long
error message that continues
# Script continues here but in string!
```

### Correct Code

```bash
# Close the quote
echo "Hello world"

# Escape nested quotes
echo "She said \"hello\" to me"

# Or use single quotes inside double
echo "She said 'hello' to me"

# Multiline strings work with quotes
message="This is a long
error message that continues
on multiple lines"

# Heredoc for complex multiline
cat <<EOF
This is a complex
multi-line message
EOF
```

### Rationale

Unclosed quotes cause:
- Entire rest of file treated as string
- Syntax errors in unexpected places
- Commands not executing
- Difficult-to-diagnose issues

### Finding Unclosed Quotes

```bash
# Symptoms:
# - ShellCheck shows errors on many lines
# - Syntax highlighting looks wrong
# - Commands appear inside strings

# Check for:
echo "text
     ^-- Missing closing quote

echo "text that ends but starts again "text
                                       ^-- Started new string

echo "nested "quotes" problem"
              ^-- Should be escaped
```

### Escaping Quotes

```bash
# Backslash escaping in double quotes
echo "He said \"hi\""

# Mix quote types
echo "Don't use contractions"      # Single quote inside double
echo 'He said "hello"'              # Double quote inside single

# For complex cases, use heredoc
cat <<'EOF'
She said "I won't be able to make it"
The file is in ~/Documents
Path: $HOME/bin
EOF
```

### Multiline Quoted Strings

```bash
# Valid multiline in double quotes
text="Line 1
Line 2
Line 3"

# Valid multiline in single quotes
text='Line 1
Line 2
Line 3'

# Continued lines (no newline in result)
text="This is a long \
line that continues"

# Heredoc for readability
read -r -d '' text <<'EOF'
This is a multiline
text block with
preserved formatting
EOF
```

### Common Patterns

```bash
# SQL queries
query="
SELECT *
FROM users
WHERE name = 'John'
"

# JSON (be careful with nesting)
json="{\"name\": \"$username\", \"age\": $age}"

# HTML/XML
html="<div class=\"container\">
  <p>Hello $name</p>
</div>"

# Better: use heredoc with proper quoting
cat <<EOF
<div class="container">
  <p>Hello $name</p>
</div>
EOF
```

---

## SC1083

**Message:** This `{`/`}` is literal. Check if `;` is missing or quote the expression

**Severity:** Error

### Problematic Code

```bash
# Missing semicolon before }
function deploy() {
    cd /var/www
    git pull
}  # Missing ; before }

# Literal braces in wrong context
echo {foo}

# Brace expansion without comma or range
files={file1,file2}  # Looks like expansion but needs assignment
```

### Correct Code

```bash
# Add semicolon or newline
function deploy() {
    cd /var/www
    git pull
}  # OK - newline counts

function deploy() { cd /var/www; git pull; }  # OK - semicolons

# Quote literal braces
echo "{foo}"

# Proper brace expansion
echo {1..5}        # Expands to: 1 2 3 4 5
echo {a,b,c}       # Expands to: a b c

# For variables, use array
files=(file1 file2)
```

### Rationale

Braces have special meaning in shell:
- `{ cmd; }` - Command grouping (needs `;` or newline before `}`)
- `{1..10}` - Brace expansion (range)
- `{a,b,c}` - Brace expansion (alternatives)
- `${var}` - Variable expansion

Literal braces must be quoted.

### Command Grouping

```bash
# Grouping commands (current shell)
{ cmd1; cmd2; }              # OK - semicolons
{
  cmd1
  cmd2
}                             # OK - newlines

{ cmd1; cmd2 }               # ERROR - missing ; before }
{ cmd1 cmd2; }               # ERROR - missing ; between commands

# Subshell (separate process)
( cmd1; cmd2 )               # OK - semicolons or newlines work
```

### Brace Expansion

```bash
# Ranges
echo {1..10}                 # 1 2 3 4 5 6 7 8 9 10
echo {a..z}                  # a b c d ... z
echo {00..10}                # 00 01 02 ... 10

# Alternatives
echo {foo,bar,baz}           # foo bar baz
cp file.txt{,.bak}           # Expands to: cp file.txt file.txt.bak

# Combinations
echo {a,b}{1,2}              # a1 a2 b1 b2
mkdir -p dir/{src,bin,doc}   # Creates 3 directories

# Nested
echo {{a,b},{c,d}}           # a b c d
```

### Literal Braces

```bash
# Quote when you want literal braces
echo "{foo}"                 # Outputs: {foo}
echo '{bar}'                 # Outputs: {bar}

# In regex or patterns
grep "pattern {1,3}" file    # Match 1-3 occurrences

# In JSON
json='{"key": "value"}'      # Single quotes preserve literal

# Mixed
echo "Values: {a,b,c}"       # Outputs: Values: {a,b,c} (quoted, so literal)
echo Values: {a,b,c}         # Outputs: Values: a b c (unquoted, expands)
```

### Common Errors

```bash
# 1. Missing semicolon in function
foo() {
    echo "bar"
}  # ERROR - missing semicolon

foo() {
    echo "bar";
}  # OK

# 2. Wrong brace style
foo()
{      # OK in bash
    echo "bar"
}

foo() {
    echo "bar" }  # ERROR - } should be on newline or after ;

# 3. Literal braces in command
find . -name {*.txt}         # ERROR
find . -name "*.txt"         # OK
find . -name \*.txt          # OK
```

---

## SC1009

**Message:** The mentioned parser error was in ...

**Severity:** Error

### Problematic Code

```bash
# Unterminated if
if [ -f "$file" ]
then
    cat "$file"
# Missing fi

# Unterminated for
for i in *.txt
do
    cat "$i"
# Missing done

# Unterminated string
echo "Hello
cat file.txt  # Still in string!
```

### Correct Code

```bash
# Complete if statement
if [ -f "$file" ]; then
    cat "$file"
fi

# Complete for loop
for i in *.txt; do
    cat "$i"
done

# Close string
echo "Hello"
cat file.txt
```

### Rationale

Shell requires matching keywords:
- `if` ... `then` ... `fi`
- `for` ... `do` ... `done`
- `while` ... `do` ... `done`
- `case` ... `esac`
- `{` ... `}`

Missing closing keywords cause parser errors.

### Common Mismatches

```bash
# 1. Missing fi
if condition; then
    command
# Error: unexpected end of file, expecting 'fi'

# 2. Missing done
for i in list; do
    command
# Error: unexpected end of file, expecting 'done'

# 3. Wrong terminator
if condition; then
    command
done  # ERROR - should be 'fi'

# 4. Missing esac
case $var in
    pattern) command ;;
# ERROR - should end with 'esac'
```

### Nested Structures

```bash
# Properly nested
if condition1; then
    if condition2; then
        command1
    fi
    command2
fi

# Common mistakes with nesting
if condition1; then
    if condition2; then
        command1
    # Missing fi for inner if
    command2
fi  # This closes outer if, but inner is unclosed!
```

### Finding Missing Terminators

```bash
# Tips for finding the problem:
# 1. Check indentation - should show structure
# 2. Count opening vs closing keywords
# 3. ShellCheck tells you which line opened the block
# 4. Many editors highlight matching keywords

# Use consistent style:
if test; then
    commands
fi  # Always align 'fi' with 'if'

for var in list; do
    commands
done  # Always align 'done' with 'for'
```

### All Block Structures

```bash
# if-then-fi
if test; then
    commands
fi

# if-then-else-fi
if test; then
    commands1
else
    commands2
fi

# if-then-elif-fi
if test1; then
    commands1
elif test2; then
    commands2
else
    commands3
fi

# for-do-done
for var in list; do
    commands
done

# while-do-done
while test; do
    commands
done

# until-do-done
until test; do
    commands
done

# case-esac
case $var in
    pattern1) commands1 ;;
    pattern2) commands2 ;;
esac

# function with braces
func() {
    commands
}

# Command grouping
{
    commands
}
```

---

## SC1020

**Message:** You need a space before the ] or ]]

**Severity:** Error

### Problematic Code

```bash
# Missing space before closing bracket
if [ "$STUFF" = ""]]; then
    echo "matched"
fi

# Also affects test command
if test -f file]; then
    echo "exists"
fi
```

### Correct Code

```bash
# Proper spacing around brackets
if [ "$STUFF" = "" ]; then
    echo "matched"
fi

# Space before closing bracket
if test -f file ]; then
    echo "exists"
fi
```

### Rationale

Shells are whitespace-sensitive. The `[` command requires spaces around all its arguments, including the closing `]`. Without proper spacing, the shell may interpret `]` as part of the previous argument or fail to recognize it as the closing bracket.

### Examples

```bash
# ❌ Bad - Multiple spacing issues
if ["$var"="value"]; then
    echo "bad"
fi

# ✅ Good - Proper spacing throughout
if [ "$var" = "value" ]; then
    echo "good"
fi
```

### Exceptions

None.

### Related Codes

- [SC1035](#sc1035) - Missing space after `!`
- [SC1069](#sc1069) - Missing space before `[`

---

## SC1035

**Message:** You need a space here

**Severity:** Error

### Problematic Code

```bash
# Missing space after ! negation
if ![-z "$foo" ]; then
    echo "not empty"
fi

# Missing space in compound test
if [ -f file]&&[ -r file]; then
    echo "exists and readable"
fi
```

### Correct Code

```bash
# Proper space after negation
if ! [ -z "$foo" ]; then
    echo "not empty"
fi

# Spaces around operators
if [ -f file ] && [ -r file ]; then
    echo "exists and readable"
fi
```

### Rationale

Shells require whitespace to separate tokens. Missing spaces can cause the shell to misinterpret commands, treating multiple tokens as a single argument. ShellCheck identifies exactly where spacing is needed.

### Examples

```bash
# ❌ Bad - Various spacing issues
if ![ -d /tmp]||[ -w /tmp]; then echo "ok"; fi

# ✅ Good - Consistent spacing
if ! [ -d /tmp ] || [ -w /tmp ]; then
    echo "ok"
fi
```

### Exceptions

ShellCheck doesn't understand Bash History Expansion (`!!`, `!$`), which uses `!` without spaces. These are rarely used in scripts and can be ignored in `.bashrc` files.

### Related Codes

- [SC1020](#sc1020) - Missing space before `]`
- [SC1069](#sc1069) - Missing space before `[`

---

## SC1068

**Message:** Don't put spaces around the = in assignments

**Severity:** Error (Retired in v0.7.2)

### Problematic Code

```bash
# Spaces around equals sign
foo = 42

# Also wrong with quotes
name = "John Doe"
```

### Correct Code

```bash
# No spaces in assignments
foo=42

# Proper assignment syntax
name="John Doe"
```

### Rationale

Shells are space-sensitive. `foo=42` is an assignment, but `foo = 42` is a command named `foo` with arguments `=` and `42`. This is a common mistake from users familiar with languages that allow spaces around `=`.

### Examples

```bash
# ❌ Bad - Treated as command with args
count = 10      # Runs command 'count' with args '=' '10'
path = /tmp     # Runs command 'path' with args '=' '/tmp'

# ✅ Good - Proper assignments
count=10
path=/tmp
```

### Exceptions

If you genuinely want to run a command with `=` as an argument, quote it:
```bash
foo "=" 42  # Intentionally running command 'foo'
```

### Related Codes

- [SC1007](#sc1007) - Space after `=` in assignment

---

## SC1069

**Message:** You need a space before the [

**Severity:** Error

### Problematic Code

```bash
# No space between keyword and bracket
if[ -e file ]; then
    echo "exists"
fi

# Also affects while loops
while[ "$count" -gt 0 ]; do
    echo "$count"
    ((count--))
done
```

### Correct Code

```bash
# Space before opening bracket
if [ -e file ]; then
    echo "exists"
fi

# Proper spacing in while loop
while [ "$count" -gt 0 ]; do
    echo "$count"
    ((count--))
done
```

### Rationale

Keywords like `if`, `while`, and `until` are separate from the `[` test command. A space is required to separate them. Without it, the shell looks for a command literally named `if[` or `while[`.

### Examples

```bash
# ❌ Bad - Various missing spaces
if[-f "$file"]; then echo "found"; fi
until[-z "$var"]; do read var; done

# ✅ Good - Consistent spacing
if [ -f "$file" ]; then echo "found"; fi
until [ -z "$var" ]; do read var; done
```

### Exceptions

None.

### Related Codes

- [SC1020](#sc1020) - Missing space before `]`
- [SC1035](#sc1035) - Missing space after `!`

---

## SC1072

**Message:** Unexpected ..

**Severity:** Error

### Problematic Code

```bash
# Incomplete shellcheck directive
# shellcheck disable
echo "This won't be properly disabled"

# Directive in problematic location (known bug)
if true; then
    # shellcheck disable=SC2086
    echo $var
fi
```

### Correct Code

```bash
# Complete directive
# shellcheck disable=all
echo "Properly disabled"

# Move directive before if block
# shellcheck disable=SC2086
if true; then
    echo $var
fi
```

### Rationale

ShellCheck directives must be complete and properly formatted. An incomplete directive like `# shellcheck disable` without specifying what to disable causes parser errors. Additionally, placing directives inside `then` clauses can trigger this error due to a known bug.

### Examples

```bash
# ❌ Bad - Incomplete directives
# shellcheck disable
# shellcheck enable

# ✅ Good - Proper directives
# shellcheck disable=SC2086,SC2034
# shellcheck disable=all
```

### Exceptions

This error may appear on otherwise valid code when directives are in `then` clauses. Move the directive to the top of the containing block.

### Related Codes

- [SC1073](#sc1073) - Couldn't parse this structure

---

## SC1077

**Message:** For command expansion, the tick should slant left (` vs ´)

**Severity:** Error

### Problematic Code

```bash
# Using forward/acute accent instead of backtick
echo "Username is ´whoami´"

# Mixed tick types
result=´ls -l`
```

### Correct Code

```bash
# Use $() - preferred modern syntax
echo "Username is $(whoami)"

# Or backticks (deprecated but valid)
echo "Username is `whoami`"

# Consistent modern syntax
result=$(ls -l)
```

### Rationale

Bash distinguishes between backticks (grave accent `` ` ``), forward ticks (acute accent `´`), and apostrophes (`'`). Only backticks start command expansions. Forward ticks are literal characters. ShellCheck helps catch this common font-related mistake.

### Examples

```bash
# ❌ Bad - Using wrong tick characters
output=´date´
files=´find . -name "*.sh"´

# ✅ Good - Modern command substitution
output=$(date)
files=$(find . -name "*.sh")
```

### Exceptions

For literal forward ticks (fancy quotation marks), use single quotes:
```bash
echo '``Proprietary software is an injustice.´´ - RMS'
```

### Related Codes

- [SC2006](common-errors.md#sc2006) - Use `$(..)` instead of deprecated backticks

---

## SC1079

**Message:** This is actually an end quote, but due to next char it looks suspect

**Severity:** Warning

### Problematic Code

```bash
# Quote followed by suspicious character
echo "hello"world

# Confusing quote placement
var="value"extra
```

### Correct Code

```bash
# Proper string concatenation
echo "hello" "world"
# Or
echo "helloworld"

# Clear variable assignment
var="valueextra"
# Or separate
var="value"
extra="data"
```

### Rationale

When a closing quote is immediately followed by certain characters, it can indicate a quoting mistake or unclear intent. ShellCheck flags these to prevent subtle bugs.

### Examples

```bash
# ❌ Bad - Ambiguous quoting
path="/usr/local"bin
command="ls"-la

# ✅ Good - Clear intent
path="/usr/local/bin"
command="ls -la"
```

### Exceptions

None - if the code is intentional, the warning helps document unusual patterns.

### Related Codes

- [SC1078](#sc1078) - Unclosed double quote

---

## SC1086

**Message:** Don't use $ on the iterator name in for loops

**Severity:** Error

### Problematic Code

```bash
# Dollar sign on loop variable
for $var in *.txt; do
    echo "$var"
done

# Also wrong with arrays
for $item in "${array[@]}"; do
    process "$item"
done
```

### Correct Code

```bash
# Loop variable without $
for var in *.txt; do
    echo "$var"
done

# Proper array iteration
for item in "${array[@]}"; do
    process "$item"
done
```

### Rationale

The `for` loop expects the variable's *name*, not its value. Using `$var` tries to expand the (likely non-existent) variable first, then use that value as the loop variable name. The variable cannot be specified indirectly in `for` loops.

### Examples

```bash
# ❌ Bad - Dollar signs on loop variables
for $file in /tmp/*; do cat "$file"; done
for $i in {1..10}; do echo "$i"; done

# ✅ Good - Plain variable names
for file in /tmp/*; do cat "$file"; done
for i in {1..10}; do echo "$i"; done
```

### Exceptions

None.

### Related Codes

- [SC1007](#sc1007) - Space after = in assignment

---

## SC1089

**Message:** Parsing stopped here. Is this keyword correctly matched up?

**Severity:** Error

### Problematic Code

```bash
# Extra closing keyword
if true; then
    echo "hello"
fi
fi  # Extra fi

# Missing opening but has closing
done  # No corresponding while/for

# Caused by bad quoting
var="foo
if [[ $var = "bar ]]; then  # Quote spans if statement!
    echo true
fi
```

### Correct Code

```bash
# Properly matched keywords
if true; then
    echo "hello"
fi

# Complete loop structure
for file in *; do
    echo "$file"
done

# Fixed quoting
var="foo"
if [[ $var = "bar" ]]; then
    echo true
fi
```

### Rationale

This error indicates mismatched structural keywords - too many closing keywords (`fi`, `done`, `esac`) or keywords without their openers. Often caused by deleting code but leaving terminators, or by quotes spanning structural elements.

### Examples

```bash
# ❌ Bad - Multiple structural issues
while read line
    echo "$line"
done
done  # Extra done

if [ -f file ]
then
  cat file
# Missing fi

# ✅ Good - Balanced structure
while read line; do
    echo "$line"
done

if [ -f file ]; then
    cat file
fi
```

### Exceptions

None.

### Related Codes

- [SC1073](#sc1073) - Couldn't parse this structure
- [SC1009](#sc1009) - Unterminated string

---

## Quick Reference: All Parser Error Codes

### Quoting and String Errors (SC1000-1050)

| Code | Message | Severity |
|------|---------|----------|
| SC1001 | This \c will be a regular 'c' in this context | Info |
| SC1003 | Want to escape a single quote? echo 'This is how it'"'"'s done' | Info |
| SC1004 | Backslash+linefeed is literal. Break outside quotes | Info |
| SC1007 | Remove space after = or quote to make literal | Error |
| SC1008 | Unrecognized shebang. Specify #!/bin/sh or similar | Error |
| SC1009 | Unterminated quoted string | Error |
| SC1010 | Use semicolon or linefeed before 'then' | Error |
| SC1011 | Unmatched or missing $() or `..` | Error |
| SC1012 | \t is just literal 't' here. For tab, use "$(printf '\t')" | Info |
| SC1014 | Use 'if cmd; then ..' to check exit code, or 'if [[ $(cmd) == .. ]]' | Error |
| SC1015 | Note that A && B || C is not if-then-else. C may run when A is true | Info |
| SC1016 | Trying to declare parameters? Don't. Use () and refer to params as $1, $2 | Error |
| SC1017 | Literal carriage return. Run script through tr -d '\r' | Error |
| SC1018 | Literal tab character | Info |
| SC1019 | Expected this to be an argument to the unary operator | Error |
| SC1020 | You need a space before the ] or ]] | Error |
| SC1026 | If grouping expressions inside [[..]], use ( .. ) | Error |
| SC1028 | In [..] you have to escape ( and ). Use [[ .. ]] instead | Error |
| SC1029 | In `[[..]]` you shouldn't escape ( or ) | Error |
| SC1035 | You need a space here | Error |
| SC1036 | '(' is invalid here. Did you forget to escape it? | Error |
| SC1037 | Braces are required for positional parameters > 9 | Error |
| SC1038 | Shells are space sensitive. Use '< <(cmd)', not '<<(cmd)' | Error |
| SC1039 | Remove indentation before end token or use <<- | Error |
| SC1040 | When using <<-, you can only indent with tabs | Error |
| SC1041 | Found 'eof' further down, but not on separate line | Error |
| SC1042 | Close matches include 'EOF' | Info |
| SC1044 | Couldn't find end token EOF in here document | Error |

### Bracket and Parenthesis Errors (SC1050-1090)

| Code | Message | Severity |
|------|---------|----------|
| SC1051 | Semicolons directly after then/else are not allowed | Error |
| SC1052 | Semicolons directly after case labels are not allowed | Error |
| SC1054 | You need a space after '((' | Error |
| SC1065 | Trying to declare parameters? Don't. Use () and refer to $1.. | Error |
| SC1068 | Don't put spaces around the = in assignments | Error |
| SC1069 | You need a space before the [ | Error |
| SC1071 | ShellCheck only supports sh/bash/dash/ksh scripts | Error |
| SC1072 | Unexpected .. Fix to allow more checks | Error |
| SC1073 | Couldn't parse this (thing). Fix to allow more checks | Error |
| SC1077 | For command expansion, tick should slant left (` vs ´) | Error |
| SC1078 | Did you forget to close this double quoted string? | Error |
| SC1079 | This is an end quote, but due to next char looks suspect | Warning |
| SC1083 | This {/} is literal. Check expression (missing ;/\n?) | Error |
| SC1084 | Use #!, not just ! | Error |
| SC1086 | Don't use $ on the iterator name in for loops | Error |
| SC1087 | Use braces when expanding arrays, e.g. ${array[idx]} | Error |
| SC1088 | Parsing stopped here. Invalid use of parentheses? | Error |
| SC1089 | Parsing stopped here. Is this keyword correctly matched? | Error |
| SC1090 | Can't follow non-constant source. Use directive to specify | Info |
| SC1091 | Not following: (file) was not specified as input | Info |

### Command and Function Errors (SC1100-1150)

| Code | Message | Severity |
|------|---------|----------|
| SC1097 | Unexpected ==. For assignment, use =. For comparison, use [ .. ] | Error |
| SC1098 | Quote/escape special characters when using eval | Warning |
| SC1099 | Unexpected (( after function definition. Missing space? | Error |
| SC1100 | ShellCheck intentionally doesn't support arithmetic for loops | Info |
| SC1101 | Delete trailing spaces after \ to break line | Error |
| SC1102 | Shells disambiguate (( differently. Use $(( for math | Warning |
| SC1104 | Use #!, not just #. | Error |
| SC1105 | Shells disambiguate (( differently. Use < <( for process sub | Warning |
| SC1107 | This directive is unknown. It will be ignored | Warning |
| SC1108 | Missing space before ( | Error |
| SC1109 | This is an unquoted HTML entity. Replace with char/escape | Warning |
| SC1110 | This is a unicode quote. Delete and retype it | Warning |
| SC1111 | This is a unicode quote. Delete and retype it | Warning |
| SC1112 | This is a unicode quote. Delete and retype it | Warning |
| SC1113 | Use #!, not just #sh | Error |
| SC1114 | Remove leading spaces before the shebang | Error |
| SC1115 | Remove spaces between # and ! in shebang | Error |
| SC1116 | Missing $ on parameter expansion | Warning |
| SC1117 | Backslash is literal in "\n". Prefer "\\n" | Info |
| SC1118 | Delete whitespace after \ | Error |
| SC1119 | Add a linefeed between end token and terminating ')' | Error |
| SC1120 | No such command. Use builtin or command to invoke | Error |
| SC1121 | Add ;/& terminators (or quote to make literal) | Error |
| SC1122 | Nothing allowed after end token. To continue, add space | Error |
| SC1123 | ShellCheck directives only valid before first command | Warning |
| SC1124 | ShellCheck directives only valid before first command | Warning |
| SC1126 | Place shellcheck directives before commands, not after | Warning |
| SC1127 | Was this intended as a comment? Use # in sh | Warning |
| SC1128 | Expected 'do'. Loops in functions need space before {/() | Error |
| SC1129 | Unexpected token. This keyword not valid in this context | Error |
| SC1130 | Unexpected blank line after here-doc token | Error |
| SC1131 | Use 'elif' to start another condition | Error |
| SC1132 | Missing space before '(' | Error |
| SC1133 | Unexpected start of line. If breaking lines, add \ | Error |

### Advanced Parsing Errors (SC1134+)

| Code | Message | Severity |
|------|---------|----------|
| SC1134 | Newline here will nest commands. Use ; or & instead | Warning |

---

## Best Practices for Avoiding Parser Errors

1. **Use consistent indentation** - Makes structure visible
2. **One statement per line** - Easier to read and debug
3. **Use shellcheck regularly** - Catches issues early
4. **Test incrementally** - Add code in small chunks
5. **Match opening/closing** - Align `if`/`fi`, `do`/`done`, etc.
6. **Quote strings** - Prevents many subtle errors
7. **Use editor highlighting** - Shows mismatched quotes/brackets
8. **Comment complex sections** - Helps track structure
9. **Respect whitespace rules** - Spaces matter in shell syntax
10. **Prefer modern syntax** - Use `$()` over backticks, `[[` over `[`
11. **Validate directives** - Ensure shellcheck comments are complete
