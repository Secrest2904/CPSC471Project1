from socket import *
import os, sys

HEADER_SIZE = 10  # bytes reserved at the front of every message to store payload length
PACKET_SIZE = 4096  # max bytes read per recv() call
os.makedirs("cloud", exist_ok=True)  # folder where uploaded files are stored

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

# Server always connects to the client's data port 
def data_connect(client_host, client_port):
    data_sock = socket(AF_INET, SOCK_STREAM)
    data_sock.connect((client_host, client_port)); return data_sock

if len(sys.argv) < 2: print("Usage: python ser.py <PORTNUMBER>"); sys.exit(1)

# Set up the control channel listener
server_sock = socket(AF_INET, SOCK_STREAM)
server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # allow immediate reuse of the port after restart
server_sock.bind(('', int(sys.argv[1]))); server_sock.listen(5)
print(f"Server listening on port {sys.argv[1]}")

while True:
    # Accept one client; control_sock persists for the entire session
    control_sock, addr = server_sock.accept()
    client_host = addr[0]
    print(f"Connection from {addr}")
    try:
        while True:
            # Each iteration: receive one command over the control channel
            try:
                parts = recv_msg(control_sock).decode().strip().split()
            except Exception:
                print("Client disconnected"); break
            if not parts:
                continue
            cmd = parts[0].lower()
            if cmd == "quit":
                print("Client quit"); break
            # Every command (ls/get/put) is followed by a PORT message from the client
            try:
                client_data_port = int(recv_msg(control_sock).decode().split()[1])
            except Exception as e:
                send_msg(control_sock, f"FAILURE bad PORT: {e}"); continue

            if cmd == "ls":
                try:
                    files = os.listdir("cloud")
                    data_sock = data_connect(client_host, client_data_port)
                    send_msg(data_sock, "\n".join(files) if files else "(empty)"); data_sock.close()
                    send_msg(control_sock, "SUCCESS"); print("ls: SUCCESS")
                except Exception as e:
                    send_msg(control_sock, f"FAILURE {e}"); print(f"ls: FAILURE - {e}")

            elif cmd == "get":
                if len(parts) < 2:
                    send_msg(control_sock, "FAILURE no filename"); continue
                filename = os.path.basename(parts[1])
                filepath = os.path.join("cloud", filename)
                # Send FAILURE without opening data channel; client skips accept() on FAILURE
                if not os.path.isfile(filepath):
                    send_msg(control_sock, f"FAILURE file not found: {filename}"); print(f"get {filename}: FAILURE"); continue
                try:
                    with open(filepath, "rb") as f: file_data = f.read()
                    data_sock = data_connect(client_host, client_data_port)
                    send_msg(data_sock, file_data); data_sock.close()
                    send_msg(control_sock, f"SUCCESS {len(file_data)}"); print(f"get {filename}: SUCCESS - {len(file_data)} bytes")
                except Exception as e:
                    send_msg(control_sock, f"FAILURE {e}"); print(f"get {filename}: FAILURE - {e}")

            elif cmd == "put":
                if len(parts) < 2:
                    send_msg(control_sock, "FAILURE no filename"); continue
                filename = os.path.basename(parts[1])
                try:
                    # Connect to client, receive the file, then report status
                    data_sock = data_connect(client_host, client_data_port)
                    file_data = recv_msg(data_sock); data_sock.close()
                    with open(os.path.join("cloud", filename), "wb") as f: f.write(file_data)
                    send_msg(control_sock, f"SUCCESS {len(file_data)}"); print(f"put {filename}: SUCCESS - {len(file_data)} bytes")
                except Exception as e:
                    send_msg(control_sock, f"FAILURE {e}"); print(f"put {filename}: FAILURE - {e}")

            else: send_msg(control_sock, f"FAILURE unknown command: {cmd}"); print(f"Unknown '{cmd}': FAILURE")

    except Exception as e:
        print(f"Session error: {e}")
    finally: control_sock.close()
    print(f"Connection closed for {addr}")
