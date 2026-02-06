#Requires -Version 7.0
[CmdletBinding()]
param(
  [string] $InputRoot = "C:\Users\Devon Tyler\Documents\Filed Certifications",
  [string] $OutputRoot = "C:\Users\Devon Tyler\Documents\Filed Certifications - OCR",
  [string] $Language = "eng",
  [ValidateRange(1,32)]
  [int] $Jobs = 2,
  [bool] $MakePDFA = $true,
  [bool] $ForceOCR = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Command {
  param([string]$Name, [string]$Hint)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing dependency: '$Name'. $Hint"
  }
}

Assert-Command -Name "py" -Hint "Python is required."
Assert-Command -Name "tesseract" -Hint "Tesseract is required."
Assert-Command -Name "gswin64c" -Hint "Ghostscript is required (gswin64c.exe)."

$UsePythonModule = $true  # Always use py -m ocrmypdf to avoid PATH issues on Windows

if (-not (Test-Path $InputRoot)) { throw "InputRoot does not exist: $InputRoot" }
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
$LogDir = Join-Path $OutputRoot "_logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Get-RelativePath {
  param([string]$Base, [string]$Path)
  $baseUri = [Uri]((Resolve-Path $Base).Path + "\")
  $pathUri = [Uri]((Resolve-Path $Path).Path)
  [Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString().Replace("/", "\"))
}

function New-SafeName([string]$Text) {
  ($Text -replace '[\\/:*?"<>|]', '_')
}

Import-Module ThreadJob -ErrorAction SilentlyContinue | Out-Null

$Pdfs = Get-ChildItem -Path $InputRoot -Recurse -File -Filter *.pdf | Sort-Object FullName
if ($Pdfs.Count -eq 0) { Write-Host "No PDFs found under: $InputRoot"; exit 0 }

Write-Host ("Found {0} PDF(s)." -f $Pdfs.Count)
Write-Host ("OutputRoot: {0}" -f $OutputRoot)
Write-Host ("Language: {0} | Jobs: {1} | PDF/A: {2} | ForceOCR: {3}" -f $Language, $Jobs, $MakePDFA, $ForceOCR)

$queue = [System.Collections.Generic.Queue[System.IO.FileInfo]]::new()
foreach ($p in $Pdfs) { $queue.Enqueue($p) }

$running = @()

function Start-OneJob {
  param([System.IO.FileInfo]$Pdf)

  $inPath = $Pdf.FullName
  $rel = Get-RelativePath -Base $InputRoot -Path $inPath
  $outPath = Join-Path $OutputRoot $rel
  $outDir  = Split-Path $outPath -Parent
  New-Item -ItemType Directory -Path $outDir -Force | Out-Null

  # Only skip if output exists and is newer/equal
  if (Test-Path $outPath) {
    $inTime  = (Get-Item $inPath).LastWriteTimeUtc
    $outTime = (Get-Item $outPath).LastWriteTimeUtc
    if ($outTime -ge $inTime) { return $null }
  }

  $safe = New-SafeName $rel
  $logPath = Join-Path $LogDir ($safe + ".log")

  return Start-ThreadJob -Name $safe -ArgumentList @(
    $inPath, $outPath, $logPath, $Language, $MakePDFA, $ForceOCR, $UsePythonModule
  ) -ScriptBlock {
    param($InFile, $OutFile, $LogFile, $Lang, $PdfA, $Force, $UsePyModule)

    Set-StrictMode -Version Latest
    $ErrorActionPreference = "Stop"

    # Rebuild args *inside* the job (job-safe)
    $args = @(
  "--deskew",
  "--rotate-pages",
  "--rotate-pages-threshold","10",
  "--optimize","3",
  "-l",$Lang,
  "--tesseract-timeout","0",
  "--jobs","1"
)

    if ($PdfA) { $args += @("--output-type","pdfa") }
    if ($Force) { $args += "--force-ocr" } else { $args += "--skip-text" }

    $args += @($InFile, $OutFile)

    # Log the exact command being executed for debugging
    ("CMD: py -m ocrmypdf " + ($args -join " ")) | Set-Content -Path $LogFile -Encoding UTF8

    try {
      & py -m ocrmypdf @args 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Null
      if (-not (Test-Path $OutFile)) { throw "OCR completed without producing output: $OutFile" }
      $hash = (Get-FileHash -Algorithm SHA256 -Path $OutFile).Hash.ToLowerInvariant()
      "OUTPUT_SHA256=$hash" | Add-Content -Path $LogFile -Encoding UTF8
      return $true
    }
    catch {
      $_ | Out-String | Add-Content -Path $LogFile -Encoding UTF8
      throw
    }
  }
}

while ($queue.Count -gt 0 -or @($running).Count -gt 0) {

  while (@($running).Count -lt $Jobs -and $queue.Count -gt 0) {
    $next = $queue.Dequeue()
    $j = Start-OneJob -Pdf $next
    if ($null -ne $j) { $running = @($running + $j) }
  }

  $done = @($running | Where-Object { $_.State -in @("Completed","Failed","Stopped") })
  foreach ($j in $done) {
    try {
      Receive-Job -Job $j -ErrorAction Stop | Out-Null
    } catch {
      Write-Host "FAILED: $($j.Name)" -ForegroundColor Red
      Write-Host $_.Exception.Message
    } finally {
      Remove-Job -Job $j -Force -ErrorAction SilentlyContinue | Out-Null
    }
  }

  $running = @($running | Where-Object { $_.State -notin @("Completed","Failed","Stopped") })
  Start-Sleep -Milliseconds 200
}

Write-Host "Done."
Write-Host "Output: $OutputRoot"
Write-Host "Logs:   $LogDir"
