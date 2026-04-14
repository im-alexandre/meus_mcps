# launch-claude-wsl.ps1
# Abre claude no WSL e depois o Claude Desktop app

param(
    [string]$Distro = "",
    [int]$WslStartupSeconds = 3
)

# 1. Inicia claude no WSL em uma nova janela de terminal
$wtPath = (Get-Command wt -ErrorAction SilentlyContinue)?.Source
if ($wtPath) {
    if ($Distro) {
        Start-Process wt -ArgumentList "new-tab", "--", "wsl", "-d", $Distro, "bash", "-c", "claude"
    } else {
        Start-Process wt -ArgumentList "new-tab", "--", "wsl", "bash", "-c", "claude"
    }
} else {
    if ($Distro) {
        Start-Process cmd -ArgumentList "/c", "start", "wsl", "-d", "`"$Distro`"", "bash", "-c", "`"claude`""
    } else {
        Start-Process cmd -ArgumentList "/c", "start", "wsl", "bash", "-c", "`"claude`""
    }
}

# 2. Aguarda WSL inicializar
Start-Sleep -Seconds $WslStartupSeconds

# 3. Abre o Claude Desktop app
$claudePaths = @(
    "$env:LOCALAPPDATA\Programs\Claude\Claude.exe",
    "$env:LOCALAPPDATA\Programs\@anthropic-ai\claude-code\Claude.exe",
    "$env:LOCALAPPDATA\AnthropicClaude\claude.exe"
)
$claudeExe = $claudePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($claudeExe) {
    Start-Process $claudeExe
} else {
    Write-Warning "Claude Desktop nao encontrado nos paths padrao. Abra-o manualmente."
    Write-Host "Paths verificados:"
    $claudePaths | ForEach-Object { Write-Host "  $_" }
}
