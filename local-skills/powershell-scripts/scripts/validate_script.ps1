#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Validates PowerShell script quality and best practices compliance

.DESCRIPTION
    Analyzes PowerShell scripts for common issues, anti-patterns, and style violations.
    Uses PSScriptAnalyzer if available, otherwise performs basic validation.

.PARAMETER Path
    Path to the PowerShell script file to validate

.PARAMETER Severity
    Minimum severity level to report. Valid values: Error, Warning, Information

.EXAMPLE
    .\validate_script.ps1 -Path .\MyScript.ps1

.EXAMPLE
    .\validate_script.ps1 -Path .\MyScript.ps1 -Severity Error

.OUTPUTS
    Validation results with issues found

.NOTES
    Install PSScriptAnalyzer for comprehensive analysis:
    Install-Module -Name PSScriptAnalyzer -Scope CurrentUser
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, ValueFromPipeline)]
    [ValidateScript({ Test-Path $_ -PathType Leaf })]
    [string]$Path,

    [Parameter()]
    [ValidateSet('Error', 'Warning', 'Information')]
    [string]$Severity = 'Warning'
)

begin {
    Write-Verbose "Starting PowerShell script validation"

    # Check if PSScriptAnalyzer is available
    $hasPSScriptAnalyzer = $null -ne (Get-Module -ListAvailable -Name PSScriptAnalyzer)
}

process {
    $resolvedPath = Resolve-Path -Path $Path
    Write-Verbose "Validating script: $resolvedPath"

    if ($hasPSScriptAnalyzer) {
        Write-Verbose "Using PSScriptAnalyzer for comprehensive analysis"
        Import-Module PSScriptAnalyzer -ErrorAction Stop

        $results = Invoke-ScriptAnalyzer -Path $resolvedPath -Severity $Severity

        if ($results) {
            Write-Warning "Found $($results.Count) issue(s) in $resolvedPath"
            $results | Format-Table -Property Severity, Line, RuleName, Message -AutoSize
        } else {
            Write-Output "✅ No issues found in $resolvedPath"
        }
    } else {
        Write-Warning "PSScriptAnalyzer not found. Performing basic validation only."
        Write-Host "Install with: Install-Module -Name PSScriptAnalyzer -Scope CurrentUser"

        # Basic validation
        $issues = @()
        $content = Get-Content -Path $resolvedPath -Raw

        # Check for common aliases
        $aliases = @('gci', 'ls', 'dir', 'where', 'foreach', 'select', '%', '?')
        foreach ($alias in $aliases) {
            if ($content -match "\b$alias\b") {
                $issues += "Found alias: $alias (use full cmdlet name)"
            }
        }

        # Check for Write-Host in functions
        if ($content -match 'function\s+\w+-\w+[\s\S]*?Write-Host') {
            $issues += "Found Write-Host in function (consider Write-Output, Write-Verbose, or Write-Warning)"
        }

        if ($issues) {
            Write-Warning "Found $($issues.Count) potential issue(s):"
            $issues | ForEach-Object { Write-Output "  - $_" }
        } else {
            Write-Output "✅ Basic validation passed"
        }
    }
}

end {
    Write-Verbose "Validation completed"
}
