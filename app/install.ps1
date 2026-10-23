# One-time Candor setup for Windows: run by double-clicking "Install Candor.cmd" in the Candor folder.
# Installs what is missing, adds Desktop and Start-menu shortcuts, then opens Candor.
# Safe to run again (for example after downloading a newer version). Adapted from Qualia's installer.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

function Step($number, $text) { Write-Host ''; Write-Host "[$number/5] $text" -ForegroundColor Cyan }
function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
function Winget-Install($id) {
    & winget install --id $id --exact --source winget --accept-package-agreements --accept-source-agreements
    $code = $LASTEXITCODE
    Refresh-Path
    return $code -eq 0
}
function Find-Python {
    # The real python.exe of a Python 3.10 or newer, or $null. The Microsoft Store "python"
    # placeholder prints nothing here, so it is skipped.
    $candidates = @('python', 'py', "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe", "$env:ProgramFiles\Python313\python.exe")
    foreach ($candidate in $candidates) {
        if (-not (Have $candidate)) { continue }
        $extra = @()
        if ($candidate -eq 'py') { $extra = @('-3') }
        try {
            $exe = & $candidate @extra -c "import sys; print(sys.executable if sys.version_info >= (3, 10) else '')"
        } catch { continue }
        if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path "$exe".Trim())) { return "$exe".Trim() }
    }
    return $null
}
function Ask($question) {
    $answer = Read-Host "$question [Y/n]"
    return ($answer -eq '' -or $answer -match '^[Yy]')
}
function Run-Setup($py) {
    # harness_setup.py installs the Python packages and the job-board tools and ends with a
    # table of what works. It exits non-zero while something is missing; that is reported, not fatal.
    & $py -u harness_setup.py --yes --quick | Tee-Object -Variable lines | Out-Host
    return $lines
}

try {
    Write-Host 'Setting up Candor. The first time takes 10 to 30 minutes, most of it waiting for downloads.'
    Write-Host 'Later runs are quicker.'

    Step 1 'Checking Python (the language Candor is written in)'
    $py = Find-Python
    if (-not $py) {
        if (-not (Have 'winget')) { throw 'Python 3.10 or newer is missing. Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then run Install Candor again.' }
        Write-Host 'Installing Python with winget. Windows may ask "Do you want to allow this app to make changes?": click Yes.'
        Winget-Install 'Python.Python.3.13' | Out-Null
        $py = Find-Python
        if (-not $py) { throw 'Python was installed but cannot be found yet. Restart your computer, then run Install Candor again.' }
    }
    Write-Host "Python is ready ($py)."

    Step 2 'Installing what the job search needs (Python packages, job-board tools, document tools)'
    $lines = Run-Setup $py
    $tools = [ordered]@{
        'Node'     = @('OpenJS.NodeJS.LTS', 'Node.js (needed by the job-board tools)')
        'Bun'      = @('Oven-sh.Bun', 'Bun (runs the job-board searches)')
        'lualatex' = @('MiKTeX.MiKTeX', 'MiKTeX (builds your CV and cover letter PDFs; a large download)')
        'xelatex'  = @('MiKTeX.MiKTeX', 'MiKTeX (builds your CV and cover letter PDFs; a large download)')
        'poppler'  = @('oschwartz10612.Poppler', 'Poppler (reads PDFs to check page count and layout)')
    }
    $offered = @{}
    $installed = $false
    foreach ($name in $tools.Keys) {
        $id, $label = $tools[$name]
        if ($offered[$id]) { continue }
        if (-not ($lines | Where-Object { $_ -match "^\s*$name\b:?\s+MISSING" })) { continue }
        $offered[$id] = $true
        if (-not (Have 'winget')) { Write-Warning "$label is missing, and winget is not available to install it. The list above says how to get it."; continue }
        if (-not (Ask "Install $label now?")) { continue }
        Write-Host "Installing $label. Windows may ask for permission: click Yes."
        if (Winget-Install $id) { $installed = $true } else { Write-Warning "$label did not install. You can try again later by running Install Candor again." }
    }
    if ($installed) {
        Write-Host ''
        Write-Host 'Checking again now that the new tools are in place...'
        $lines = Run-Setup $py
    }
    if ($lines | Where-Object { $_ -match 'required item\(s\) need attention' }) {
        Write-Warning 'Some parts are still missing (listed above). Candor will open, but searching or building documents may not work until they are fixed. Run Install Candor again after fixing them, or restart your computer if something was just installed.'
    }

    Step 3 'Checking for an AI assistant (Claude Code or Codex)'
    $engines = @('claude', 'codex') | Where-Object { Have $_ }
    if ($engines) {
        Write-Host "Found: $($engines -join ', '). Candor uses your own subscription to it."
    } else {
        Write-Host 'Candor needs one AI assistant on this computer. You have neither yet. Pick one:' -ForegroundColor Yellow
        Write-Host '  - Codex (with a ChatGPT plan): go to chatgpt.com/codex, install Codex, and sign in.'
        Write-Host '  - Claude Code (with a Claude plan): install it from claude.com/code, or, if you have Node,'
        Write-Host '    type this in a terminal: npm install -g @anthropic-ai/claude-code'
        Write-Host 'Candor''s setup screen walks you through this too, so you can carry on now.'
    }

    Step 4 'Creating the Candor shortcuts'
    $pythonw = Join-Path (Split-Path -Parent $py) 'pythonw.exe'
    if (-not (Test-Path $pythonw)) { $pythonw = $py }
    $icon = Join-Path $root 'app\static\candor.ico'
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
        $shortcut = $shell.CreateShortcut((Join-Path $folder 'Candor.lnk'))
        $shortcut.TargetPath = $pythonw
        $shortcut.Arguments = '-m app.launcher'
        $shortcut.WorkingDirectory = $root
        if (Test-Path $icon) { $shortcut.IconLocation = $icon }
        $shortcut.Description = 'Candor - job applications you can defend'
        $shortcut.Save()
    }
    Write-Host 'Added Candor to your Desktop and Start menu.'

    Step 5 'Opening Candor'
    Start-Process -FilePath $pythonw -ArgumentList '-m', 'app.launcher' -WorkingDirectory $root
    Write-Host ''
    Write-Host 'All done. Candor is opening now. Next time, double-click the Candor icon on your Desktop.' -ForegroundColor Green
    Write-Host 'Closing the Candor window stops it. Your CV, applications and notes stay in this folder, on this computer.'
} catch {
    Write-Host ''
    Write-Host "Setup stopped: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Fix the problem above, then double-click Install Candor again. Nothing of yours was changed.' -ForegroundColor Red
    exit 1
}
