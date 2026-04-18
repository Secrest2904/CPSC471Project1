from socket import *
import os, sys

HEADER_SIZE = 10  # bytes reserved at the front of every message to store payload length
PACKET_SIZE = 4096  # max bytes read per recv() call

os.makedirs("download", exist_ok=True)  # folder where received files are saved

# Prepend a 10 byte size header then send all bytes in a loop
def send_msg(sock, data):
    if isinstance(data, str):
        data = data.encode()

    data = f"{len(data):010d}".encode() + data  # header + payload
    bytes_sent = 0

    while bytes_sent < len(data):
        n = sock.send(data[bytes_sent:])
        if not n:
            raise RuntimeError("broken")
        bytes_sent += n

# Read the 10 byte header to get the payload size, then recv exactly that many bytes
def recv_msg(sock):
    header = b""

    while len(header) < HEADER_SIZE:
        chunk = sock.recv(HEADER_SIZE - len(header))
        if not chunk:
            raise RuntimeError("broken")
        header += chunk

    payload, size = b"", int(header.decode())
    while len(payload) < size:
        chunk = sock.recv(min(PACKET_SIZE, size - len(payload)))
        if not chunk:
            raise RuntimeError("broken")
        payload += chunk

    return payload

# Open a listen socket, send the command + PORT to the server, return the listener
def open_transfer(control_sock, cmd):
    listen_sock = socket(AF_INET, SOCK_STREAM)
    listen_sock.bind(('', 0)); listen_sock.listen(1)  # port 0 = OS picks a free port
    send_msg(control_sock, cmd)
    send_msg(control_sock, f"PORT {listen_sock.getsockname()[1]}")  # tell server which port to connect to
    return listen_sock

if len(sys.argv) < 3: print("Usage: python cli.py <server_host> <server_port>"); sys.exit(1)

# Establish the control channel
control_sock = socket(AF_INET, SOCK_STREAM)
control_sock.connect((sys.argv[1], int(sys.argv[2])))
print(f"Connected to {sys.argv[1]}:{sys.argv[2]}")

while True:
    try:
        command = input("ftp> ").strip()
    except EOFError:
        break
    if not command:
        continue
    parts = command.split()
    cmd = parts[0].lower()

    if cmd == "quit":
        send_msg(control_sock, "quit"); break

    elif cmd == "ls":
        # Open data channel, wait for SUCCESS, then accept the already queued data connection
        listen_sock = open_transfer(control_sock, "ls")
        status = recv_msg(control_sock).decode()

        if status.startswith("SUCCESS"):
            data_conn, _ = listen_sock.accept()
            print(recv_msg(data_conn).decode()); data_conn.close()

        else:
            print(f"Error: {status}")
        listen_sock.close()

    elif cmd == "get":
        if len(parts) < 2:
            print("Usage: get <filename>"); continue
        filename = parts[1]
        # Server sends FAILURE over control if file is missing
        listen_sock = open_transfer(control_sock, f"get {filename}")
        status = recv_msg(control_sock).decode()

        if status.startswith("SUCCESS"):
            data_conn, _ = listen_sock.accept()
            file_data = recv_msg(data_conn); data_conn.close()
            with open(os.path.join("download", os.path.basename(filename)), "wb") as f: f.write(file_data)
            print(f"{filename}: {len(file_data)} bytes received")

        else:
            print(f"Error: {status}")
        listen_sock.close()

    elif cmd == "put":
        if len(parts) < 2:
            print("Usage: put <filename>"); continue
        filename = parts[1]

        if not os.path.isfile(filename):
            print(f"Error: '{filename}' not found locally"); continue
        with open(filename, "rb") as f: file_data = f.read()
        # For put, accept first, then send
        listen_sock = open_transfer(control_sock, f"put {filename}")
        data_conn, _ = listen_sock.accept()
        send_msg(data_conn, file_data); data_conn.close(); listen_sock.close()
        status = recv_msg(control_sock).decode()

        if status.startswith("SUCCESS"):
            print(f"{filename}: {len(file_data)} bytes sent")
        else:
            print(f"Error: {status}")

    else:
        print("Commands: ls | get <filename> | put <filename> | quit")

control_sock.close()
