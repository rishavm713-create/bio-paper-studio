# Bio Paper Studio - one-step installer for Windows 10/11.
# Run in PowerShell:  irm https://raw.githubusercontent.com/rishavm713-create/bio-paper-studio/main/install.ps1 | iex
# Or double-click "Install Bio Paper Studio (Windows).bat" in the downloaded folder.
$ErrorActionPreference = "Stop"
$Repo = "rishavm713-create/bio-paper-studio"
$Skill = Join-Path $env:USERPROFILE ".claude\skills\paper-studio"
function Say($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User") + ";" + (Join-Path $env:USERPROFILE ".local\bin") }
function Find-Python {
    foreach ($c in @(@("py", "-3"), @("python"))) {
        try { & $c[0] $c[1..9] -c "import sys; assert sys.version_info >= (3, 8)" 2>$null; if ($LASTEXITCODE -eq 0) { return $c } } catch {}
    }
    return $null
}

Say "1/5 Python"
$Py = Find-Python
if (-not $Py) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements
        Refresh-Path; $Py = Find-Python
    }
    if (-not $Py) { throw "Python 3 is missing. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run this again." }
}
Write-Host "Python found: $($Py -join ' ')"

Say "2/5 Claude Code"
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    Refresh-Path
}
if (Get-Command claude -ErrorAction SilentlyContinue) { Write-Host "Claude Code found." } else { Write-Warning "Claude Code did not install. Get it from https://claude.com/claude-code" }

Say "3/5 App files"
$Src = $PSScriptRoot
if (-not $Src -or -not (Test-Path (Join-Path $Src "skill\bio-paper\render.py"))) {
    $Tmp = Join-Path $env:TEMP "bio-paper-studio"
    Remove-Item $Tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory $Tmp | Out-Null
    Invoke-WebRequest "https://github.com/$Repo/archive/refs/heads/main.zip" -OutFile "$Tmp\main.zip" -UseBasicParsing
    Expand-Archive "$Tmp\main.zip" $Tmp -Force
    $Src = Join-Path $Tmp "bio-paper-studio-main"
}
New-Item -ItemType Directory -Force $Skill, (Join-Path $env:USERPROFILE "BioPapers") | Out-Null
Copy-Item (Join-Path $Src "skill\bio-paper\*") $Skill -Recurse -Force          # keeps your own extra references
$Refs = Join-Path $Skill "references"
New-Item -ItemType Directory -Force $Refs | Out-Null
Get-ChildItem (Join-Path $Src "references") | Where-Object { $_.Name -notin "ncert", "papers" } |   # these come from the official sites (step 4)
    Copy-Item -Destination $Refs -Recurse -Force
$Note = Join-Path $Src "note.txt"
if (Test-Path $Note) { $Cfg = Join-Path $env:USERPROFILE ".config\bio-paper"; New-Item -ItemType Directory -Force $Cfg | Out-Null; Copy-Item $Note $Cfg -Force }

Say "4/5 References (downloading from the official websites in the background)"
$Get = Join-Path $Skill "references\get_references.py"
$PArgs = @($Py[1..9]) + @("`"$Get`"")
Start-Process -WindowStyle Hidden -FilePath $Py[0] -ArgumentList $PArgs -RedirectStandardOutput (Join-Path $Skill "references\download-log.txt")

Say "5/5 Desktop shortcut"
$Desk = [Environment]::GetFolderPath("Desktop")
Copy-Item (Join-Path $Src "Bio Paper Studio.bat") (Join-Path $Desk "Paper Studio.bat") -Force

Write-Host "`nDone." -ForegroundColor Green
Write-Host "First time only: open PowerShell, type  claude  and sign in with your Claude account."
Write-Host "Then double-click 'Paper Studio' on the Desktop."
