# Generate PWA Icons for Windows 11
# This script creates placeholder icons for PWA packaging
# In production, replace with professionally designed icons

Write-Output "🎨 Generating PWA Icons for Windows 11 MSIX Package`n"

# Icon sizes needed for Windows 11
$sizes = @(72, 96, 128, 144, 152, 192, 384, 512)

# Source logo (we'll use the existing SVG or create simple placeholder)
$sourceIcon = "assets\img\apple-touch-icon.png"  # 796KB high-quality icon
$outputDir = "assets\icons"

# Ensure output directory exists
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Output "Source icon: $sourceIcon`n"

# Check if ImageMagick is available (for proper resizing)
$magick = Get-Command magick -ErrorAction SilentlyContinue

if ($magick) {
    Write-Output "✅ ImageMagick found - Using high-quality resizing`n"
    
    foreach ($size in $sizes) {
        $output = "$outputDir\icon-${size}x${size}.png"
        Write-Output "  Generating icon-${size}x${size}.png..."
        
        magick convert $sourceIcon -resize "${size}x${size}" $output 2>&1 | Out-Null
        
        if (Test-Path $output) {
            Write-Output "    ✅ Created"
        } else {
            Write-Output "    ❌ Failed"
        }
    }
} else {
    Write-Output "⚠️  ImageMagick not found. Using PowerShell method...`n"
    Write-Output "For better quality icons, install ImageMagick from:`n"
    Write-Output "https://imagemagick.org/script/download.php#windows`n"
    
    # Alternative: Use .NET System.Drawing (lower quality)
    Add-Type -AssemblyName System.Drawing
    
    $srcImage = [System.Drawing.Image]::FromFile((Resolve-Path $sourceIcon).Path)
    
    foreach ($size in $sizes) {
        $output = "$outputDir\icon-${size}x${size}.png"
        Write-Output "  Generating icon-${size}x${size}.png..."
        
        $destImage = New-Object System.Drawing.Bitmap($size, $size)
        $graphics = [System.Drawing.Graphics]::FromImage($destImage)
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.DrawImage($srcImage, 0, 0, $size, $size)
        
        $destImage.Save((Join-Path $PWD $output), [System.Drawing.Imaging.ImageFormat]::Png)
        
        $graphics.Dispose()
        $destImage.Dispose()
        
        if (Test-Path $output) {
            Write-Output "    ✅ Created"
        }
    }
    
    $srcImage.Dispose()
}

Write-Output "`n✅ Icon generation complete!`n"
Write-Output "Generated icons in: $outputDir`n"

# List generated icons
Write-Output "Generated files:"
Get-ChildItem "$outputDir\icon-*.png" | ForEach-Object {
    $sizeKB = "{0:N0} KB" -f ($_.Length / 1KB)
    Write-Output "  ✅ $($_.Name) ($sizeKB)"
}

Write-Output "`n🎉 Ready for PWA packaging!`n"
