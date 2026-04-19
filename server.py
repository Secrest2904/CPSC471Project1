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