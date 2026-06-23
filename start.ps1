# Agentic OS Windows PowerShell dashboard launcher
$ErrorActionPreference = "Stop"

Write-Host "Starting Agentic OS Dashboard..."
Write-Host ""

if (-not (Test-Path -Path "server.py" -PathType Leaf)) {
    throw "server.py not found. Are you in the right directory?"
}

function Find-Python {
    $candidates = @(
        @{ Command = "py"; Arguments = @("-3.10") },
        @{ Command = "py"; Arguments = @("-3") },
        @{ Command = "python"; Arguments = @() }
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if (-not $command) { continue }

        try {
            & $candidate.Command @($candidate.Arguments + @("--version")) *> $null
            if ($LASTEXITCODE -eq 0) {
                return [pscustomobject]@{
                    Command = $candidate.Command
                    Arguments = $candidate.Arguments
                }
            }
        } catch {
            continue
        }
    }

    throw "Python 3.10+ required. Install from https://www.python.org/downloads/windows/ and enable the Python launcher."
}

$Python = Find-Python
$PythonCommand = $Python.Command
$PythonArgs = $Python.Arguments

Write-Host "Installing/verifying Python dependencies..."
& $PythonCommand @($PythonArgs + @("-m", "pip", "install", "-r", "requirements.txt"))
if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies." }

$Port = 8080
if (Test-Path -Path "data/settings.json" -PathType Leaf) {
    try {
        $Settings = Get-Content -Path "data/settings.json" -Raw | ConvertFrom-Json
        if ($Settings.dashboard.port) {
            $Port = [int]$Settings.dashboard.port
        }
    } catch {
        Write-Host "WARNING: Could not read data/settings.json; using default port 8080."
        $Port = 8080
    }
}

Write-Host "Dashboard: http://127.0.0.1:$Port"
Write-Host "Press Ctrl+C to stop"
Write-Host ""

& $PythonCommand @($PythonArgs + @("server.py", "--port", $Port))
