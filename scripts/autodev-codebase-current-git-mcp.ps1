$ErrorActionPreference = "Stop"

$codebaseCommand = Get-Command codebase -ErrorAction Stop
$codebaseSource = $codebaseCommand.Source
$codebaseCmd = $codebaseSource
$usePwshShim = $false

if ($IsWindows -and $codebaseCmd -like "*.ps1") {
    $cmdShim = [System.IO.Path]::ChangeExtension($codebaseCmd, ".cmd")
    if (Test-Path $cmdShim) {
        $codebaseCmd = $cmdShim
    } else {
        $codebaseCmd = "pwsh"
        $usePwshShim = $true
    }
}

function Resolve-WorkspacePath {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEBASE_WORKSPACE)) {
        return (Resolve-Path $env:CODEBASE_WORKSPACE).Path
    }

    $currentPath = (Get-Location).Path

    $gitRoot = & git -C $currentPath rev-parse --show-toplevel 2>$null
    if (-not [string]::IsNullOrWhiteSpace($gitRoot)) {
        return $gitRoot.Trim()
    }

    return $currentPath
}

function Get-FreePort {
    $port = 3001

    while ($port -le 65535) {
        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
            $listener.Start()
            $listener.Stop()
            return $port
        } catch {
            $port++
        }
    }

    throw "No free port found."
}

function Wait-HttpEndpoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,

        [int]$TimeoutSeconds = 30
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)

    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 2
            if ($null -ne $response) {
                return
            }
        } catch {
            if ($_.Exception.Response) {
                return
            }
        }

        Start-Sleep -Milliseconds 500
    }

    throw "Timed out waiting for $Url"
}

$workspacePath = Resolve-WorkspacePath
$env:CODEBASE_WORKSPACE = $workspacePath

$logRoot = Join-Path $env:TEMP "autodev-codebase"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

$workspaceBytes = [System.Text.Encoding]::UTF8.GetBytes($workspacePath)
$workspaceHex = [Convert]::ToHexString($workspaceBytes).ToLowerInvariant()
$workspaceSlug = $workspaceHex.Substring(0, [Math]::Min(24, $workspaceHex.Length))

$serverStdoutLog = Join-Path $logRoot "$workspaceSlug.server.stdout.log"
$serverStderrLog = Join-Path $logRoot "$workspaceSlug.server.stderr.log"
$stdioStderrLog = Join-Path $logRoot "$workspaceSlug.stdio.stderr.log"

$port = Get-FreePort
[Console]::Error.WriteLine("autodev-codebase: workspace $workspacePath")
[Console]::Error.WriteLine("autodev-codebase: porta $port")

$serveArgs = @(
    "index",
    "--serve",
    "--watch",
    "--host=127.0.0.1",
    "--port=$port",
    "--path=$workspacePath",
    "--log-level=error"
)

if ($usePwshShim) {
    Start-Process `
        -FilePath $codebaseCmd `
        -ArgumentList @("-NoLogo", "-NoProfile", "-File", $codebaseSource) + $serveArgs `
        -WorkingDirectory $workspacePath `
        -RedirectStandardOutput $serverStdoutLog `
        -RedirectStandardError $serverStderrLog `
        -WindowStyle Hidden | Out-Null
} else {
    Start-Process `
        -FilePath $codebaseCmd `
        -ArgumentList $serveArgs `
        -WorkingDirectory $workspacePath `
        -RedirectStandardOutput $serverStdoutLog `
        -RedirectStandardError $serverStderrLog `
        -WindowStyle Hidden | Out-Null
}

Wait-HttpEndpoint -Url "http://127.0.0.1:$port/mcp" -TimeoutSeconds 30

$stdioArgs = @(
    "stdio",
    "--server-url=http://127.0.0.1:$port/mcp",
    "--log-level=error"
)

if ($usePwshShim) {
    & $codebaseCmd "-NoLogo" "-NoProfile" "-File" $codebaseSource @stdioArgs 2>> $stdioStderrLog
} else {
    & $codebaseCmd @stdioArgs 2>> $stdioStderrLog
}
