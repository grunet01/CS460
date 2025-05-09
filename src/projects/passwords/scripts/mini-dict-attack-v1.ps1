<#
.SYNOPSIS
  Targeted “mini-list” attacks on bcrypt hashes
.DESCRIPTION
  • Builds a mini-wordlist from known patterns
  • Runs three focused attacks using your existing file paths:
    1) Word+digits hybrid (10 min)
    2) Date-format mask (10 min)
    3) Possessive suffix rule (5 min)
  • Uses --remove to drop cracked entries so later commands skip them
#>

# Paths (adjust if needed)
$hashcat = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\hashcat.exe"
$bcryptHc = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\Formatted-Passwords\bcrypt_with_user.txt"
$workDir = Split-Path $bcryptHc -Parent

# 1) Build mini-list from your recovered plaintexts
$miniList = @(
  'drum','rebel','daisy','joshualiz','pasword','volovvit','banzai','philosophized','jupiter','micronesia'
)
$miniFile = Join-Path $workDir "mini.txt"
$miniList | Set-Content $miniFile

# 2) Create possessive rule
$ruleFile = Join-Path $workDir "poss.rule"
"'s" | Set-Content $ruleFile

# Output folder
$outDir = Join-Path $workDir "mini_cracked"
if (!(Test-Path $outDir)) { New-Item $outDir -ItemType Directory | Out-Null }

# Phase A: hybrid word + 1–3 digits
Write-Host "[Phase A] Hybrid: word + 1-3 digits"
# Phase A1: 2‑digit suffix (5 min)
& $hashcat -m 3200 -a 6 --opencl-device-types 1,2 -O -w 4 --username `
    --outfile (Join-Path $outDir "bcrypt_hybrid2d.txt") `
    --status --status-timer 60 `
    $bcryptHc $miniFile ?d?d

# Phase A2: 3‑digit suffix (10 min)
& $hashcat -m 3200 -a 6 --opencl-device-types 1,2 -O -w 4 --username `
    --outfile (Join-Path $outDir "bcrypt_hybrid3d.txt") `
    --status --status-timer 60 `
    $bcryptHc $miniFile ?d?d?d


Write-Host "
Mini-list attacks complete. Results in $outDir" -ForegroundColor Green
