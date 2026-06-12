Set-Location $PSScriptRoot

git rev-parse --git-dir *>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error: not a git repository."
    exit 1
}

git pull --rebase
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Done."
