# Saves credentials to your Windows user environment. Secrets are typed here and never echoed.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\set_secrets.ps1
# Remove: powershell -ExecutionPolicy Bypass -File scripts\set_secrets.ps1 -Clear
param([switch]$Clear)
$names = "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER", "ELEVENLABS_API_KEY"
if ($Clear) {
    $names | ForEach-Object { [Environment]::SetEnvironmentVariable($_, $null, "User") }
    Write-Host "Cleared."
    return
}
function Read-Secret($prompt) { [Net.NetworkCredential]::new("", (Read-Host $prompt -AsSecureString)).Password }

[Environment]::SetEnvironmentVariable("TWILIO_ACCOUNT_SID", (Read-Host "Twilio Account SID"), "User")
[Environment]::SetEnvironmentVariable("TWILIO_AUTH_TOKEN", (Read-Secret "Twilio Auth token"), "User")
$number = Read-Host "Twilio phone number in E.164, e.g. +15551234567 (Enter to skip)"
if ($number) { [Environment]::SetEnvironmentVariable("TWILIO_PHONE_NUMBER", $number, "User") }
$key = Read-Secret "ElevenLabs API key (Enter to skip and use local voices only)"
if ($key) { [Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", $key, "User") }
Write-Host "Saved to your user environment."
