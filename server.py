from socket import *

serverport = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverport))

serverSocket.listen(1)

print(f"Server is live and listening on port {serverport}")


data = ""

while True:
    connectionSocket, addr = serverSocket.accept()

    data = connectionSocket.recv(40)

    print(data)
    connectionSocket.close()