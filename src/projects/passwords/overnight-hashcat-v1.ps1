<#
.SYNOPSIS
  Overnight Hashcat with RAM‑disk acceleration

.DESCRIPTION
  • Creates a RAM‑disk (R:) of specified size via ImDisk  
  • Copies your core dictionary into R:  
  • Runs dictionary+rules and mask attacks on each hash file  
  • Uses NVIDIA GPU only, optimized kernels, high workload  
  • Time‑boxes mask phase proportionally per hash type  
  • Cleans up RAM‑disk when done  
#>

#———————————————————————————————
# 1) Prerequisites & Configuration
#———————————————————————————————
# Path to ImDisk CLI (adjust if installed elsewhere)
$imdiskExe    = "imdisk"   

# RAM‑disk settings
$ramLetter    = "R:"
$ramSize      = "2G"               # size of RAM‑disk (e.g. 2G, 4G)
$coreDictSrc  = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\hashmob.net.user.found.dict"       # your on‑disk “core” dictionary (~500 MB–1 GB)
$coreDictRam  = "$ramLetter\core.dict"

# Hashcat settings
$hashcatExe   = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\hashcat.exe"
$hashDir      = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\Formatted-Passwords"
$ruleFile     = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\rules\best64.rule"
$outputDir    = Join-Path $hashDir "cracked"
$mask         = "?u?l?l?l?d?d?d"

# Ensure output folder exists
if (!(Test-Path $outputDir)) { New-Item $outputDir -ItemType Directory | Out-Null }

# Jobs and time budgets
$jobs = @(
  @{ file="ntlm_with_user.txt";         mode=1000; name="NTLM"   },
  @{ file="sha512_crypt_with_user.txt"; mode=1800; name="SHA512" },
  @{ file="passwd.hc";                  mode=1800; name="PASSWD" },
  @{ file="bcrypt_with_user.txt";       mode=3200; name="BCRYPT" },
  @{ file="mysql_with_user.txt";        mode=300;  name="MYSQL"  }
)
$timeBudgets = @{ 1000=27000; 1800=60; 3200=60; 300=300 }

#———————————————————————————————
# 2) Create RAM‑disk & copy dictionary
#———————————————————————————————
Write-Host "Creating RAM‑disk $ramLetter ($ramSize) ..." -ForegroundColor Yellow
& $imdiskExe -a -s $ramSize -m $ramLetter -p "/fs:ntfs /q /y" | Out-Null

# Wait for mount
Start-Sleep -Seconds 2

Write-Host "Copying core dictionary to RAM‑disk…" -ForegroundColor Yellow
Copy-Item $coreDictSrc $coreDictRam -Force

# Use the RAM‑disk dictionary from now on
$wordlist = $coreDictRam

#———————————————————————————————
# 3) Attack Loop
#———————————————————————————————
foreach ($job in $jobs) {
  $inFile      = Join-Path $hashDir $job.file
  $workFile    = Join-Path $hashDir ("work_{0}.hc" -f $job.name)
  $dictSess    = "{0}_DICT" -f $job.name
  $maskSess    = "{0}_MASK" -f $job.name
  $dictOut     = Join-Path $outputDir ("{0}_dict.txt" -f $job.name)
  $maskOut     = Join-Path $outputDir ("{0}_mask.txt" -f $job.name)
  $dictLog     = Join-Path $outputDir ("{0}_dict.log" -f $job.name)
  $maskLog     = Join-Path $outputDir ("{0}_mask.log" -f $job.name)
  $runtime     = $timeBudgets[$job.mode]

  Write-Host "`n=== $($job.name) (mode $($job.mode)) ===" -ForegroundColor Cyan

  # work copy
  Copy-Item $inFile $workFile -Force

  # Phase 1: dictionary + rules
  Write-Host "[$dictSess] Dictionary+rules attack…" -ForegroundColor Magenta
  & $hashcatExe `
    -m $job.mode -a 0 -d 1 -O -w 3 `
    --session $dictSess --username `
    --status --status-timer=60 `
    --outfile $dictOut `
    $workFile $wordlist -r $ruleFile `
    --remove

  # Phase 2: mask with time limit
  Write-Host "[$maskSess] Mask attack (max $runtime s)…" -ForegroundColor Magenta
  & $hashcatExe `
    -m $job.mode -a 3 -d 1 -O -w 3 `
    --session $maskSess --username `
    --status --status-timer=60 `
    --outfile $maskOut --logfile-path $maskLog `
    --runtime $runtime `
    $workFile $mask

  # cleanup
  Remove-Item $workFile -Force
  Write-Host "[$($job.name)] done." -ForegroundColor Green
}

#———————————————————————————————
# 4) Teardown RAM‑disk
#———————————————————————————————
Write-Host "`nEjecting RAM‑disk $ramLetter…" -ForegroundColor Yellow
& $imdiskExe -D -m $ramLetter | Out-Null

Write-Host "`nAll jobs complete. Cracked outputs in $outputDir" -ForegroundColor Green
