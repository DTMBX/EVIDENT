Param()
$ErrorActionPreference = 'Stop'
$max=80
$interval=15
for ($i=0; $i -lt $max; $i++) {
    $r = gh run list --workflow 'jekyll.yml' --branch main -L 1 --json databaseId,headBranch,status,conclusion,createdAt 2>$null | ConvertFrom-Json
    if (-not $r -or $r.Count -eq 0) {
        Write-Host 'no run yet; sleeping'
        Start-Sleep -s $interval
        continue
    }
    $run = $r[0]
    Write-Host ('RUN ' + $run.databaseId + ' status=' + $run.status + ' conclusion=' + $run.conclusion + ' head=' + $run.headBranch + ' created=' + $run.createdAt)
    if ($run.status -eq 'completed') {
        if ($run.conclusion -eq 'success') { Write-Host 'Jekyll workflow SUCCESS:' $run.databaseId; exit 0 }
        else {
            $outdir = Join-Path $env:TEMP ('jekyll_run_' + $run.databaseId)
            if (-not (Test-Path $outdir)) { New-Item -ItemType Directory -Path $outdir | Out-Null }
            gh run view $run.databaseId --log | Out-File -FilePath (Join-Path $outdir 'run.log') -Encoding utf8
            Write-Host 'Jekyll workflow FAILED:' $run.databaseId 'logs saved to' $outdir
            exit 2
        }
    }
    Start-Sleep -s $interval
}
Write-Host 'timeout waiting for run to complete'
exit 3
