---
name: powershell-scripts
description: Expert PowerShell scripting assistant. Use when writing, reviewing, or refactoring PowerShell scripts (.ps1) and modules (.psm1). Provides cmdlet development best practices, pipeline patterns, error handling, and proper parameter design following Microsoft guidelines.
---

# PowerShell Scripts

Expert guidance for writing idiomatic, maintainable PowerShell scripts following Microsoft cmdlet development guidelines.

## When to Use This Skill

- Writing or refactoring `.ps1` scripts or `.psm1` modules
- Implementing PowerShell functions with proper parameter design
- Adding pipeline support to cmdlets
- Implementing proper error handling and ShouldProcess
- Creating comment-based help documentation
- Converting aliases to full cmdlet names
- Troubleshooting PowerShell-specific issues

## Quick Start

### Basic Function Template

```powershell
function Verb-Noun {
    <#
    .SYNOPSIS
        Brief description
    .DESCRIPTION
        Detailed explanation
    .PARAMETER Name
        Parameter description
    .EXAMPLE
        Verb-Noun -Name "example"
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    process {
        Write-Verbose "Processing: $Name"
        # Logic here
    }
}
```

### Pipeline-Enabled Function

```powershell
function Update-Item {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory, ValueFromPipeline, ValueFromPipelineByPropertyName)]
        [string]$Name,

        [Parameter()]
        [switch]$PassThru
    )

    begin {
        Write-Verbose "Starting update process"
    }

    process {
        if ($PSCmdlet.ShouldProcess($Name, 'Update item')) {
            # Update logic
            if ($PassThru) {
                Write-Output $result
            }
        }
    }

    end {
        Write-Verbose "Update process completed"
    }
}
```

## Core Principles

### Naming Conventions

- **Functions:** Use approved Verb-Noun format (check `Get-Verb`)
- **Parameters:** PascalCase, singular form, descriptive
- **Variables:** PascalCase for public, camelCase for private
- **Avoid Aliases:** Use full cmdlet names in scripts

### Parameter Design

- Use `[CmdletBinding()]` for advanced functions
- Add proper validation attributes (`[ValidateSet()]`, `[ValidateNotNullOrEmpty()]`)
- Use `[switch]` for boolean flags
- Support common parameters (`-Verbose`, `-ErrorAction`, etc.)
- Enable pipeline input with `ValueFromPipeline` or `ValueFromPipelineByPropertyName`

### Pipeline Patterns

- Implement Begin/Process/End blocks for pipeline functions
- Stream objects one at a time in `process` block
- Use `-PassThru` pattern for action cmdlets (default to no output)
- Return rich objects, not formatted text

### Error Handling

- Use `SupportsShouldProcess` for functions that modify system state
- Set appropriate `ConfirmImpact` level (Low, Medium, High)
- Use `Write-Verbose` for operational details
- Use `Write-Warning` for warnings
- Use `$PSCmdlet.WriteError()` for non-terminating errors
- Use `$PSCmdlet.ThrowTerminatingError()` for terminating errors
- Create proper ErrorRecord objects with category and target

### Output and Messaging

- `Write-Verbose`: Operational details (visible with `-Verbose`)
- `Write-Warning`: Warning conditions
- `Write-Error` or `$PSCmdlet.WriteError()`: Non-terminating errors
- `throw` or `$PSCmdlet.ThrowTerminatingError()`: Terminating errors
- `Write-Output`: Data output (avoid `Write-Host` for data)
- `Write-Host`: User interface text only

## Common Patterns

### ShouldProcess with Error Handling

```powershell
function Remove-Resource {
    [CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
    param(
        [Parameter(Mandatory, ValueFromPipeline)]
        [ValidateNotNullOrEmpty()]
        [string]$Name,

        [Parameter()]
        [switch]$Force
    )

    begin {
        Write-Verbose "Starting removal process"
        $ErrorActionPreference = 'Stop'
    }

    process {
        try {
            if ($Force -or $PSCmdlet.ShouldProcess($Name, 'Remove resource')) {
                Write-Verbose "Removing: $Name"
                # Removal logic
                Write-Warning "Resource '$Name' removed"
            }
        } catch {
            $errorRecord = [System.Management.Automation.ErrorRecord]::new(
                $_.Exception,
                'RemovalFailed',
                [System.Management.Automation.ErrorCategory]::NotSpecified,
                $Name
            )
            $PSCmdlet.ThrowTerminatingError($errorRecord)
        }
    }

    end {
        Write-Verbose "Removal process completed"
    }
}
```

### Validated Parameters with Tab Completion

```powershell
function Set-Configuration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('Dev', 'Test', 'Prod')]
        [string]$Environment,

        [Parameter()]
        [ValidateRange(1, 100)]
        [int]$Timeout = 30,

        [Parameter()]
        [ValidateNotNullOrEmpty()]
        [string[]]$Tags
    )

    process {
        Write-Verbose "Environment: $Environment, Timeout: $Timeout"
        # Configuration logic
    }
}
```

## Comment-Based Help

Include for all public functions:

```powershell
<#
.SYNOPSIS
    Brief one-line description

.DESCRIPTION
    Detailed explanation of what the function does

.PARAMETER Name
    Description of the Name parameter

.PARAMETER Force
    Description of the Force switch

.EXAMPLE
    Verb-Noun -Name "example"
    Description of this example

.EXAMPLE
    Get-Item | Verb-Noun
    Description of pipeline example

.OUTPUTS
    System.Management.Automation.PSCustomObject
    Description of output object

.NOTES
    Additional notes, version info, or requirements
#>
```

## Anti-Patterns to Avoid

❌ Using aliases in scripts (`gci`, `?`, `%`, `where`)
❌ Using `Write-Host` for data output
❌ Not implementing pipeline support for collection operations
❌ Missing `[CmdletBinding()]` for advanced functions
❌ Using `Read-Host` in non-interactive scripts
❌ Not including comment-based help
❌ Using generic `throw` instead of proper ErrorRecord objects
❌ Returning formatted text instead of objects

## References

For comprehensive guidelines, see [references/guidelines.md](references/guidelines.md) which contains the complete PowerShell cmdlet development best practices.

### Resources
- [generate_function.ps1](scripts/generate_function.ps1): Generates PowerShell function template with best practices. Use `Get-Help generate_function.ps1 -Full` for usage details.
- [validate_script.ps1](scripts/validate_script.ps1): Validates PowerShell script against best practices and provides feedback. Use `Get-Help validate_script.ps1 -Full` for usage details.
