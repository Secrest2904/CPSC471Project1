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

def fileAccess(filename):
    try:
        with open(filename, "rb") as file:
            sendableBytes = file.read()
            return sendableBytes
    except:
        print("Invalid file")


clientSocket.connect((serverName, serverPort))

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