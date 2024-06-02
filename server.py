import socket
import urllib.parse
import os
from pathlib import Path

PORT = 8080
BUFFER_SIZE = 4096

# Function to send a response to the client safely
def safe_send(client_socket, data):
    try:
        client_socket.sendall(data)
    except socket.error as e:
        print(f"Send failed: {e}")

# Function to handle the GET requests from the client
def handle_get(client_socket, resource):
    filepath = urllib.parse.unquote(resource)

    if ".." in filepath:
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n\r\nForbidden: Resource access is forbidden.\r\n"
        client_socket.sendall(response.encode())
        return
    
    if filepath == "/":
        filepath += "index.html"
    elif os.path.isdir(Path("./web") / filepath.strip('/')):
        filepath = os.path.join(filepath, "index.html")

    fullpath = Path("./web") / filepath.strip('/')

    try:
        with open(fullpath, "rb") as file:
            content = file.read()
    except FileNotFoundError:
        response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n404 Not Found: The requested resource was not found on this server.\r\n"
        client_socket.sendall(response.encode())
        return

    content_type = "Content-Type: text/plain\r\n"  # Default to text/plain for this example
    if fullpath.suffix in [".html"]:
        content_type = "Content-Type: text/html\r\n"
    elif fullpath.suffix in [".jpg", ".jpeg"]:
        content_type = "Content-Type: image/jpeg\r\n"
    elif fullpath.suffix in [".png"]:
        content_type = "Content-Type: image/png\r\n"
    elif fullpath.suffix in [".css"]:
        content_type = "Content-Type: text/css\r\n"
    elif fullpath.suffix in [".js"]:
        content_type = "Content-Type: application/javascript\r\n"

    # Send header
    response_header = f"HTTP/1.1 200 OK\r\n{content_type}Content-Length: {len(content)}\r\n\r\n"
    client_socket.sendall(response_header.encode())

    # Send file content
    client_socket.sendall(content)

# Put function
def handle_put(client_socket, resource, data):
    filepath = urllib.parse.unquote(resource)

    if ".." in filepath:
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n\r\nForbidden: Resource access is forbidden.\r\n"
        client_socket.sendall(response.encode())
        return

    fullpath = Path("./web") / filepath.strip('/')

    try:
        with open(fullpath, "wb") as file:
            file.write(data)
    except FileNotFoundError:
        response = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\n500 Internal Server Error: Could not open file for writing.\r\n"
        client_socket.sendall(response.encode())
        return

    response = "HTTP/1.1 201 Created\r\nContent-Type: text/plain\r\n\r\n201 Created: File saved successfully.\r\n"
    client_socket.sendall(response.encode())

# Post function
def handle_post(client_socket, resource, data):
    filepath = urllib.parse.unquote(resource)

    if ".." in filepath:
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n\r\nForbidden: Resource access is forbidden.\r\n"
        client_socket.sendall(response.encode())
        return

    fullpath = Path("./web") / filepath.strip('/')

    try:
        with open(fullpath, "ab") as file:
            file.write(data)
    except FileNotFoundError:
        response = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\n500 Internal Server Error: Could not open file for appending.\r\n"
        client_socket.sendall(response.encode())
        return

    response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n200 OK: Data appended successfully.\r\n"
    client_socket.sendall(response.encode())

# Delete function
def handle_delete(client_socket, resource):
    filepath = urllib.parse.unquote(resource)

    if ".." in filepath:
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\n\r\nForbidden: Resource access is forbidden.\r\n"
        client_socket.sendall(response.encode())
        return

    fullpath = Path("./web") / filepath.strip('/')

    try:
        os.remove(fullpath)
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n200 OK: File deleted successfully.\r\n"
    except FileNotFoundError:
        response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n404 Not Found: The requested resource was not found on this server.\r\n"
    
    client_socket.sendall(response.encode())

def handle_request(client_socket, request):
    request_lines = request.split("\r\n")
    request_line = request_lines[0]
    headers = request_lines[1:]
    data = None

    if request_line:
        method, resource, _ = request_line.split()
        data_start = request.find("\r\n\r\n")
        if data_start != -1:
            data = request[data_start+4:]

        try:
            if method == "GET":
                handle_get(client_socket, resource)
            elif method == "PUT":
                if data:
                    handle_put(client_socket, resource, data.encode())
            elif method == "POST":
                if data:
                    handle_post(client_socket, resource, data.encode())
            elif method == "DELETE":
                handle_delete(client_socket, resource)
            else:
                response = "HTTP/1.1 501 Not Implemented\r\nContent-Type: text/plain\r\n\r\nNot Implemented\r\n"
                client_socket.sendall(response.encode())
        except Exception as e:
            print(f"An error occurred: {e}")
            response = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\n500 Internal Server Error: An error occurred on the server.\r\n"
            client_socket.sendall(response.encode())

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))
    server_socket.listen(10)
    print(f"Server listening on port {PORT}...")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Connection accepted from {client_address}")

            # Keep the connection open until explicitly closed by the client
            while True:
                try:
                    request = client_socket.recv(BUFFER_SIZE).decode()
                    if not request:
                        break  # No more data, connection closed by the client

                    handle_request(client_socket, request)

                except socket.error as e:
                    print(f"Error receiving data: {e}")
                    break

            print(f"Connection closed by {client_address}")

        except KeyboardInterrupt:
            print("\nShutting down the server...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            client_socket.close()

    server_socket.close()

if __name__ == "__main__":
    main()
