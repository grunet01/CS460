<#
.SYNOPSIS
  Overnight Hashcat Automation (no RAM‑disk, in‑place files)

.DESCRIPTION
  • Runs dictionary+rules and mask attacks on each formatted hash file in .\passwords  
  • Uses only your NVIDIA GPU, optimized kernels, high workload  
  • Time‑boxes mask phase proportionally per hash type  
  • Uses --remove to drop cracked hashes from the original files (no work‐copies)  
#>

#————————————————————————————————————————
# 1) Configuration
#————————————————————————————————————————
$hashcatExe = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\hashcat.exe"
$hashDir    = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\Formatted-Passwords"
$outputDir  = Join-Path $hashDir "cracked"
$ruleFile   = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\rules\best64.rule"
$mask       = "?1?2?2?2?2?2?2?3?3?3?3?d?d?d?d" #"?u?l?l?l?d?d?d"
$mask_file  = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\masks\rockyou-4-43200.hcmask"

$wordlist_lg = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\hashmob.net.user.found.dict"
$wordlist_xs = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\example.dict"

# ensure output folder exists
if (!(Test-Path $outputDir)) {
    New-Item $outputDir -ItemType Directory | Out-Null
}

#————————————————————————————————————————
# 2) Define jobs & time budgets
#————————————————————————————————————————

# Total: 21/50

$jobs = @(
    #@{ file="ntlm_with_user.txt";         mode=1000; name="NTLM"   } 
        #exhausted
        #9/10  4 of them found with lookup table https://hashes.com/en/decrypt/hash
    #@{ file="sha512_crypt_with_user.txt"; mode=1800; name="SHA512" } 
        #non-exhausted
        #3/10
    #@{ file="passwd.hc";                  mode=500;  name="PASSWD" }
        #exhausted
        #3/10
    #@{ file="bcrypt_with_user.txt";       mode=3200; name="BCRYPT" }
        #non-exhausted
        #0/10
    #@{ file="mysql_with_user.txt";        mode=300;  name="MYSQL"  }
        #exhausted
        #6/10

)

# Time budgets (in seconds)
# Dictionary Phase Budgets
$dictTimeBudgets = @{
  1000 = 1800     # NTLM
  1800 = 2400     # SHA512
  500  = 24000     # MD5-crypt
  3200 = 18000     # bcrypt
  300  = 14400     # MySQL-old
}

# Mask Phase Budgets
$maskTimeBudgets = @{
  1000 = 7200     # NTLM
  1800 = 1800     # SHA512
  500  = 18000     # MD5-crypt
  3200 = 12000     # bcrypt
  300  = 3200     # MySQL-old
}



#————————————————————————————————————————
# 3) Attack loop (in‑place, using --remove)
#————————————————————————————————————————
foreach ($job in $jobs) {
  $inFile      = Join-Path $hashDir $job.file
  $dictSession = "{0}_DICT" -f $job.name
  $maskSession = "{0}_MASK" -f $job.name
  $dictRestore = "$dictSession.restore"
  $maskRestore = "$maskSession.restore"
  $dictOut     = Join-Path $outputDir ("{0}_dict_cracked.txt" -f $job.name)
  $maskOut     = Join-Path $outputDir ("{0}_mask_cracked.txt" -f $job.name)
  $dictTime    = 12000 #$dictTimeBudgets[$job.mode]
  $maskTime    = 12000 #$maskTimeBudgets[$job.mode]

  Write-Host "`n=== $($job.name) (mode $($job.mode)) ===" -ForegroundColor Cyan

  # Phase 1: Dictionary+rules (resume if restore exists)
  if (Test-Path $dictRestore) {
    Write-Host "[$dictSession] Restore file found. Resuming dictionary session..."
    & $hashcatExe --restore --session $dictSession
  } else {
      Write-Host "[$dictSession] Dictionary+rules attack (max $dictTime s)..."
      & $hashcatExe `
        -m $job.mode -a 0 -d 1 -O -w 3 `
        --session $dictSession `
        --username `
        --status --status-timer=60 `
        --outfile $dictOut `
        --runtime $dictTime `
        $inFile $wordlist_lg -r $ruleFile `
        --remove
  }

  # Phase 2: Mask (resume if restore exists)
  if (Test-Path $maskRestore) {
    Write-Host "[$maskSession] Restore file found. Resuming mask session..."
    & $hashcatExe --restore --session $maskSession
  } else {
      Write-Host "[$maskSession] Mask attack (max $maskTime s)..."
      & $hashcatExe `
        -m $job.mode -a 3 -d 1 -O -w 3 `
        --session $maskSession `
        --username `
        --status --status-timer=60 `
        --outfile $maskOut `
        --runtime $maskTime `
        $inFile $mask_file

  }

  Write-Host "[$($job.name)] done."
}


Write-Host "`nAll jobs complete. Cracked files in $outputDir`n" -ForegroundColor Green
