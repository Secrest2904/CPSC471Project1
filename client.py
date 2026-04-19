from socket import *
import os
import sys

HEADER_SIZE = 10
PACKET_SIZE = 4096
DOWNLOAD_DIRECTORY = "Downloads_471"

def check_directory():
    os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)

clientSocket = socket(AF_INET, SOCK_STREAM)


def sendMessage(sock, payload: bytes):
    header = f"{len(payload):<{HEADER_SIZE}}".encode()
    sock.sendall(header + payload)

def recv_exact(sock, num_bytes):
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def recv_message(sock):
    header = recv_exact(sock, HEADER_SIZE)
    if not header:
        return None
    try:
        messageLength = int(header.decode().strip())
    except ValueError:
        return None
    return recv_exact(sock, messageLength)

def data_listener():
    listener = socket(AF_INET, SOCK_STREAM)
    listener.bind(("", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    return listener, port

def receive_listening(listener):
    dataConnection, _ = listener.accept()
    payload = recv_message(dataConnection)
    dataConnection.close()
    listener.close()
    if payload is None:
        print("Error while listening")
        return
    text = payload.decode()
    if text:
        print(text, end="")
    else:
        print("No files on the server")

def receive_file(listener, filename, expected_size):
    filepath = os.path.join(DOWNLOAD_DIRECTORY, filename)
    dataConnection, _ = listener.accept()

    bytes_received = 0
    with open(filepath, "wb") as receivedFile:
        while bytes_received < expected_size:
            chunk = dataConnection.recv(min(PACKET_SIZE, expected_size - bytes_received))
            if not chunk:
                break
            receivedFile.write(chunk)
            bytes_received += len(chunk)
    dataConnection.close()
    listener.close()
    print(f"{filename} {bytes_received} bytes successfully sent")
    print(f"Saved to: {filepath}")

def send_file(listener, filename):
    dataConnection, _ = listener.accept()

    file_size = os.path.getsize(filename)
    size_header = f"{file_size:<{HEADER_SIZE}}".encode()
    dataConnection.sendall(size_header)

    bytes_sent = 0
    with open(filename, "rb") as writeFile:
        while True:
            chunk = writeFile.read(PACKET_SIZE)
            if not chunk:
                break
            dataConnection.sendall(chunk)
            bytes_sent += len(chunk)
    dataConnection.close()
    listener.close()

    print(f"Successfully transferred {filename} as {bytes_sent} bytes")

def main():
    if len(sys.argv) != 3:
        print("Error: run python client.py <server machine ie. localhost> <port number ie. 12000>")
        sys.exit(1)
    check_directory()
    serverName = sys.argv[1]
    serverPort = int(sys.argv[2])

    control_sock = socket(AF_INET, SOCK_STREAM)
    control_sock.connect((serverName, serverPort))

    print(f"Connected to {serverName}:{serverPort}")
    print(f"Download directory: {DOWNLOAD_DIRECTORY}/")

    try:
        while True:
            command = input(">> ").strip()
            if not command:
                continue
            parts = command.split()
            cmd = parts[0].lower()

            if cmd == "quit":
                sendMessage(control_sock, b"quit")
                reply = recv_message(control_sock)
                if reply:
                    print(reply.decode())
                break
            elif cmd == "ls":
                if len(parts) != 1:
                    print("ls should be used on its own")
                    continue
                listener, data_port = data_listener()
                sendMessage(control_sock, f"ls {data_port}".encode())
                receive_listening(listener)
                reply = recv_message(control_sock)
                if reply:
                    print(reply.decode())
            
            elif cmd == "get":
                if len(parts) != 2:
                    print ("Usage: get <filename>")
                    continue
                filename = parts[1]
                listener, data_port = data_listener()
                sendMessage(control_sock, f"get {filename} {data_port}".encode())

                reply = recv_message(control_sock)
                if reply is None:
                    print("No reply from server")
                    listener.close()
                    continue
                reply_text = reply.decode()
                if not reply_text.startswith("OK GET"):
                    print(reply_text)
                    listener.close()
                    continue
                
                reply_parts = reply_text.split()
                expected_size = int(reply_parts[-1])
                receive_file(listener, filename, expected_size)

            elif cmd == "put":
                if len(parts) != 2:
                    print("Usage: put <filename>")
                    continue

                filename = parts[1]
                if not os.path.isfile(filename):
                    print(f"File not found: {filename}")
                    continue

                listener, data_port = data_listener()
                sendMessage(control_sock, f"put {filename} {data_port}".encode())

                reply = recv_message(control_sock)
                if reply is None:
                    print("No reply from server")
                    listener.close()
                    continue

                reply_text = reply.decode()
                if not reply_text.startswith("OK PUT"):
                    print(reply_text)
                    listener.close()
                    continue

                send_file(listener, filename)

                final_reply = recv_message(control_sock)
                if final_reply:
                    print(final_reply.decode())



            else:
                print("Invalid Command, commands are ls, get <filename>, put <filename>, and quit")
    finally:
        control_sock.close()

if __name__ == "__main__":
    main()