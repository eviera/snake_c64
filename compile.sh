#!/bin/bash
# Compila main.asm y carga main.prg en VICE, reutilizando su ventana.
set -u
cd -- "$(dirname -- "$0")" || exit 1

JAVA_BIN="${JAVA_HOME:+$JAVA_HOME/bin/java}"
if [ -z "$JAVA_BIN" ] && command -v brew >/dev/null 2>&1; then
    brew_root="$(brew --prefix)"
    for candidate in "$brew_root/opt/openjdk@17/bin/java" "$brew_root/opt/openjdk/bin/java"; do
        if [ -x "$candidate" ]; then JAVA_BIN="$candidate"; break; fi
    done
fi
JAVA_BIN="${JAVA_BIN:-java}"
if ! "$JAVA_BIN" -version >/dev/null 2>&1; then
    echo 'Falta Java. Instalalo con: brew install openjdk@17' >&2
    exit 1
fi
if ! "$JAVA_BIN" -jar ./KickAss.jar ./main.asm; then
    echo 'Error de compilacion. No se iniciara VICE.' >&2
    exit 1
fi

export VICE_BIN="${VICE_BIN:-/Applications/vice-arm64-gtk3-3.10/bin/x64sc}"
exec /usr/bin/ruby - "$PWD/main.prg" <<'RUBY'
require 'socket'
require 'timeout'

program = ARGV.fetch(0)
vice = ENV.fetch('VICE_BIN')
client = nil

def send_command(client, command)
  Timeout.timeout(3) { client.write(command + "\n") }
end

def read_prompt(client, loading: false)
  response = ''
  Timeout.timeout(10) do
    loop do
      response << client.readpartial(4096)
      if response.match?(/\([A-Za-z0-9]+:\$[0-9a-fA-F]+\)\s*\z/)
        # Al activar el monitor puede llegar un prompt antes de procesar load.
        return response unless loading
        return response if response.match?(/loading|error|failed|cannot|not found/i)
      end
    end
  end
end

begin
  raise 'No existe main.prg.' unless File.file?(program)
  raise "No existe VICE en #{vice}" unless File.executable?(vice)
  begin
    client = Timeout.timeout(1) { TCPSocket.new('127.0.0.1', 6510) }
  rescue SystemCallError, IOError, Timeout::Error
    client = nil
  end

  if client.nil?
    if system('/usr/bin/pgrep', '-x', 'x64sc', out: File::NULL)
      raise 'Hay un VICE abierto sin monitor accesible. Cerralo una vez y ejecuta compile.sh de nuevo; las siguientes compilaciones reutilizaran esa ventana.'
    end
    log = File.join(File.dirname(program), 'tmp', 'vice-mac.log')
    Dir.mkdir(File.dirname(log)) unless Dir.exist?(File.dirname(log))
    pid = Process.spawn(vice, '-remotemonitor', '-remotemonitoraddress',
                        'ip4://127.0.0.1:6510', '-autostartprgmode', '1',
                        '-autoload', program, out: log, err: [:child, :out])
    Process.detach(pid)
    puts 'VICE iniciado. Cuando aparezca READY, ejecuta SYS 49152.'
  else
    # El primer comando activa el monitor; no esperar un saludo previo.
    send_command(client, "load \"#{program}\" 0")
    response = read_prompt(client, loading: true)
    raise "VICE no pudo cargar el programa: #{response}" if response.match?(/error|failed|cannot|not found/i)
    raise "VICE no confirmo la carga: #{response}" unless response.match?(/loading/i)
    send_command(client, 'x')
    puts 'main.prg recargado en la misma ventana de VICE. Ejecuta SYS 49152.'
  end
rescue StandardError => error
  begin
    send_command(client, 'x') if client
  rescue StandardError
  end
  warn "Error: #{error.message}"
  exit 1
ensure
  client.close if client
end
RUBY
