<#
.SYNOPSIS
  Quick 20‑minute bcrypt basic checks

.DESCRIPTION
  Runs a series of short, targeted attacks against your bcrypt file:
    1) common‑password dictionary (no rules) — 5 min
    2) dictionary + best64.rule           — 5 min
    3) hybrid mask (3 digits suffix)      — 10 min
  Cracked results written to separate output files.
#>

# Configuration — adjust paths as needed
$hashcat    = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\hashcat.exe"
$bcryptFile = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\Formatted-Passwords\bcrypt_with_user.txt"
# A small common password list (e.g. top 100k)
$smallDict  = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\example.dict"
# The best64 rules shipped with hashcat
$ruleFile   = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\rules\best64.rule"

# Output files
$outDir     = Split-Path $bcryptFile -Parent | Join-Path -ChildPath "quick_cracked"
if (!(Test-Path $outDir)) { New-Item $outDir -ItemType Directory | Out-Null }
$dictOut1   = Join-Path $outDir "bcrypt_common_cracked.txt"
$dictOut2   = Join-Path $outDir "bcrypt_best64_cracked.txt"
$hybridOut  = Join-Path $outDir "bcrypt_hybrid_cracked.txt"

# Phase 1: small dictionary, no rules (5 min)
Write-Host "Phase 1: small dictionary (5 min)"
& $hashcat -m 3200 -a 0 -d 1 -w 3 --username --outfile $dictOut1 --status --status-timer=60 $bcryptFile $smallDict

Write-Host "Quick checks complete. See results in $outDir" -ForegroundColor Green
