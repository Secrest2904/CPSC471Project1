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



while True:
    connectionSocket, addr = serverSocket.accept()

    data = b""

    while True:
        tmpBuff = connectionSocket.recv(40)
        if not tmpBuff:
            break
        data += tmpBuff

    print(data.decode())
    connectionSocket.close()