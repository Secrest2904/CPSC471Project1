from socket import *

serverName = "localhost"
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)

clientSocket.connect((serverName, serverPort))

data = "Hello, this is a test string"

clientSocket.send(data.encode())
clientSocket.close()