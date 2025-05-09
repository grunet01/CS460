<#
.SYNOPSIS
  Username‑dictionary attack across all hash files
.DESCRIPTION
  • Extracts every username from each formatted hash file into one dictionary  
  • Runs a pure dictionary attack (no rules) using that username list on each hash file  
  • Leverages both GPU and CPU OpenCL devices (-D 1,2)  
  • Uses --remove to drop cracked hashes in-place
#>

#————————————————————————————————————————
# 1) Configuration
#————————————————————————————————————————
$hashcatExe = "C:\Users\Ethan\Downloads\hashcat-6.2.6\hashcat-6.2.6\hashcat.exe"
$hashDir    = "C:\Users\Ethan\Documents\GitHub\CS460\src\projects\passwords\Formatted-Passwords"
$outputDir  = Join-Path $hashDir "cracked_usernames"

# ensure output folder exists
if (!(Test-Path $outputDir)) { New-Item $outputDir -ItemType Directory | Out-Null }

# all input hash files
$hashFiles = @(
    "ntlm_with_user.txt",
    "sha512_crypt_with_user.txt",
    "passwd.hc",
    "bcrypt_with_user.txt",
    "mysql_with_user.txt"
) | ForEach-Object { Join-Path $hashDir $_ }

# temporary username dictionary
$userDict = Join-Path $hashDir "usernames.dict"

#————————————————————————————————————————
# 2) Build username dictionary
#————————————————————————————————————————
Write-Host "Extracting usernames from all hash files..." -ForegroundColor Cyan
$users = foreach($file in $hashFiles) {
    Get-Content $file | ForEach-Object {
        # assume username:hash:... or username:hash
        $fields = $_ -split ':'
        if ($fields.Count -ge 2) { $fields[0] }
    }
}
# unique and save
$users | Sort-Object -Unique | Set-Content $userDict
Write-Host "Username dictionary ($($users.Count) entries) written to $userDict" -ForegroundColor Green

#————————————————————————————————————————
# 3) Dictionary attack per file
#————————————————————————————————————————
foreach ($inFile in $hashFiles) {
    $base = [IO.Path]::GetFileNameWithoutExtension($inFile)
    $mode = switch ($base) {
        'ntlm_with_user'         { 1000 }
        'sha512_crypt_with_user' { 1800 }
        'passwd'                 { 500  }
        'bcrypt_with_user'       { 3200 }
        'mysql_with_user'        { 300  }
        default                  { throw "Unknown file type $base" }
    }
    $session = "USER_$base"
    $outFile = Join-Path $outputDir "$base`_user_cracked.txt"

    Write-Host "`n=== Attacking $base (mode $mode) with username dictionary ===" -ForegroundColor Cyan
    & $hashcatExe `
      -m $mode -a 0 -D 1,2 -O -w 3 `
      --session $session `
      --username `
      --status --status-timer=60 `
      --outfile $outFile `
      --remove `
      $inFile $userDict
}

Write-Host "`nUsername dictionary attacks complete. Results in $outputDir" -ForegroundColor Green
