from socket import *

serverName = "localhost"
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)

clientSocket.connect((serverName, serverPort))

data = "Hello, this is a test string. Now what happens if I make it extremely long and potentially exceed the socket send length"
bytessent = 0

while bytessent != len(data):
    bytessent += clientSocket.send(data[bytessent:].encode())

clientSocket.close()