#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Generates PowerShell function template with best practices

.DESCRIPTION
    Creates a PowerShell function template following Microsoft cmdlet development guidelines.
    Includes proper parameter blocks, comment-based help, and pipeline support options.

.PARAMETER FunctionName
    Name of the function in Verb-Noun format (e.g., Get-UserData)

.PARAMETER IncludePipeline
    Include pipeline support (ValueFromPipeline)

.PARAMETER IncludeShouldProcess
    Include ShouldProcess support for confirmation

.PARAMETER OutputPath
    Path where the generated function should be saved. If not specified, outputs to console.

.EXAMPLE
    .\generate_function.ps1 -FunctionName "Get-UserData"
    Generates basic function template

.EXAMPLE
    .\generate_function.ps1 -FunctionName "Update-Configuration" -IncludePipeline -IncludeShouldProcess
    Generates function with pipeline and ShouldProcess support

.EXAMPLE
    .\generate_function.ps1 -FunctionName "New-Resource" -OutputPath .\NewResource.ps1
    Generates function and saves to file

.OUTPUTS
    Function template as string or file

.NOTES
    Use Get-Verb to see approved PowerShell verbs
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[A-Z][a-z]+-[A-Z][a-zA-Z]+$')]
    [string]$FunctionName,

    [Parameter()]
    [switch]$IncludePipeline,

    [Parameter()]
    [switch]$IncludeShouldProcess,

    [Parameter()]
    [string]$OutputPath
)

begin {
    Write-Verbose "Generating function template for: $FunctionName"
}

process {
    # Build CmdletBinding attributes
    $cmdletBinding = '[CmdletBinding('
    if ($IncludeShouldProcess) {
        $cmdletBinding += 'SupportsShouldProcess = $true, ConfirmImpact = ''Medium'''
    }
    $cmdletBinding += ')]'

    # Build parameter attributes
    $paramAttributes = '[Parameter(Mandatory)'
    if ($IncludePipeline) {
        $paramAttributes += ",`n        ValueFromPipeline = `$true,`n        ValueFromPipelineByPropertyName = `$true"
    }
    $paramAttributes += ']'

    # Build function template
    $template = @"
function $FunctionName {
    <#
    .SYNOPSIS
        Brief description of what the function does

    .DESCRIPTION
        Detailed explanation of the function's purpose and behavior

    .PARAMETER Name
        Description of the Name parameter

    .EXAMPLE
        $FunctionName -Name "example"
        Description of this example
"@

    if ($IncludePipeline) {
        $template += @"


    .EXAMPLE
        "item1", "item2" | $FunctionName
        Description of pipeline example
"@
    }

    $template += @"


    .OUTPUTS
        System.Management.Automation.PSCustomObject
        Description of output

    .NOTES
        Additional notes or requirements
    #>
    $cmdletBinding
    param(
        $paramAttributes
        [ValidateNotNullOrEmpty()]
        [string]`$Name
"@

    if ($IncludeShouldProcess) {
        $template += @"
,

        [Parameter()]
        [switch]`$PassThru
"@
    }

    $template += @"

    )

    begin {
        Write-Verbose 'Starting $FunctionName process'
    }

    process {
"@

    if ($IncludeShouldProcess) {
        $template += @"

        try {
            if (`$PSCmdlet.ShouldProcess(`$Name, 'Process item')) {
                Write-Verbose "Processing: `$Name"

                # TODO: Add main logic here

                `$result = [PSCustomObject]@{
                    Name      = `$Name
                    Processed = Get-Date
                }

                if (`$PassThru.IsPresent) {
                    Write-Output `$result
                }
            }
        } catch {
            `$errorRecord = [System.Management.Automation.ErrorRecord]::new(
                `$_.Exception,
                'ProcessingFailed',
                [System.Management.Automation.ErrorCategory]::NotSpecified,
                `$Name
            )
            `$PSCmdlet.ThrowTerminatingError(`$errorRecord)
        }
"@
    } else {
        $template += @"

        Write-Verbose "Processing: `$Name"

        # TODO: Add main logic here

        `$result = [PSCustomObject]@{
            Name      = `$Name
            Processed = Get-Date
        }

        Write-Output `$result
"@
    }

    $template += @"

    }

    end {
        Write-Verbose '$FunctionName process completed'
    }
}
"@

    # Output or save template
    if ($OutputPath) {
        $template | Set-Content -Path $OutputPath -Encoding UTF8
        Write-Output "✅ Function template saved to: $OutputPath"
    } else {
        Write-Output $template
    }
}

end {
    Write-Verbose "Template generation completed"
}
