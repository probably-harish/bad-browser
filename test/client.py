import socket
import ssl
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 8081))

    private_key, public_key = generate_key_pair()
    server_public_key = client_socket.recv(2048)
    server_public_key = serialization.load_pem_public_key(server_public_key, backend=default_backend())

    shared_key = b"SharedKey"  # This key should be generated securely in a real-world scenario

    encrypted_key = server_public_key.encrypt(
        shared_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),  # Fix this line
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    client_socket.sendall(encrypted_key)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_verify_locations(cafile="server.crt")

    connection = context.wrap_socket(client_socket, server_hostname='localhost')

    message = b"Hello, server!"
    connection.sendall(message)

    data = connection.recv(1024)
    print(f"Received: {data.decode()}")

    connection.close()

if __name__ == "__main__":
    client()
