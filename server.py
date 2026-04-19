from socket import *
import os
import sys

HEADER_SIZE = 10
PACKET_SIZE = 4096
CLOUD_DIR = "cloud"

def ensure_server_dirs():
    os.makedirs(CLOUD_DIR, exist_ok=True)

def recv_exact(sock, num_bytes):
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def send_message(sock, payload: bytes):
    header = f"{len(payload):<{HEADER_SIZE}}".encode()
    sock.sendall(header + payload)

def recv_message(sock):
    header = recv_exact(sock, HEADER_SIZE)
    if not header:
        return None

    try:
        msg_len = int(header.decode().strip())
    except ValueError:
        return None

    return recv_exact(sock, msg_len)

def connect_data_socket(client_ip, client_port):
    data_sock = socket(AF_INET, SOCK_STREAM)
    data_sock.connect((client_ip, client_port))
    return data_sock

def handle_ls(control_sock, client_ip, data_port):
    try:
        entries = os.listdir(CLOUD_DIR)
        entries.sort()
        listing = "\n".join(entries)
        if listing:
            listing += "\n"

        data_sock = connect_data_socket(client_ip, data_port)
        send_message(data_sock, listing.encode())
        data_sock.close()

        send_message(control_sock, b"OK LS")
        print("SUCCESS: ls")
    except Exception as e:
        send_message(control_sock, f"ERR LS {e}".encode())
        print(f"FAILURE: ls -> {e}")

def handle_get(control_sock, client_ip, data_port, filename):
    file_path = os.path.join(CLOUD_DIR, filename)

    if not os.path.isfile(file_path):
        send_message(control_sock, f"ERR GET File not found: {filename}".encode())
        print(f"FAILURE: get {filename} -> file not found")
        return

    try:
        file_size = os.path.getsize(file_path)
        send_message(control_sock, f"OK GET {filename} {file_size}".encode())

        data_sock = connect_data_socket(client_ip, data_port)

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(PACKET_SIZE)
                if not chunk:
                    break
                data_sock.sendall(chunk)

        data_sock.close()
        print(f"SUCCESS: get {filename}")
    except Exception as e:
        send_message(control_sock, f"ERR GET {e}".encode())
        print(f"FAILURE: get {filename} -> {e}")


def handle_put(control_sock, client_ip, data_port, filename):
    file_path = os.path.join(CLOUD_DIR, filename)

    try:
        send_message(control_sock, f"OK PUT {filename}".encode())

        data_sock = connect_data_socket(client_ip, data_port)

        size_header = recv_exact(data_sock, HEADER_SIZE)
        if not size_header:
            raise RuntimeError("Missing file size header")

        file_size = int(size_header.decode().strip())
        bytes_left = file_size

        with open(file_path, "wb") as f:
            while bytes_left > 0:
                chunk = data_sock.recv(min(PACKET_SIZE, bytes_left))
                if not chunk:
                    raise RuntimeError("Connection closed before file completed")
                f.write(chunk)
                bytes_left -= len(chunk)

        data_sock.close()
        send_message(control_sock, f"OK PUT_DONE {filename}".encode())
        print(f"SUCCESS: put {filename}")
    except Exception as e:
        send_message(control_sock, f"ERR PUT {e}".encode())
        print(f"FAILURE: put {filename} -> {e}")



def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <PORTNUMBER ie. 12000>")
        sys.exit(1)
    
    ensure_server_dirs()
    server_port = int(sys.argv[1])
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind({"", server_port})
    server_socket.listen(1)

    print(f"Server listening on port {server_port}")
    print(f"Cloud directory: {CLOUD_DIR}/")

    while True:
        control_sock, addr = server_socket.accept()
        client_ip = addr[0]
        print(f"Control connection from {client_ip}:{addr[1]}")

        try:
            while True:
                payload = recv_message(control_sock)
                if payload is None:
                    break

                message = payload.decode().strip()
                parts = message.split()

                if not parts:
                    send_message(control_sock, b"Error: Empty Command")
                    continue

                cmd = parts[0].lower()

                if cmd == "quit":
                    send_message(control_sock, b"OK QUIT")
                    print ("Successfully quit")
                    break

                elif cmd == "ls":
                    if len(parts) != 2:
                        send_message(control_sock, b"Error Usage: ls <port>")
                        continue
                    data_port = int(parts[1])
                    handle_ls(control_sock, client_ip, data_port)
                
                elif cmd == "get":
                    if len(parts) != 3:
                        send_message(control_sock, b"Error Usage: get <filename> <port>")
                        continue
                    filename = parts[1]
                    data_port = int(parts[2])
                    handle_get(control_sock, client_ip, data_port, filename)
                
                elif cmd == "put":
                    if len(parts) != 3:
                        send_message(control_sock, b"Error Usage: put <filename> <port>")
                        continue
                    filename = parts[1]
                    data_port = int(parts[2])
                    handle_put(control_sock, client_ip, data_port, filename)
                else:
                    send_message(control_sock, b"Error: Unknown Command")
        finally:
            control_sock.close()
            print("Connection closed")
if __name__ == "__main__":
    main()