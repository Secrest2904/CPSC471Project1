from socket import *
import os
import sys

HEADER_SIZE = 10
PACKET_SIZE = 4096
CLOUD_DIR = "cloud"


def ensure_server_dirs():
    try:
        os.makedirs(CLOUD_DIR, exist_ok=True)
    except OSError as e:
        print(f"Directory setup error: {e}")
        sys.exit(1)


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


def send_message(sock, payload: bytes):
    try:
        header = f"{len(payload):<{HEADER_SIZE}}".encode()
        sock.sendall(header + payload)
    except error as e:
        print(f"Send error: {e}")


def recv_message(sock):
    try:
        header = recv_exact(sock, HEADER_SIZE)
        if not header:
            return None

        msg_len = int(header.decode().strip())
        return recv_exact(sock, msg_len)

    except (ValueError, error) as e:
        print(f"Message receive error: {e}")
        return None


def connect_data_socket(client_ip, client_port):
    try:
        data_sock = socket(AF_INET, SOCK_STREAM)
        data_sock.connect((client_ip, client_port))
        return data_sock
    except error as e:
        print(f"Data connection error: {e}")
        return None


def handle_ls(control_sock, client_ip, data_port):
    data_sock = None
    try:
        entries = os.listdir(CLOUD_DIR)
        entries.sort()
        listing = "\n".join(entries)
        if listing:
            listing += "\n"

        data_sock = connect_data_socket(client_ip, data_port)
        if not data_sock:
            raise RuntimeError("Failed to establish data connection")

        send_message(data_sock, listing.encode())
        send_message(control_sock, b"OK LS")
        print("SUCCESS: ls")

    except Exception as e:
        send_message(control_sock, f"ERR LS {e}".encode())
        print(f"FAILURE: ls -> {e}")

    finally:
        if data_sock:
            data_sock.close()


def handle_get(control_sock, client_ip, data_port, filename):
    file_path = os.path.join(CLOUD_DIR, filename)
    data_sock = None

    if not os.path.isfile(file_path):
        send_message(control_sock, f"ERR GET File not found: {filename}".encode())
        print(f"FAILURE: get {filename} -> file not found")
        return

    try:
        file_size = os.path.getsize(file_path)
        send_message(control_sock, f"OK GET {filename} {file_size}".encode())

        data_sock = connect_data_socket(client_ip, data_port)
        if not data_sock:
            raise RuntimeError("Failed to establish data connection")

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(PACKET_SIZE)
                if not chunk:
                    break
                data_sock.sendall(chunk)

        print(f"SUCCESS: get {filename}")

    except (OSError, error) as e:
        send_message(control_sock, f"ERR GET {e}".encode())
        print(f"FAILURE: get {filename} -> {e}")

    finally:
        if data_sock:
            data_sock.close()


def handle_put(control_sock, client_ip, data_port, filename):
    file_path = os.path.join(CLOUD_DIR, filename)
    data_sock = None

    try:
        send_message(control_sock, f"OK PUT {filename}".encode())

        data_sock = connect_data_socket(client_ip, data_port)
        if not data_sock:
            raise RuntimeError("Failed to establish data connection")

        size_header = recv_exact(data_sock, HEADER_SIZE)
        if not size_header:
            raise RuntimeError("Missing file size header")

        try:
            file_size = int(size_header.decode().strip())
        except ValueError:
            raise RuntimeError("Invalid file size received")

        bytes_left = file_size

        with open(file_path, "wb") as f:
            while bytes_left > 0:
                chunk = data_sock.recv(min(PACKET_SIZE, bytes_left))
                if not chunk:
                    raise RuntimeError("Connection closed before file completed")
                f.write(chunk)
                bytes_left -= len(chunk)

        send_message(control_sock, f"OK PUT_DONE {filename}".encode())
        print(f"SUCCESS: put {filename}")

    except (OSError, error, RuntimeError) as e:
        send_message(control_sock, f"ERR PUT {e}".encode())
        print(f"FAILURE: put {filename} -> {e}")

    finally:
        if data_sock:
            data_sock.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <PORTNUMBER>")
        sys.exit(1)

    ensure_server_dirs()

    try:
        server_port = int(sys.argv[1])
    except ValueError:
        print("Port must be an integer")
        sys.exit(1)

    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(("", server_port))
        server_socket.listen(1)
    except error as e:
        print(f"Server setup error: {e}")
        sys.exit(1)

    print(f"Server listening on port {server_port}")
    print(f"Cloud directory: {CLOUD_DIR}/")

    try:
        while True:
            try:
                control_sock, addr = server_socket.accept()
            except error as e:
                print(f"Accept error: {e}")
                continue

            client_ip = addr[0]
            print(f"Control connection from {client_ip}:{addr[1]}")

            try:
                while True:
                    payload = recv_message(control_sock)
                    if payload is None:
                        break

                    try:
                        message = payload.decode().strip()
                    except UnicodeDecodeError:
                        send_message(control_sock, b"Error: Invalid encoding")
                        continue

                    parts = message.split()
                    if not parts:
                        send_message(control_sock, b"Error: Empty Command")
                        continue

                    cmd = parts[0].lower()

                    if cmd == "quit":
                        send_message(control_sock, b"OK QUIT")
                        print("Successfully quit")
                        break

                    elif cmd == "ls":
                        if len(parts) != 2:
                            send_message(control_sock, b"Error Usage: ls <port>")
                            continue
                        try:
                            data_port = int(parts[1])
                        except ValueError:
                            send_message(control_sock, b"Invalid port")
                            continue
                        handle_ls(control_sock, client_ip, data_port)

                    elif cmd == "get":
                        if len(parts) != 3:
                            send_message(control_sock, b"Error Usage: get <filename> <port>")
                            continue
                        filename = parts[1]
                        try:
                            data_port = int(parts[2])
                        except ValueError:
                            send_message(control_sock, b"Invalid port")
                            continue
                        handle_get(control_sock, client_ip, data_port, filename)

                    elif cmd == "put":
                        if len(parts) != 3:
                            send_message(control_sock, b"Error Usage: put <filename> <port>")
                            continue
                        filename = parts[1]
                        try:
                            data_port = int(parts[2])
                        except ValueError:
                            send_message(control_sock, b"Invalid port")
                            continue
                        handle_put(control_sock, client_ip, data_port, filename)

                    else:
                        send_message(control_sock, b"Error: Unknown Command")

            except Exception as e:
                print(f"Connection error: {e}")

            finally:
                control_sock.close()
                print("Connection closed")

    except KeyboardInterrupt:
        print("\nServer shutting down...")

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()