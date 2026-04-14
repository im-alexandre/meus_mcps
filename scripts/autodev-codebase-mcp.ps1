$ErrorActionPreference = "Stop"

$hostName = "127.0.0.1"
$qdrantUrl = "http://localhost:6333/collections"
$dockerExe = "docker"
$pwshExe = (Get-Command pwsh -ErrorAction Stop).Source
$codebaseCmd = (Get-Command codebase -ErrorAction Stop).Source
$workspacePath = $null

$baseDir = Join-Path $env:USERPROFILE ".ai\shared\autodev-codebase"
$logDir = Join-Path $baseDir "logs"
$stateDir = Join-Path $baseDir "servers"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

function Resolve-WorkspacePath {
    if ($env:CODEBASE_WORKSPACE) {
        try {
            return (Resolve-Path -LiteralPath $env:CODEBASE_WORKSPACE -ErrorAction Stop).Path
        } catch {
            throw "CODEBASE_WORKSPACE aponta para um path invalido: $($env:CODEBASE_WORKSPACE)"
        }
    }

    if ($env:CLAUDE_PROJECT_DIR) {
        try {
            return (Resolve-Path -LiteralPath $env:CLAUDE_PROJECT_DIR -ErrorAction Stop).Path
        } catch {
            throw "CLAUDE_PROJECT_DIR aponta para um path invalido: $($env:CLAUDE_PROJECT_DIR)"
        }
    }

    $currentPath = (Get-Location).Path

    while ($true) {
        $hasGit = Test-Path (Join-Path $currentPath ".git")
        $hasAgents = Test-Path (Join-Path $currentPath "AGENTS.md")

        if ($hasGit -or $hasAgents) {
            return $currentPath
        }

        $parent = Split-Path -Path $currentPath -Parent
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $currentPath) {
            return $null
        }

        $currentPath = $parent
    }
}

function Test-Qdrant {
    try {
        $null = Invoke-WebRequest -UseBasicParsing -Uri $qdrantUrl -TimeoutSec 2
        return $true
    } catch {
        return $false
    }
}

function Ensure-Qdrant {
    if (Test-Qdrant) {
        return
    }

    $containerExists = $false
    try {
        $containerId = & $dockerExe ps -aq --filter "name=^qdrant$"
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($containerId)) {
            $containerExists = $true
        }
    } catch {
        throw "Falha ao consultar o Docker para o container qdrant: $($_.Exception.Message)"
    }

    if ($containerExists) {
        & $dockerExe start qdrant | Out-Null
    } else {
        & $dockerExe run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant | Out-Null
    }

    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 500
        if (Test-Qdrant) {
            return
        }
    }

    throw "Qdrant nao respondeu em localhost:6333 apos a tentativa de inicializacao."
}

function Get-FreePort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse($hostName), 0)
    $listener.Start()
    try {
        return ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    } finally {
        $listener.Stop()
    }
}

function Wait-ForHttpServer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process
    )

    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ($Process.HasExited) {
            throw "Servidor autodev-codebase encerrou antes de aceitar conexoes."
        }

        try {
            $null = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 1
            return
        } catch {
            if ($_.Exception.Response) {
                return
            }
        }

        Start-Sleep -Milliseconds 500
    }

    throw "Servidor autodev-codebase nao respondeu no tempo esperado."
}

function Get-WorkspaceKey {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkspacePath
    )

    $normalized = [System.IO.Path]::GetFullPath($WorkspacePath).ToLowerInvariant()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($normalized)
    $hashBytes = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return ([System.BitConverter]::ToString($hashBytes)).Replace("-", "").ToLowerInvariant()
}

function Get-StateFilePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkspacePath
    )

    $workspaceKey = Get-WorkspaceKey -WorkspacePath $WorkspacePath
    return Join-Path $stateDir "$workspaceKey.json"
}

function Get-LockPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkspacePath
    )

    return (Get-StateFilePath -WorkspacePath $WorkspacePath) + ".lock"
}

function Read-ServerState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateFilePath
    )

    if (-not (Test-Path -LiteralPath $StateFilePath)) {
        return $null
    }

    try {
        return Get-Content -LiteralPath $StateFilePath -Raw | ConvertFrom-Json
    } catch {
        Remove-Item -LiteralPath $StateFilePath -Force -ErrorAction SilentlyContinue
        return $null
    }
}

function Write-ServerState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StateFilePath,
        [Parameter(Mandatory = $true)]
        [hashtable]$State
    )

    $State | ConvertTo-Json | Set-Content -LiteralPath $StateFilePath -Encoding UTF8
}

function Acquire-WorkspaceLock {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LockPath
    )

    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        try {
            New-Item -ItemType Directory -Path $LockPath -ErrorAction Stop | Out-Null
            return
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }

    throw "Nao foi possivel adquirir o lock do workspace para autodev-codebase."
}

function Release-WorkspaceLock {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LockPath
    )

    Remove-Item -LiteralPath $LockPath -Recurse -Force -ErrorAction SilentlyContinue
}

function Test-ProcessAlive {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    try {
        $null = Get-Process -Id $ProcessId -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Test-ServerHealth {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ServerHost,
        [Parameter(Mandatory = $true)]
        [int]$ServerPort
    )

    $healthUrl = "http://$ServerHost`:$ServerPort/health"
    try {
        $null = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 1
        return $true
    } catch {
        if ($_.Exception.Response) {
            return $true
        }
        return $false
    }
}

function Start-WorkspaceServer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkspacePath
    )

    $port = Get-FreePort
    $serverUrl = "http://$hostName`:$port/mcp"
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $workspaceKey = Get-WorkspaceKey -WorkspacePath $WorkspacePath
    $stdoutLog = Join-Path $logDir "autodev-codebase-$workspaceKey-$timestamp.stdout.log"
    $stderrLog = Join-Path $logDir "autodev-codebase-$workspaceKey-$timestamp.stderr.log"

    $serverProcess = Start-Process -FilePath $pwshExe `
        -ArgumentList @(
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "& '$codebaseCmd' index --serve --host=$hostName --port=$port --path='$WorkspacePath' --log-level=error"
        ) `
        -WindowStyle Hidden `
        -WorkingDirectory $WorkspacePath `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru

    Wait-ForHttpServer -Url $serverUrl -Process $serverProcess

    return @{
        workspacePath = $WorkspacePath
        host = $hostName
        port = $port
        serverUrl = $serverUrl
        pid = $serverProcess.Id
        startedAt = (Get-Date).ToString("o")
        lastSeenAt = (Get-Date).ToString("o")
        stdoutLog = $stdoutLog
        stderrLog = $stderrLog
    }
}

function Get-OrStart-WorkspaceServerState {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkspacePath
    )

    $stateFilePath = Get-StateFilePath -WorkspacePath $WorkspacePath
    $lockPath = Get-LockPath -WorkspacePath $WorkspacePath

    Acquire-WorkspaceLock -LockPath $lockPath
    try {
        $state = Read-ServerState -StateFilePath $stateFilePath
        if ($state -and $state.workspacePath -eq $WorkspacePath) {
            $serverPid = 0
            try {
                $serverPid = [int]$state.pid
            } catch {
                $serverPid = 0
            }

            $port = 0
            try {
                $port = [int]$state.port
            } catch {
                $port = 0
            }

            if ($serverPid -gt 0 -and $port -gt 0 -and (Test-ProcessAlive -ProcessId $serverPid) -and (Test-ServerHealth -ServerHost $hostName -ServerPort $port)) {
                $state.lastSeenAt = (Get-Date).ToString("o")
                Write-ServerState -StateFilePath $stateFilePath -State @{
                    workspacePath = $state.workspacePath
                    host = $state.host
                    port = $port
                    serverUrl = $state.serverUrl
                    pid = $serverPid
                    startedAt = $state.startedAt
                    lastSeenAt = $state.lastSeenAt
                    stdoutLog = $state.stdoutLog
                    stderrLog = $state.stderrLog
                }
                return Read-ServerState -StateFilePath $stateFilePath
            }
        }

        $newState = Start-WorkspaceServer -WorkspacePath $WorkspacePath
        Write-ServerState -StateFilePath $stateFilePath -State $newState
        return Read-ServerState -StateFilePath $stateFilePath
    } finally {
        Release-WorkspaceLock -LockPath $lockPath
    }
}

$workspacePath = Resolve-WorkspacePath
if (-not $workspacePath) {
    throw "Nao foi possivel determinar o workspace do autodev-codebase. Defina CODEBASE_WORKSPACE ou inicie o MCP a partir de um diretorio dentro do projeto."
}

Ensure-Qdrant

$serverState = Get-OrStart-WorkspaceServerState -WorkspacePath $workspacePath
if (-not $serverState -or -not $serverState.serverUrl) {
    throw "Nao foi possivel inicializar ou localizar o servidor HTTP do autodev-codebase."
}

& $codebaseCmd "stdio" "--server-url=$($serverState.serverUrl)" "--log-level=error"
