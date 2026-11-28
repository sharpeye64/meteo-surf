# Lance l'appli pour la tester sur ton téléphone avec Expo Go (même Wi-Fi que ce PC). Fermer l'onglet (ou Ctrl+C) arrête tout.
# Par défaut, l'appli lit les VRAIES données publiées sur houlalah.fr (fraîches, renouvelées par le robot).
# Option -Local : elle lit les fichiers générés sur ce PC (web/data/app), servis par un petit serveur local (port 8766).
#   Ces fichiers datent de la dernière génération faite sur le PC : ils peuvent avoir des heures ou des jours de retard
#   (cause des captures du 28/11 : prévisions de la veille à 19 h, bouées vieilles de 17 h).
param([switch]$Local)

$root = Split-Path $PSScriptRoot -Parent
$data = $null
if ($Local) {
  # Adresse du PC sur le Wi-Fi : celle de la carte réseau qui porte la route par défaut (pas un VPN ni une carte virtuelle)
  $route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Sort-Object RouteMetric, InterfaceMetric | Select-Object -First 1
  $ip = if ($route) { (Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress }
  if (-not $ip) { $ip = '192.168.1.115' }
  $env:EXPO_PUBLIC_DATA_URL = "http://${ip}:8766/data/app"
  $idx = Join-Path $root 'web\data\app\index.json'
  if (Test-Path $idx) { Write-Host ("Données LOCALES, générées le " + (Get-Item $idx).LastWriteTime.ToString('dd/MM HH:mm')) -ForegroundColor Yellow }
  $data = Start-Process python -ArgumentList "`"$root\tools\serveur_local.py`"", "`"$root\web`"", '8766' -WindowStyle Hidden -PassThru
  Write-Host "Serveur de données : http://${ip}:8766/data/app"
} else {
  Remove-Item Env:EXPO_PUBLIC_DATA_URL -ErrorAction SilentlyContinue
  Write-Host "Données : https://houlalah.fr/data/app (production)" -ForegroundColor Green
}
try {
  Set-Location $PSScriptRoot
  npx expo start --lan --port 8082 --clear
} finally {
  if ($data -and -not $data.HasExited) { Stop-Process -Id $data.Id }
}
