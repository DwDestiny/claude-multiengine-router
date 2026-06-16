# Input: user-scoped Claude router install plus Python. Output: backup then removal through the portable uninstaller.
# Pos: Windows PowerShell thin wrapper for uninstall.py.

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$UninstallArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    if ($env:PYTHON_BIN) {
        return @{ Command = $env:PYTHON_BIN; PrefixArgs = @() }
    }

    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) {
        return @{ Command = $python3.Source; PrefixArgs = @() }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{ Command = $python.Source; PrefixArgs = @() }
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @{ Command = $py.Source; PrefixArgs = @("-3") }
    }

    throw "[claude-multiengine-router] Python 3 is required. Install Python 3 or set PYTHON_BIN."
}

$resolved = Resolve-PythonCommand
$scriptPath = Join-Path $PSScriptRoot "uninstall.py"
& $resolved["Command"] @($resolved["PrefixArgs"]) $scriptPath @UninstallArgs
exit $LASTEXITCODE
