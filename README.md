# CPSC 471 - Programming Assignment 1: Simplified FTP

## Group Members

| Name | Email |
|------|-------|
| Nathan Dulkis | ndulkis@csu.fullerton.edu |
| [Partner Name] | [partner@email.com] |
| [Partner Name] | [partner@email.com] |

## Programming Language

Python 3

## Execution Instructions

### Start the Server
```
python server.py <PORTNUMBER>
```
Example:
```
python server.py 12000
```
The server will create a `cloud/` directory in the current folder. Files uploaded by clients are stored there and served from there.

### Start the Client
```
python client.py <server_host> <server_port>
```
Example (same machine):
```
python client.py localhost 12000
```
The client will create a `download/` directory in the current folder where received files are saved.

### Available Commands

| Command | Description |
|---------|-------------|
| `ls` | List files available on the server |
| `get <filename>` | Download a file from the server into `download/` |
| `put <filename>` | Upload a local file to the server's `cloud/` folder |
| `quit` | Disconnect from the server and exit |


