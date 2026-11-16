# Lance l'appli pour la tester sur ton téléphone avec Expo Go (même Wi-Fi que ce PC).
# Les données viennent du serveur local du PC (port 8766) tant que la version pour l'appli n'est pas publiée sur houlalah.fr.
$env:EXPO_PUBLIC_DATA_URL = 'http://192.168.1.115:8766/data/app'
Set-Location $PSScriptRoot
npx expo start --lan --port 8082
