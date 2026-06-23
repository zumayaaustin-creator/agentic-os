# Agentic OS Windows PowerShell installer
$ErrorActionPreference = "Stop"

Write-Host "=== Agentic OS Installer ==="
Write-Host ""

# Detect Windows using PowerShell runtime variables.
$IsWindowsHost = if ($PSVersionTable.PSEdition -eq "Desktop") { $true } else { $IsWindows }
if (-not $IsWindowsHost) {
    Write-Host "WARNING: This installer is intended for Windows PowerShell. Use ./install.sh on Linux/macOS."
} else {
    Write-Host "Detected OS: windows"
}
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"

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
            $versionOutput = & $candidate.Command @($candidate.Arguments + @("--version")) 2>&1
            if ($LASTEXITCODE -eq 0) {
                return [pscustomobject]@{
                    Command = $candidate.Command
                    Arguments = $candidate.Arguments
                    Version = ($versionOutput | Select-Object -First 1).ToString()
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
Write-Host "Python: $($Python.Version)"

# Create required directories.
New-Item -ItemType Directory -Force -Path "backups", "audit" | Out-Null

# Install Python dependencies.
Write-Host "Installing Python dependencies..."
& $PythonCommand @($PythonArgs + @("-m", "pip", "install", "-r", "requirements.txt"))
if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies." }

# Check optional CLIs.
$optionalCommands = @(
    @{ Name = "opencode"; Warning = "WARNING: opencode not found. Install via: npm install -g @opencode/cli" },
    @{ Name = "hermes"; Warning = "WARNING: Hermes Agent not found. See https://github.com/NousResearch/hermes-agent for installation instructions." },
    @{ Name = "gemini"; Warning = "WARNING: Gemini CLI not found. Install via: npm install -g @google/gemini-cli" }
)

foreach ($optional in $optionalCommands) {
    $found = Get-Command $optional.Name -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "$($optional.Name): found"
    } else {
        Write-Host $optional.Warning
    }
}

# Initialize git if not already present, matching install.sh .gitignore additions.
if (-not (Test-Path -Path ".git" -PathType Container)) {
    Write-Host "Initializing git repository..."
    git init
    if ($LASTEXITCODE -ne 0) { throw "Failed to initialize git repository." }

    if (-not (Test-Path -Path ".gitignore")) {
        New-Item -ItemType File -Path ".gitignore" | Out-Null
    }

    $gitignoreEntries = @("audit/*", "backups/*.tar.gz", "data/settings.json")
    $gitignoreContent = Get-Content -Path ".gitignore" -ErrorAction SilentlyContinue
    foreach ($entry in $gitignoreEntries) {
        if ($gitignoreContent -notcontains $entry) {
            Add-Content -Path ".gitignore" -Value $entry
        }
    }
}

Write-Host ""
Write-Host "=== Installation complete! ==="
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit data/settings.json with your API keys"
Write-Host "  2. Run .\start.ps1 to launch the dashboard"
Write-Host "  3. Open http://127.0.0.1:8080 in your browser"
