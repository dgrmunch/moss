import socket
import threading
import os
import logging

logging.basicConfig(level=logging.INFO, format='[SERVER] %(message)s')

CONTENT_DIR = "content"
HOST = "0.0.0.0"
PORT = 1966

def handle_client(conn, addr):
    logging.info(f"Connection from {addr}")
    try:
        request = conn.recv(1024).decode("utf-8").strip()
        logging.info(f"Requested path: {request}")

        if not request:
            conn.close()
            return

        path = request.lstrip("/")
        if path == "":
            path = "index.md"

        full_path = os.path.join(CONTENT_DIR, path)

        if not os.path.exists(full_path):
            logging.info(f"File not found: {full_path}")
            conn.sendall(b"ERROR: File not found\n")
        else:
            logging.info(f"Serving file: {full_path}")
            with open(full_path, "rb") as f:
                content = f.read()
            # Enviar encabezado mínimo antes del contenido para protocolo
            conn.sendall(b"20 OK\n\n" + content)

    except Exception as e:
        logging.error(f"Error handling client {addr}: {e}")
    finally:
        conn.close()
        logging.info(f"Connection closed: {addr}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    logging.info(f"Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()

if __name__ == "__main__":
    main()
