$ErrorActionPreference = "Stop"

$principal = New-Object Security.Principal.WindowsPrincipal(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "This script must be run from an elevated PowerShell window."
}

$envFile = Join-Path $PSScriptRoot "..\.env"
$mqttPort = 1883
if (Test-Path -LiteralPath $envFile) {
    $portLine = Get-Content -LiteralPath $envFile | Where-Object {
        $_ -match '^MQTT_PORT=([0-9]+)$'
    } | Select-Object -Last 1
    if ($portLine -and $portLine -match '^MQTT_PORT=([0-9]+)$') {
        $mqttPort = [int]$Matches[1]
    }
}

if ($mqttPort -lt 1 -or $mqttPort -gt 65535) {
    throw "MQTT_PORT must be between 1 and 65535."
}

$ruleName = "Geme Plug MQTT (Private LAN)"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

if ($existingRule) {
    $existingRule | Set-NetFirewallRule `
        -Enabled True `
        -Profile Private `
        -Direction Inbound `
        -Action Allow `
        -RemoteAddress LocalSubnet
    $existingRule | Get-NetFirewallPortFilter | Set-NetFirewallPortFilter `
        -Protocol TCP `
        -LocalPort $mqttPort
    Write-Host "Updated firewall rule '$ruleName' for TCP $mqttPort."
} else {
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Description "Allow Geme smart plug to reach the local EMQX MQTT broker." `
        -Enabled True `
        -Profile Private `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort $mqttPort `
        -RemoteAddress LocalSubnet | Out-Null
    Write-Host "Created firewall rule '$ruleName' for TCP $mqttPort."
}
