$codebaseCmd = (Get-Command codebase -ErrorAction Stop).Source

$workspacePath = if ($env:CODEBASE_WORKSPACE) { $env:CODEBASE_WORKSPACE }
                 else { (& git rev-parse --show-toplevel 2>$null).Trim() }
if (-not $workspacePath) { throw "Nao e um repositorio git." }

$port = 3001
while ($port -le 65535) {
    try {
        $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        $l.Start(); $l.Stop(); break
    } catch { $port++ }
}

Write-Host "autodev-codebase: porta $port"

Start-Process $codebaseCmd `
    -ArgumentList @("index", "--serve", "--host=127.0.0.1", "--port=$port", "--path=$workspacePath", "--log-level=error") `
    -WindowStyle Hidden

& $codebaseCmd "stdio" "--server-url=http://127.0.0.1:$port/mcp" "--log-level=error"
