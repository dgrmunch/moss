import subprocess
import time
import signal
import sys

def main():
    # Lanza el server.py como proceso
    server_process = subprocess.Popen([sys.executable, "server.py"])
    time.sleep(1)  # esperar que el server arranque

    # Lanza el cliente.py con los parámetros por defecto
    try:
        # El cliente.py se ha modificado para recibir url inicial como argumento opcional
        subprocess.run([sys.executable, "client.py", "http://localhost:1987/index.md"])
    except KeyboardInterrupt:
        print("\n[INFO] Cliente terminado por usuario")

    # Cuando el cliente acaba, mata el server
    print("[INFO] Cerrando servidor...")
    server_process.terminate()
    server_process.wait()
    print("[INFO] Servidor detenido.")

if __name__ == "__main__":
    main()
