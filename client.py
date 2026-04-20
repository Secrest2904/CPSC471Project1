from socket import *
import os
import sys

HEADER_SIZE = 10
PACKET_SIZE = 4096
DOWNLOAD_DIRECTORY = "Downloads_471"


def check_directory():
    try:
        os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)
    except OSError as e:
        print(f"Directory error: {e}")
        sys.exit(1)


def sendMessage(sock, payload: bytes):
    try:
        header = f"{len(payload):<{HEADER_SIZE}}".encode()
        sock.sendall(header + payload)
    except error as e:
        print(f"Send error: {e}")


def recv_exact(sock, num_bytes):
    data = b""
    try:
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
    except error as e:
        print(f"Receive error: {e}")
        return None
    return data


def recv_message(sock):
    try:
        header = recv_exact(sock, HEADER_SIZE)
        if not header:
            return None
        messageLength = int(header.decode().strip())
        return recv_exact(sock, messageLength)
    except (ValueError, error) as e:
        print(f"Message receive error: {e}")
        return None


def data_listener():
    try:
        listener = socket(AF_INET, SOCK_STREAM)
        listener.bind(("", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        return listener, port
    except error as e:
        print(f"Listener error: {e}")
        return None, None


def receive_listening(listener):
    try:
        dataConnection, _ = listener.accept()
        payload = recv_message(dataConnection)
        if payload is None:
            print("Error while listening")
            return

        try:
            text = payload.decode()
            if text:
                print(text, end="")
            else:
                print("No files on the server")
        except UnicodeDecodeError:
            print("Decode error")

    except error as e:
        print(f"Listening error: {e}")
    finally:
        try:
            dataConnection.close()
            listener.close()
        except:
            pass


def receive_file(listener, filename, expected_size):
    filepath = os.path.join(DOWNLOAD_DIRECTORY, filename)

    try:
        dataConnection, _ = listener.accept()
        bytes_received = 0

        with open(filepath, "wb") as receivedFile:
            while bytes_received < expected_size:
                chunk = dataConnection.recv(min(PACKET_SIZE, expected_size - bytes_received))
                if not chunk:
                    break
                receivedFile.write(chunk)
                bytes_received += len(chunk)

        print(f"{filename} {bytes_received} bytes successfully received")
        print(f"Saved to: {filepath}")

    except (error, OSError) as e:
        print(f"File receive error: {e}")
    finally:
        try:
            dataConnection.close()
            listener.close()
        except:
            pass


def send_file(listener, filename):
    try:
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

        print(f"Successfully transferred {filename} as {bytes_sent} bytes")

    except (error, OSError) as e:
        print(f"File send error: {e}")
    finally:
        try:
            dataConnection.close()
            listener.close()
        except:
            pass


def main():
    if len(sys.argv) != 3:
        print("Error: run python client.py <server> <port>")
        sys.exit(1)

    check_directory()

    try:
        serverName = sys.argv[1]
        serverPort = int(sys.argv[2])
    except ValueError:
        print("Port must be an integer")
        sys.exit(1)

    try:
        control_sock = socket(AF_INET, SOCK_STREAM)
        control_sock.connect((serverName, serverPort))
    except error as e:
        print(f"Connection error: {e}")
        sys.exit(1)

    print(f"Connected to {serverName}:{serverPort}")
    print(f"Download directory: {DOWNLOAD_DIRECTORY}/")

    try:
        while True:
            try:
                command = input(">> ").strip()
            except EOFError:
                break

            if not command:
                continue

            parts = command.split()
            cmd = parts[0].lower()

            if cmd == "quit":
                sendMessage(control_sock, b"quit")
                reply = recv_message(control_sock)
                if reply:
                    print(reply.decode(errors="ignore"))
                break

            elif cmd == "ls":
                if len(parts) != 1:
                    print("ls should be used on its own")
                    continue

                listener, data_port = data_listener()
                if not listener:
                    continue

                sendMessage(control_sock, f"ls {data_port}".encode())
                receive_listening(listener)

                reply = recv_message(control_sock)
                if reply:
                    print(reply.decode(errors="ignore"))

            elif cmd == "get":
                if len(parts) != 2:
                    print("Usage: get <filename>")
                    continue

                filename = parts[1]
                listener, data_port = data_listener()
                if not listener:
                    continue

                sendMessage(control_sock, f"get {filename} {data_port}".encode())

                reply = recv_message(control_sock)
                if not reply:
                    print("No reply from server")
                    listener.close()
                    continue

                reply_text = reply.decode(errors="ignore")
                if not reply_text.startswith("OK GET"):
                    print(reply_text)
                    listener.close()
                    continue

                try:
                    expected_size = int(reply_text.split()[-1])
                except ValueError:
                    print("Invalid file size from server")
                    listener.close()
                    continue

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
                if not listener:
                    continue

                sendMessage(control_sock, f"put {filename} {data_port}".encode())

                reply = recv_message(control_sock)
                if not reply:
                    print("No reply from server")
                    listener.close()
                    continue

                reply_text = reply.decode(errors="ignore")
                if not reply_text.startswith("OK PUT"):
                    print(reply_text)
                    listener.close()
                    continue

                send_file(listener, filename)

                final_reply = recv_message(control_sock)
                if final_reply:
                    print(final_reply.decode(errors="ignore"))

            else:
                print("Invalid command")

    except KeyboardInterrupt:
        print("\nClient shutting down...")

    finally:
        try:
            control_sock.close()
        except:
            pass


if __name__ == "__main__":
    main()