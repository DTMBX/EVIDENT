$out = Join-Path $PSScriptRoot 'secret-scan-results-2.txt'

$tracked = git ls-files | Select-String -Pattern '\.env($|\.|_)|secrets|secret|key|pem|pfx|sqlite|\.db$|backup|\.log$|token|credentials' -CaseSensitive:$false | ForEach-Object { $_.Line } | Sort-Object -Unique

$redacted = @()
$regex = '(api[_-]?key|secret|token|bearer|private[_-]?key|password|stripe|cloudflare|supabase|firebase|aws_access|db_url|postgres)'
$matches = git grep -nEI $regex -- . 2>$null
foreach ($m in $matches) {
  $parts = $m -split ':', 3
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