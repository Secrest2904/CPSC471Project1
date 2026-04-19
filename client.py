from socket import *
import os
import sys

HEADER_SIZE = 10
PACKET_SIZE = 4096
DOWNLOAD_DIRECTORY = "Downloads_471"

def check_directory():
    os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)


serverName = "localhost"
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)


def sendMessage(sock, payload: bytes):
    header = f"{len(payload):<{HEADER_SIZE}}".encode()

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
    listener.bind("", 0)
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
            receive_file.write(chunk)
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
            chunk = f.read(PACKET_SIZE)
            if not chunk:
                break
            dataConnection.sendall(chunk)
            bytes_sent += len(chunk)
    dataConnection.close()
    listener.close()

    print(f"Successfully transferred {filename} as {bytes_sent} bytes")

while True:
    command = str(input(">> "))
    task = command.strip().split()
    if task[0] == "quit":
        break
    elif task[0] == "ls":
        sendData("ls")
    elif task[0] == "get":
        try:
            sendData(task)
            print("File request sent to the server")
        except:
            print("Unable to send data to the server")
    elif task[0] == "put":
        try:
            sendData(fileAccess(task[1]))
            print(f"Successfully sent file: {task[1]}")
        except:
            print(f"File {task[1]} failed to send")
    else:
        print("Please use the following commands: quit, ls, get 'filename', or put 'filename'")

clientSocket.close()