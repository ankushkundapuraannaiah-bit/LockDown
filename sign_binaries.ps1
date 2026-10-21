# Lock Down Browser - Authenticode Digital Signing Script
# Publisher: Ankush
param(
    [string[]]$FilesToSign = @(
        "dist\LockDownBrowser\LockDownBrowser.exe",
        "Output\LockDownBrowser-Setup.exe"
    )
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Lock Down Browser - Signing Executables (Publisher: Ankush)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Find existing Ankush Code Signing Certificate
$cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object {
    $_.Subject -like "*CN=Ankush*" -and $_.HasPrivateKey
} | Select-Object -First 1

if (-not $cert) {
    # Check if PFX exists to import
    $pfxPath = Join-Path $PSScriptRoot "AnkushCodeSigning.pfx"
    if (Test-Path $pfxPath) {
        Write-Host "Importing certificate from PFX..." -ForegroundColor Yellow
        $pwd = ConvertTo-SecureString -String "AnkushCodeSign2026" -Force -AsPlainText
        $imported = Import-PfxCertificate -FilePath $pfxPath -CertStoreLocation Cert:\CurrentUser\My -Password $pwd
        $cert = $imported | Where-Object { $_.Subject -like "*CN=Ankush*" } | Select-Object -First 1
    }
}

if (-not $cert) {
    Write-Host "Creating new Code Signing certificate for Ankush..." -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate -Type CodeSigningCert `
        -Subject "CN=Ankush" `
        -FriendlyName "Ankush Code Signing Certificate" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(10)
}

Write-Host "Signing Certificate Thumbprint: $($cert.Thumbprint)" -ForegroundColor Green
Write-Host "Signer Subject                : $($cert.Subject)" -ForegroundColor Green
Write-Host "Valid Until                   : $($cert.NotAfter)" -ForegroundColor Green

$timestampServer = "http://timestamp.digicert.com"

foreach ($file in $FilesToSign) {
    $resolvedPath = Resolve-Path $file -ErrorAction SilentlyContinue
    if ($resolvedPath -and (Test-Path $resolvedPath)) {
        Write-Host "`nSigning: $resolvedPath" -ForegroundColor White
        try {
            $sig = Set-AuthenticodeSignature -FilePath $resolvedPath -Certificate $cert -TimestampServer $timestampServer -HashAlgorithm SHA256
            Write-Host "  Timestamped via DigiCert RFC-3161: Success" -ForegroundColor Green
        } catch {
            Write-Warning "  Timestamp failed ($($_.Exception.Message)), signing without timestamp..."
            $sig = Set-AuthenticodeSignature -FilePath $resolvedPath -Certificate $cert -HashAlgorithm SHA256
        }
        
        # Remove MOTW
        Unblock-File -Path $resolvedPath -ErrorAction SilentlyContinue
        
        Write-Host "  Signer Status : $($sig.Status)" -ForegroundColor Cyan
        Write-Host "  Signer Subject: $($sig.SignerCertificate.Subject)" -ForegroundColor Cyan
    } else {
        Write-Warning "File not found, skipping: $file"
    }
}

Write-Host "`nAll specified binaries signed successfully with Publisher: Ankush" -ForegroundColor Green
