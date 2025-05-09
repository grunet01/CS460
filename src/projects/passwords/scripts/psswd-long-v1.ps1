<#
.SYNOPSIS
  Overnight bcrypt-only cracking session
.DESCRIPTION
  • Focus exclusively on the bcrypt hashes  
  • Uses a large dictionary + best64.rule  
  • Then a full mask attack using your mask file  
  • Leverages both GPU and CPU OpenCL devices (-D 1,2)  
  • Runs to completion (no --runtime)
  • Uses --remove to drop cracked hashes in-place
#>

#————————————————————————————————————————
# 1) Configuration
#————————————————————————————————————————
$hashcatExe  = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\hashcat.exe"
$bcryptFile  = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\Formatted-Passwords\passwd.hc"
$outputDir   = Split-Path $bcryptFile -Parent | Join-Path -ChildPath "passwd_cracked"
$largeDict   = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\hashmob.net.user.found.dict"
$ruleFile    = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\rules\best64.rule"
$maskFile    = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\masks\rockyou-7-2592000.hcmask"

$useRestore  = $false

# ensure output folder exists
if (!(Test-Path $outputDir)) { New-Item $outputDir -ItemType Directory | Out-Null }

# session names
$dictSession = "PSSWD_DICT"
$maskSession = "PSSWD_MASK"

#————————————————————————————————————————
# 2) Phase 1: Dictionary + rules
#————————————————————————————————————————
Write-Host "=== Phase 1: Dictionary+rules (passwd) ===" -ForegroundColor Cyan
# resume if possible
if ($useRestore) {
    Write-Host "Resuming dictionary session..."
    & $hashcatExe --restore --session $dictSession
} else {
    Write-Host "Starting dictionary+rules attack on passwd..."
    & $hashcatExe `
      -m 500 -a 0 -D 1,2 -O -w 3 `
      --session $dictSession `
      --username `
      --status --status-timer=60 `
      --outfile (Join-Path $outputDir "dict_cracked.txt") `
      -r $ruleFile `
      --remove `
      $bcryptFile $largeDict
}

#————————————————————————————————————————
# 3) Phase 2: Mask attack
#————————————————————————————————————————
Write-Host "`n=== Phase 2: Mask attack (passwd) ===" -ForegroundColor Cyan
if ($useRestore) {
    Write-Host "Resuming mask session..."
    & $hashcatExe --restore --session $maskSession
} else {
    Write-Host "Starting mask attack on passwd using mask file..."
    & $hashcatExe `
      -m 500 -a 3 -D 1,2 -O -w 3 `
      --session $maskSession `
      --username `
      --status --status-timer=60 `
      --outfile (Join-Path $outputDir "mask_cracked.txt") `
      --remove `
      $bcryptFile $maskFile
}

Write-Host "`nBcrypt cracking complete. Results in $outputDir" -ForegroundColor Green
