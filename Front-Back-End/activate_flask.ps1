<#
.SYNOPSIS
    Activates a Python virtual environment in Windows.

.DESCRIPTION
    This script lists the virtual environments in a specified directory and prompts the user to select one to activate.

.NOTES
    Author: Gemini
    Date: 2024-05-08
#>
param (
    [Parameter(Mandatory = $false)]
    [string]$EnvDir = "D:\ORZ\Python-Environments"  # Default environment directory
)

# Check if the environment directory exists
if (-not (Test-Path -Path $EnvDir -PathType 'Container')) {
    Write-Error "Error: Directory '$EnvDir' does not exist!"
    Write-Host "If you don't have the environment, then enter these commands:"
    Write-Host "1) mkdir '$EnvDir'"
    Write-Host "2) python -m venv '$EnvDir\flaskenv'"
    Write-Host "3) Run this script again."
    Write-Host "4) pip install -r requirements.txt"
    return
}

Write-Host "If you don't have the environment, then enter these commands:"
Write-Host "1) python -m venv '$EnvDir\Your-Env-Name'"
    Write-Host "3) Run this script again."
Write-Host "4) pip install -r requirements.txt (if it exists)"

Write-Host "Available Virtual Environments:"
Write-Host "--------------------------------"

# Get a list of directories within the environment directory
$envs = Get-ChildItem -Path $EnvDir -Directory

# Display each virtual environment with a number
for ($i = 0; $i -lt $envs.Count; $i++) { #changed < to -lt
    Write-Host "$($i + 1). $($envs[$i].Name)"
}

Write-Host "--------------------------------"

# Prompt the user to select an environment
$envNumber = Read-Host "Select the environment number to activate"

# Attempt to activate the selected environment
if ($envNumber -match '^\d+$' -and $envNumber -ge 1 -and $envNumber -le $envs.Count) {
    $selectedEnv = $envs[$envNumber - 1].FullName
    $activatePath = Join-Path -Path $selectedEnv -ChildPath "Scripts\activate.ps1"

    if (Test-Path -Path $activatePath) {
        Write-Host "Activating environment: $($envs[$envNumber - 1].Name)"
        # Use . to source the activate.ps1 script.  This is the key to making it work!
        . $activatePath
    }
    else {
        Write-Error "Error: Activation script not found in the selected environment."
    }
}
else {
    Write-Error "Invalid selection. Please try again."
}
