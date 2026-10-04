# Opens a public tunnel, points the Twilio number at this laptop, and runs the call server.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\start_call.ps1 -Number +1XXXXXXXXXX
param([string]$Number = "", [int]$Port = 8000)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Read-Secret($prompt) {
    [Net.NetworkCredential]::new("", (Read-Host $prompt -AsSecureString)).Password
}

$cloudflared = @("$env:LOCALAPPDATA\coffee-price-ai\bin\cloudflared.exe", (Get-Command cloudflared -ErrorAction SilentlyContinue).Source) |
               Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
$ngrok = (Get-Command ngrok -ErrorAction SilentlyContinue).Source
if (-not $cloudflared -and -not $ngrok) { throw "Neither cloudflared nor ngrok found." }

foreach ($name in "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "ELEVENLABS_API_KEY", "TWILIO_PHONE_NUMBER") {
    if (-not [Environment]::GetEnvironmentVariable($name)) {
        $saved = [Environment]::GetEnvironmentVariable($name, "User")
        if ($saved) { [Environment]::SetEnvironmentVariable($name, $saved) }
    }
}
if (-not $Number) { $Number = $env:TWILIO_PHONE_NUMBER }
if (-not $Number) { Write-Host "No -Number given: the Twilio webhook must be set by hand." }

if (-not $env:TWILIO_ACCOUNT_SID) { $env:TWILIO_ACCOUNT_SID = Read-Host "Twilio Account SID" }
if (-not $env:TWILIO_AUTH_TOKEN) { $env:TWILIO_AUTH_TOKEN = Read-Secret "Twilio Auth token" }
if (-not $env:ELEVENLABS_API_KEY) {
    try { $key = Read-Secret "ElevenLabs key (press Enter to use only the local voice)" } catch { $key = $null }
    if ($key) { $env:ELEVENLABS_API_KEY = $key }
}

$log = Join-Path $env:TEMP "coffee-tunnel.log"
Remove-Item $log -ErrorAction SilentlyContinue
if ($cloudflared) {
    Write-Host "Tunnel: Cloudflare quick tunnel"
    $tunnel = Start-Process $cloudflared -ArgumentList "tunnel --no-autoupdate --url http://127.0.0.1:$Port" `
              -PassThru -WindowStyle Hidden -RedirectStandardError $log
} else {
    Write-Host "Tunnel: ngrok"
    $tunnel = Start-Process $ngrok -ArgumentList "http $Port" -PassThru -WindowStyle Minimized
}

try {
    $url = $null
    for ($i = 0; $i -lt 40 -and -not $url; $i++) {
        Start-Sleep 1
        if ($cloudflared) {
            $m = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($m) { $url = $m.Matches[0].Value }
        } else {
            try {
                $url = ((Invoke-RestMethod http://127.0.0.1:4040/api/tunnels).tunnels |
                        Where-Object proto -eq "https" | Select-Object -First 1).public_url
            } catch {}
        }
    }
    if (-not $url) { throw "Tunnel did not report a public URL. See $log" }

    for ($i = 0; $i -lt 30; $i++) {
        try { [Net.Dns]::GetHostAddresses(([Uri]$url).Host) | Out-Null; break } catch { Start-Sleep 1 }
    }

    $env:PUBLIC_URL = $url
    $env:TWILIO_PHONE_NUMBER = $Number
    Write-Host "Public URL: $url"
    python -u -m coop_assistant.apps.call_server
} finally {
    Stop-Process -Id $tunnel.Id -ErrorAction SilentlyContinue
}
