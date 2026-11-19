# Lance l'appli pour la tester sur ton téléphone avec Expo Go (même Wi-Fi que ce PC).
# Les données viennent du serveur local du PC (port 8766) tant que la version pour l'appli n'est pas publiée sur houlalah.fr.
# Ce script démarre les deux : le serveur de données, puis Metro. Fermer l'onglet (ou Ctrl+C) arrête tout.
# Adresse du PC sur le Wi-Fi : celle de la carte réseau qui porte la route par défaut (pas un VPN ni une carte virtuelle)
$route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Sort-Object RouteMetric, InterfaceMetric | Select-Object -First 1
$ip = if ($route) { (Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress }
if (-not $ip) { $ip = '192.168.1.115' }
$env:EXPO_PUBLIC_DATA_URL = "http://${ip}:8766/data/app"
$root = Split-Path $PSScriptRoot -Parent
$data = Start-Process python -ArgumentList "`"$root\tools\serveur_local.py`"", "`"$root\web`"", '8766' -WindowStyle Hidden -PassThru
Write-Host "Serveur de données : http://${ip}:8766/data/app"
try {
  Set-Location $PSScriptRoot
  npx expo start --lan --port 8082
} finally {
  if ($data -and -not $data.HasExited) { Stop-Process -Id $data.Id }
}
