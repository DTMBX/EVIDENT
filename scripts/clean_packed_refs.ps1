$packed = '.git/packed-refs'
$bak = '.git/packed-refs.bak'
if (Test-Path $packed) {
  Copy-Item $packed $bak -Force
  $lines = Get-Content $packed
  $filtered = $lines | Where-Object { $_ -notmatch 'backup-before-purge|backup-before-remove-large-files|DTMBX-patch-2' }
  $filtered | Set-Content $packed
  Write-Output "Filtered packed-refs; backup saved to $bak"
} else { Write-Output "packed-refs not found" }
