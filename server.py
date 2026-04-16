from socket import *
import os
import sys

HEADER_SIZE = 10
PACKET_SIZE = 4096

os.makedirs("cloud", exist_ok=True)
os.makedirs("download", exist_ok=True)


serverport = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverport))
serverSocket.listen(1)

print(f"Server is live and listening on port {serverport}")

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