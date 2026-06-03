# install.ps1

# Ορισμός του φακέλου εγκατάστασης στα έγγραφα του χρήστη
$install_dir = "$env:USERPROFILE\Documents\DevToolsInstall"

# Έλεγχος αν ο χρήστης τρέχει το PowerShell ως διαχειριστής
$is_admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   DevTools Installer - Λήψη & Εγκατάσταση" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Βήμα 1: Προετοιμασία φακέλου εγκατάστασης
# Αν ο φάκελος υπάρχει ήδη, τον διαγράφουμε για να κάνουμε καθαρή εγκατάσταση
if (Test-Path -Path $install_dir) {
    Write-Host "[*] Ο φάκελος εγκατάστασης υπάρχει ήδη: $install_dir" -ForegroundColor Yellow
    Write-Host "[*] Γίνεται καθαρισμός παλιών αρχείων..." -ForegroundColor Yellow
    Remove-Item -Path $install_dir -Recurse -Force -ErrorAction SilentlyContinue
}

# Βήμα 2: Λήψη του κώδικα (κλωνοποίηση με Git ή λήψη ZIP)
$git_installed = $false
try {
    $null = Get-Command git -ErrorAction Stop
    $git_installed = $true
} catch {
    # Το Git δεν είναι εγκατεστημένο στο σύστημα
}

if ($git_installed) {
    Write-Host "[+] Εντοπίστηκε το Git. Γίνεται κλωνοποίηση του repository..." -ForegroundColor Green
    git clone "https://github.com/christoskataxenos/DevToolsInstall.git" $install_dir
} else {
    Write-Host "[-] Το Git δεν βρέθηκε. Γίνεται λήψη του ZIP αρχείου από το GitHub..." -ForegroundColor Yellow
    $zip_url = "https://github.com/christoskataxenos/DevToolsInstall/archive/refs/heads/main.zip"
    $zip_path = "$env:TEMP\DevToolsInstall.zip"
    
    # Λήψη του αρχείου ZIP
    Invoke-RestMethod -Uri $zip_url -OutFile $zip_path
    
    # Αποσυμπίεση του ZIP
    Write-Host "[+] Αποσυμπίεση αρχείων..." -ForegroundColor Green
    Expand-Archive -Path $zip_path -DestinationPath "$env:TEMP\DevToolsExtract" -Force
    
    # Δημιουργία του τελικού φακέλου
    New-Item -ItemType Directory -Path $install_dir -Force | Out-Null
    
    # Μεταφορά των αποσυμπιεσμένων αρχείων στον τελικό φάκελο
    Copy-Item -Path "$env:TEMP\DevToolsExtract\DevToolsInstall-main\*" -Destination $install_dir -Recurse -Force
    
    # Καθαρισμός προσωρινών αρχείων λήψης
    Remove-Item -Path $zip_path -Force
    Remove-Item -Path "$env:TEMP\DevToolsExtract" -Recurse -Force
}

# Βήμα 3: Εκτέλεση του setup.bat
# Μεταβαίνουμε στον φάκελο εγκατάστασης και εκτελούμε το υπάρχον αρχείο ρυθμίσεων setup.bat
if (Test-Path -Path "$install_dir\setup.bat") {
    Write-Host "[+] Εκτέλεση του αρχικού setup.bat..." -ForegroundColor Green
    Set-Location -Path $install_dir
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c setup.bat" -Wait -NoNewWindow
} else {
    Write-Host "[ERROR] Το αρχείο setup.bat δεν βρέθηκε στον φάκελο εγκατάστασης!" -ForegroundColor Red
}
