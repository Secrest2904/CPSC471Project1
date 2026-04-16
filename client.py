from socket import *
import os

serverName = "localhost"
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)


def sendData(string):
    dataSocket = socket(AF_INET, SOCK_STREAM)
    dataSocket.bind(("", 0))
    dataSocket.listen(1)
    port = dataSocket.getsockname()[1]
    dataSocket.connect((serverName, port))
    dataSocket.send(string)
    dataSocket.close()

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