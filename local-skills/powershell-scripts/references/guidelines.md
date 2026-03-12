# PowerShell Cmdlet Development Guidelines

This guide provides comprehensive PowerShell best practices aligned with Microsoft's cmdlet development guidelines.

## Naming Conventions

### Verb-Noun Format

- Use approved PowerShell verbs (check with `Get-Verb`)
- Use singular nouns
- PascalCase for both verb and noun
- Avoid special characters and spaces

### Parameter Names

- Use PascalCase
- Choose clear, descriptive names
- Use singular form unless always multiple
- Follow PowerShell standard names (`Path`, `Name`, `Force`, etc.)

### Variable Names

- Use PascalCase for public variables
- Use camelCase for private variables
- Avoid abbreviations
- Use meaningful names

### Alias Avoidance

- Use full cmdlet names in scripts
- Avoid aliases like `gci`, `?`, `%`, `where`
- Document any custom aliases
- Use full parameter names

## Parameter Design

### Standard Parameters

- Use common parameter names (`Path`, `Name`, `Force`)
- Follow built-in cmdlet conventions
- Use aliases for specialized terms
- Document parameter purpose

### Type Selection

- Use common .NET types
- Implement proper validation
- Consider `ValidateSet` for limited options
- Enable tab completion where possible

### Switch Parameters

- Use `[switch]` for boolean flags
- Avoid `$true`/`$false` parameters
- Default to `$false` when omitted
- Use clear action names

### Validation Attributes

Common validation attributes:
- `[ValidateSet('Option1', 'Option2')]` - Limit to specific values
- `[ValidateRange(1, 100)]` - Numeric range validation
- `[ValidateNotNullOrEmpty()]` - Ensure non-null/non-empty
- `[ValidatePattern('regex')]` - Regex pattern matching
- `[ValidateScript({...})]` - Custom validation logic
- `[ValidateLength(1, 50)]` - String length validation
- `[ValidateCount(1, 10)]` - Array count validation

## Pipeline and Output

### Pipeline Input

- Use `ValueFromPipeline` for direct object input
- Use `ValueFromPipelineByPropertyName` for property mapping
- Implement Begin/Process/End blocks for pipeline handling
- Document pipeline input requirements

### Output Objects

- Return rich objects, not formatted text
- Use `PSCustomObject` for structured data
- Avoid `Write-Host` for data output
- Enable downstream cmdlet processing

### Pipeline Streaming

- Output one object at a time
- Use `process` block for streaming
- Avoid collecting large arrays
- Enable immediate processing

### PassThru Pattern

- Default to no output for action cmdlets
- Implement `-PassThru` switch for object return
- Return modified/created object with `-PassThru`
- Use verbose/warning for status updates

Example:

```powershell
function Update-ResourceStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [string]$Name,

        [Parameter(Mandatory)]
        [ValidateSet('Active', 'Inactive', 'Maintenance')]
        [string]$Status,

        [Parameter()]
        [switch]$PassThru
    )

    begin {
        Write-Verbose 'Starting resource status update process'
        $timestamp = Get-Date
    }

    process {
        Write-Verbose "Processing resource: $Name"

        $resource = [PSCustomObject]@{
            Name        = $Name
            Status      = $Status
            LastUpdated = $timestamp
            UpdatedBy   = $env:USERNAME
        }

        if ($PassThru.IsPresent) {
            Write-Output $resource
        }
    }

    end {
        Write-Verbose 'Resource status update process completed'
    }
}
```

## Error Handling and Safety

### ShouldProcess Implementation

- Use `[CmdletBinding(SupportsShouldProcess = $true)]`
- Set appropriate `ConfirmImpact` level:
  - `Low`: Minimal risk (default)
  - `Medium`: Moderate risk (typical for modifications)
  - `High`: Significant risk (deletions, critical changes)
- Call `$PSCmdlet.ShouldProcess()` for system changes
- Use `ShouldContinue()` for additional confirmations

### Message Streams

- `Write-Verbose`: Operational details (visible with `-Verbose`)
- `Write-Warning`: Warning conditions
- `Write-Error`: Non-terminating errors
- `throw`: Terminating errors
- Avoid `Write-Host` except for user interface text

### Error Handling Pattern

In advanced functions with `[CmdletBinding()]`:
- Prefer `$PSCmdlet.WriteError()` over `Write-Error`
- Prefer `$PSCmdlet.ThrowTerminatingError()` over `throw`
- Construct proper ErrorRecord objects with category, target, and exception details

Example:

```powershell
function Remove-UserAccount {
    [CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateNotNullOrEmpty()]
        [string]$Username,

        [Parameter()]
        [switch]$Force
    )

    begin {
        Write-Verbose 'Starting user account removal process'
        $ErrorActionPreference = 'Stop'
    }

    process {
        try {
            # Validation
            if (-not (Test-UserExists -Username $Username)) {
                $errorRecord = [System.Management.Automation.ErrorRecord]::new(
                    [System.Exception]::new("User account '$Username' not found"),
                    'UserNotFound',
                    [System.Management.Automation.ErrorCategory]::ObjectNotFound,
                    $Username
                )
                $PSCmdlet.WriteError($errorRecord)
                return
            }

            # Confirmation
            $shouldProcessMessage = "Remove user account '$Username'"
            if ($Force -or $PSCmdlet.ShouldProcess($Username, $shouldProcessMessage)) {
                Write-Verbose "Removing user account: $Username"

                Remove-ADUser -Identity $Username -ErrorAction Stop
                Write-Warning "User account '$Username' has been removed"
            }
        } catch [Microsoft.ActiveDirectory.Management.ADException] {
            $errorRecord = [System.Management.Automation.ErrorRecord]::new(
                $_.Exception,
                'ActiveDirectoryError',
                [System.Management.Automation.ErrorCategory]::NotSpecified,
                $Username
            )
            $PSCmdlet.ThrowTerminatingError($errorRecord)
        } catch {
            $errorRecord = [System.Management.Automation.ErrorRecord]::new(
                $_.Exception,
                'UnexpectedError',
                [System.Management.Automation.ErrorCategory]::NotSpecified,
                $Username
            )
            $PSCmdlet.ThrowTerminatingError($errorRecord)
        }
    }

    end {
        Write-Verbose 'User account removal process completed'
    }
}
```

### Non-Interactive Design

- Accept input via parameters
- Avoid `Read-Host` in scripts
- Support automation scenarios
- Document all required inputs

## Documentation and Style

### Comment-Based Help

Include comment-based help for all public-facing functions. Place inside the function with a `<# ... #>` block containing:

- `.SYNOPSIS`: Brief description
- `.DESCRIPTION`: Detailed explanation
- `.PARAMETER`: Description for each parameter
- `.EXAMPLE`: Practical usage examples (multiple recommended)
- `.OUTPUTS`: Type of output returned
- `.NOTES`: Additional information

Example:

```powershell
function Get-UserProfile {
    <#
    .SYNOPSIS
        Retrieves user profile information

    .DESCRIPTION
        Gets detailed user profile information from Active Directory or local system.
        Supports pipeline input and filtering by profile type.

    .PARAMETER Username
        The username to retrieve profile information for

    .PARAMETER ProfileType
        The type of profile information to retrieve. Valid values are Basic or Detailed.

    .EXAMPLE
        Get-UserProfile -Username "jdoe"
        Retrieves basic profile information for user jdoe

    .EXAMPLE
        "jdoe", "asmith" | Get-UserProfile -ProfileType Detailed
        Retrieves detailed profile information for multiple users via pipeline

    .OUTPUTS
        System.Management.Automation.PSCustomObject
        Returns custom object with user profile properties

    .NOTES
        Requires appropriate permissions to query Active Directory
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [string]$Username,

        [Parameter()]
        [ValidateSet('Basic', 'Detailed')]
        [string]$ProfileType = 'Basic'
    )

    process {
        # Logic here
    }
}
```

### Consistent Formatting

- Follow consistent PowerShell style
- Use proper indentation (4 spaces recommended)
- Opening braces on same line as statement
- Closing braces on new line
- Use line breaks after pipeline operators
- PascalCase for function and parameter names
- Avoid unnecessary whitespace

### Avoid Aliases in Scripts

Use full cmdlet names and parameters:
- Use `Where-Object` instead of `?` or `where`
- Use `ForEach-Object` instead of `%` or `foreach`
- Use `Get-ChildItem` instead of `ls`, `dir`, or `gci`
- Use `Select-Object` instead of `select`
- Use full parameter names instead of abbreviations

Aliases are acceptable for interactive shell use but should not appear in scripts.

## Full Example: Complete Cmdlet Pattern

```powershell
function New-Resource {
    <#
    .SYNOPSIS
        Creates a new resource in the specified environment

    .DESCRIPTION
        Creates a new resource with the specified name and environment settings.
        Supports WhatIf and Confirm for safe execution.

    .PARAMETER Name
        The name of the resource to create

    .PARAMETER Environment
        The environment to create the resource in. Valid values are Development or Production.
        Defaults to Development.

    .PARAMETER PassThru
        Returns the created resource object

    .EXAMPLE
        New-Resource -Name "WebApp1" -Environment Production
        Creates a new resource named WebApp1 in the Production environment

    .EXAMPLE
        "App1", "App2" | New-Resource -PassThru
        Creates multiple resources via pipeline and returns the created objects

    .OUTPUTS
        None by default. System.Management.Automation.PSCustomObject when using -PassThru

    .NOTES
        Requires appropriate permissions to create resources
    #>
    [CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
    param(
        [Parameter(Mandatory = $true,
            ValueFromPipeline = $true,
            ValueFromPipelineByPropertyName = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Name,

        [Parameter()]
        [ValidateSet('Development', 'Production')]
        [string]$Environment = 'Development',

        [Parameter()]
        [switch]$PassThru
    )

    begin {
        Write-Verbose 'Starting resource creation process'
        $created = 0
    }

    process {
        try {
            if ($PSCmdlet.ShouldProcess($Name, "Create new resource in $Environment environment")) {
                Write-Verbose "Creating resource: $Name"

                # Resource creation logic here
                $resource = [PSCustomObject]@{
                    PSTypeName  = 'Custom.Resource'
                    Name        = $Name
                    Environment = $Environment
                    Created     = Get-Date
                    CreatedBy   = $env:USERNAME
                }

                $created++

                if ($PassThru.IsPresent) {
                    Write-Output $resource
                }
            }
        } catch {
            $errorRecord = [System.Management.Automation.ErrorRecord]::new(
                $_.Exception,
                'ResourceCreationFailed',
                [System.Management.Automation.ErrorCategory]::NotSpecified,
                $Name
            )
            $PSCmdlet.WriteError($errorRecord)
        }
    }

    end {
        Write-Verbose "Completed resource creation process. Created $created resource(s)."
    }
}
```

## ErrorRecord Categories

Common error categories to use:

- `NotSpecified`: General error
- `OpenError`: Error opening file/resource
- `CloseError`: Error closing file/resource
- `DeviceError`: Device error
- `DeadlockDetected`: Deadlock detected
- `InvalidArgument`: Invalid argument
- `InvalidData`: Invalid data
- `InvalidOperation`: Invalid operation
- `InvalidResult`: Invalid result
- `InvalidType`: Invalid type
- `MetadataError`: Metadata error
- `NotImplemented`: Not implemented
- `NotInstalled`: Not installed
- `ObjectNotFound`: Object not found
- `OperationStopped`: Operation stopped
- `OperationTimeout`: Operation timeout
- `SyntaxError`: Syntax error
- `ParserError`: Parser error
- `PermissionDenied`: Permission denied
- `ResourceBusy`: Resource busy
- `ResourceExists`: Resource exists
- `ResourceUnavailable`: Resource unavailable
- `ReadError`: Read error
- `WriteError`: Write error
- `FromStdErr`: From standard error
- `SecurityError`: Security error

## Best Practices Summary

✅ **Do:**
- Use `[CmdletBinding()]` for advanced functions
- Implement Begin/Process/End blocks for pipeline functions
- Return rich objects with `PSCustomObject`
- Use `SupportsShouldProcess` for state-changing operations
- Include comprehensive comment-based help
- Use full cmdlet names (no aliases)
- Implement proper error handling with ErrorRecord objects
- Use `Write-Verbose` for operational details
- Validate parameters with appropriate attributes
- Support pipeline input where appropriate

❌ **Don't:**
- Use aliases in scripts
- Use `Write-Host` for data output
- Use `Read-Host` in automation scripts
- Return formatted text instead of objects
- Skip error handling
- Forget comment-based help
- Use generic `throw` instead of proper ErrorRecord
- Ignore pipeline patterns
- Hard-code values that should be parameters
