# install.ps1

# Ορισμός του φακέλου εγκατάστασης στα έγγραφα του χρήστη
$install_dir = "$env:USERPROFILE\Documents\DevToolsInstall"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   DevTools Installer - Download & Install" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Βήμα 1: Προετοιμασία φακέλου εγκατάστασης
if (Test-Path -Path $install_dir) {
    Write-Host "[*] Installation directory already exists: $install_dir" -ForegroundColor Yellow
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
    if (Test-Path -Path "$install_dir\.git") {
        Write-Host "[+] Git repository detected. Updating existing installation..." -ForegroundColor Green
        # Αλλαγή Cwd στον φάκελο και git pull
        $prev_dir = Get-Location
        Set-Location -Path $install_dir
        # Καθαρίζουμε τυχόν τοπικές αλλαγές και κάνουμε pull
        git reset --hard HEAD
        git pull origin main
        Set-Location -Path $prev_dir
    } else {
        Write-Host "[+] Git detected. Cloning the repository..." -ForegroundColor Green
        # Διαγραφή περιεχομένων αν υπάρχει ο φάκελος αλλά δεν είναι Git repo
        if (Test-Path -Path $install_dir) {
            Write-Host "[*] Cleaning up old files..." -ForegroundColor Yellow
            Remove-Item -Path "$install_dir\*" -Recurse -Force -ErrorAction SilentlyContinue
        }
        git clone "https://github.com/christoskataxenos/DevToolsInstall.git" $install_dir
    }
} else {
    Write-Host "[-] Git not found. Downloading ZIP file from GitHub..." -ForegroundColor Yellow
    # Καθαρισμός παλιών αρχείων
    if (Test-Path -Path $install_dir) {
        Write-Host "[*] Cleaning up old files..." -ForegroundColor Yellow
        # Διαγράφουμε τα περιεχόμενα αντί για τον ίδιο τον φάκελο, σε περίπτωση που ο χρήστης είναι μέσα σε αυτόν
        Remove-Item -Path "$install_dir\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    $zip_url = "https://github.com/christoskataxenos/DevToolsInstall/archive/refs/heads/main.zip"
    $zip_path = "$env:TEMP\DevToolsInstall.zip"
    
    # Λήψη του αρχείου ZIP
    Invoke-RestMethod -Uri $zip_url -OutFile $zip_path
    
    # Αποσυμπίεση του ZIP
    Write-Host "[+] Extracting files..." -ForegroundColor Green
    Expand-Archive -Path $zip_path -DestinationPath "$env:TEMP\DevToolsExtract" -Force
    
    # Δημιουργία του τελικού φακέλου αν δεν υπάρχει
    if (-not (Test-Path -Path $install_dir)) {
        New-Item -ItemType Directory -Path $install_dir -Force | Out-Null
    }
    
    # Μεταφορά των αποσυμπιεσμένων αρχείων στον τελικό φάκελο
    Copy-Item -Path "$env:TEMP\DevToolsExtract\DevToolsInstall-main\*" -Destination $install_dir -Recurse -Force
    
    # Καθαρισμός προσωρινών αρχείων λήψης
    Remove-Item -Path $zip_path -Force
    Remove-Item -Path "$env:TEMP\DevToolsExtract" -Recurse -Force
}

# Βήμα 3: Εκτέλεση του setup.bat
# Μεταβαίνουμε στον φάκελο εγκατάστασης και εκτελούμε το υπάρχον αρχείο ρυθμίσεων setup.bat
if (Test-Path -Path "$install_dir\setup.bat") {
    Write-Host "[+] Running the initial setup.bat..." -ForegroundColor Green
    $prev_dir = Get-Location
    Set-Location -Path $install_dir
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c setup.bat" -Wait -NoNewWindow
    Set-Location -Path $prev_dir
} else {
    Write-Host "[ERROR] setup.bat was not found in the installation directory!" -ForegroundColor Red
}
