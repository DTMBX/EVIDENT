$out = Join-Path $PSScriptRoot 'secret-scan-results.txt'
"=== tracked files with risky names ===" | Out-File $out -Encoding utf8

git ls-files | Select-String -Pattern '\.env($|\.|_)|secrets|secret|key|pem|pfx|sqlite|\.db$|backup|\.log$|token|credentials' -CaseSensitive:$false |
  ForEach-Object { $_.Line } |
  Sort-Object -Unique |
"=== secret-like patterns (redacted) ===" | Out-File $out -Append -Encoding utf8

$regex = '(api[_-]?key|secret|token|bearer|private[_-]?key|password|stripe|cloudflare|supabase|firebase|aws_access|db_url|postgres)'
git grep -nEI $regex -- . 2>$null |
  ForEach-Object {
    $parts = $_ -split ':', 3
    if ($parts.Count -ge 3) {
      $redacted += ('{0}:{1}:[REDACTED]' -f $parts[0], $parts[1])
    } else {
      $redacted += $m
    }
}

$content = @()
$content += '=== tracked files with risky names ==='
$content += $tracked
$content += ''
$content += '=== secret-like patterns (redacted) ==='
$content += $redacted
$content | Set-Content -Path $out -Encoding utf8
Write-Output "Wrote results to $out"
$out = Join-Path $PSScriptRoot 'secret-scan-results.txt'
"=== tracked files with risky names ===" | Out-File $out -Encoding utf8

git ls-files | Select-String -Pattern '\.env($|\.|_)|secrets|secret|key|pem|pfx|sqlite|\.db$|backup|\.log$|token|credentials' -CaseSensitive:$false |
  ForEach-Object { $_.Line } |
  Sort-Object -Unique |
  Out-File $out -Append -Encoding utf8

"=== secret-like patterns (redacted) ===" | Out-File $out -Append -Encoding utf8

$regex = '(api[_-]?key|secret|token|bearer|private[_-]?key|password|stripe|cloudflare|supabase|firebase|aws_access|db_url|postgres)'

git grep -nEI $regex -- . 2>$null |
  ForEach-Object {
    $parts = $_ -split ':', 3
    if ($parts.Count -ge 3) { '{0}:{1}:[REDACTED]' -f $parts[0], $parts[1] } else { $_ }
  } |
  Sort-Object -Unique |
  Out-File $out -Append -Encoding utf8

Write-Output "Wrote results to $out"