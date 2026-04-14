$ErrorActionPreference = "Stop"

$codebaseCmd = (Get-Command codebase -ErrorAction Stop).Source

function Resolve-GitRoot {
    if ($env:CODEBASE_WORKSPACE) {
        try {
            return (Resolve-Path -LiteralPath $env:CODEBASE_WORKSPACE -ErrorAction Stop).Path
        } catch {
            throw "CODEBASE_WORKSPACE aponta para um path invalido: $($env:CODEBASE_WORKSPACE)"
        }
    }

    $gitRoot = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($gitRoot)) {
        return $null
    }

    try {
        return (Resolve-Path -LiteralPath $gitRoot.Trim() -ErrorAction Stop).Path
    } catch {
        throw "Nao foi possivel resolver a raiz git: $gitRoot"
    }
}

$workspacePath = Resolve-GitRoot
if (-not $workspacePath) {
    throw "Nenhum repositorio git encontrado no diretorio atual; autodev-codebase nao sera iniciado."
}

& $codebaseCmd "index" "--path=$workspacePath" "--log-level=error"
& $codebaseCmd "stdio" "--server-url=http://localhost:3001/mcp" "--log-level=error"
