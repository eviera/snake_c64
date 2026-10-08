$ErrorActionPreference = 'Stop'
$vicePath = 'D:\Juegos\Emulators\GTK3VICE-3.10-win64\bin\x64sc.exe'
$programPath = Join-Path $PSScriptRoot 'main.prg'
$monitorPort = 6510
$client = $null
$stream = $null

function Send-MonitorCommand([string] $command) {
    $bytes = [Text.Encoding]::ASCII.GetBytes($command + "`n")
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Flush()
}

function Read-MonitorPrompt {
    $buffer = New-Object byte[] 4096
    $response = ''
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($stream.DataAvailable) {
            $count = $stream.Read($buffer, 0, $buffer.Length)
            if ($count -eq 0) { throw 'VICE cerro la conexion del monitor.' }
            $response += [Text.Encoding]::ASCII.GetString($buffer, 0, $count)
            if ($response -match '\([A-Za-z0-9]+:\$[0-9a-fA-F]+\)\s*$') {
                return $response
            }
        } else {
            Start-Sleep -Milliseconds 50
        }
    }
    throw "El monitor de VICE no respondio a tiempo. Respuesta: $response"
}

try {
    if (-not (Test-Path -LiteralPath $programPath)) { throw 'No existe main.prg.' }
    if (-not (Test-Path -LiteralPath $vicePath)) { throw "No existe VICE en $vicePath" }

    $client = New-Object Net.Sockets.TcpClient
    $connection = $client.BeginConnect('127.0.0.1', $monitorPort, $null, $null)
    $connected = $false
    try {
        if ($connection.AsyncWaitHandle.WaitOne(1000)) {
            $client.EndConnect($connection)
            $connected = $true
        }
    } catch {
        $connected = $false
    } finally {
        $connection.AsyncWaitHandle.Close()
    }

    if (-not $connected) {
        $running = @(Get-Process -Name x64sc -ErrorAction SilentlyContinue)
        if ($running.Count -gt 0) {
            throw 'Hay un VICE abierto sin monitor accesible. Cerralo una vez y ejecuta compile.bat de nuevo; las siguientes compilaciones reutilizaran esa ventana.'
        }
        # GTK3VICE no debe reconectar sus entradas/salidas a la consola del BAT.
        $arguments = '-no-redirect-streams -remotemonitor -remotemonitoraddress ip4://127.0.0.1:6510 -autostartprgmode 1 -autoload "' + $programPath + '"'
        Start-Process -FilePath $vicePath -ArgumentList $arguments -WorkingDirectory $PSScriptRoot
        Write-Host 'VICE iniciado. Cuando aparezca READY, ejecuta SYS 49152.'
        exit 0
    }

    $stream = $client.GetStream()
    $stream.WriteTimeout = 3000
    Send-MonitorCommand ''
    $null = Read-MonitorPrompt
    Send-MonitorCommand ('load "' + $programPath.Replace('\', '/') + '" 0')
    $response = Read-MonitorPrompt
    if ($response -match '(?i)error|failed|cannot|not found') {
        throw "VICE no pudo cargar el programa: $response"
    }
    if ($response -notmatch '(?i)loading') {
        throw "VICE no confirmo la carga: $response"
    }
    Send-MonitorCommand 'x'
    Write-Host 'main.prg recargado en la misma ventana de VICE. Ejecuta SYS 49152.'
} catch {
    if ($null -ne $stream) {
        try { Send-MonitorCommand 'x' } catch { }
    }
    Write-Host ('Error: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    if ($null -ne $client) { $client.Close() }
}
