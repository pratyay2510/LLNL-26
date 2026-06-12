Set-Location $PSScriptRoot

git rev-parse --git-dir *>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error: not a git repository."
    exit 1
}

git add -A

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes to commit."
} else {
    do {
        $message = Read-Host "Commit message"
    } while ([string]::IsNullOrWhiteSpace($message))

    git commit -m $message
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

git push
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Done."
