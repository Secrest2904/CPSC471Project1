from socket import *
import os

serverName = "localhost"
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)
dataSocket = socket(AF_INET, SOCK_STREAM)

clientSocket.connect((serverName, serverPort))

while True:
    command = str(input(">> "))
    task = command.strip().split()
    if task == "quit":
        break

#    dataSocket.bind(("", 0))
#    dataSocket.listen(1)
#    port = dataSocket.getsockname()[1]
#    dataSocket.connect((serverName, port))
    if task == "ls":
        dataSocket.send("ls".encode())

clientSocket.close()