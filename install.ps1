Write-Host "Script install.ps1 iniciado"
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
  Write-Host "Instalando Chocolatey..."
  Set-ExecutionPolicy Bypass -Scope Process -Force
  [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
  Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
  refreshenv
} else {
  Write-Host "Chocolatey já instalado"
}
$packages = @('python3','googlechrome','chromedriver')
foreach ($p in $packages) {
  $installed = choco list --local-only | Select-String "^$p " -Quiet
  if (-not $installed) {
    choco install $p -y
  } else {
    Write-Host "$p já instalado"
  }
}
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python setup.py
