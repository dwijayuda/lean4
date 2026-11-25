param(
    [Parameter(Mandatory=$true)][string]$SourceDir
)
$ErrorActionPreference = 'Stop'
function RunGit {
    & git @args
    if ($LASTEXITCODE -ne 0) { throw "Git command failed: $args" }
}
$source = (Resolve-Path -LiteralPath $SourceDir).Path
Push-Location $PSScriptRoot
try {
    $current = (git branch --show-current)
    if ($LASTEXITCODE -ne 0 -or $current -ne 'kdkmp-bendahara-2026') { throw 'Checkout kdkmp-bendahara-2026 first.' }
    $dirty = git status --porcelain
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Working tree must be clean before starting.' }
    $rows = @()
    foreach ($index in @('indeks-uk03-06-dan-kompetensi.md','indeks-uk07-12-dan-pajak.md')) {
        foreach ($line in Get-Content -LiteralPath $index -Encoding UTF8) {
            if ($line -match '^\|\s*(.+?\.(?:pptx|pdf))\s*\|.*?([a-f0-9]{64})') {
                $name = $Matches[1]
                $hash = $Matches[2]
                $path = Join-Path $source $name
                if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing source: $name" }
                if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hash) { throw "SHA256 mismatch: $name" }
                $rows += [pscustomobject]@{Name=$name; Path=$path; Hash=$hash}
            }
        }
    }
    if ($rows.Count -ne 21) { throw "Expected 21 originals; found $($rows.Count)." }
    New-Item -ItemType Directory -Force -Path 'sumber-asli' | Out-Null
    foreach ($row in $rows) {
        Copy-Item -LiteralPath $row.Path -Destination (Join-Path 'sumber-asli' $row.Name)
    }
    RunGit add -- sumber-asli
    RunGit commit -m 'Archive 21 original KDKMP training files (SHA256 verified)'
    RunGit push origin HEAD:refs/heads/kdkmp-bendahara-2026
} finally {
    Pop-Location
}
