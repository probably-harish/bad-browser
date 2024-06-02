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

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 8081))
    server_socket.listen(1)

    print("Server listening on port 8081...")

    while True:
        connection, client_address = server_socket.accept()
        print(f"Connection from {client_address}")

        private_key, public_key = generate_key_pair()
        connection.sendall(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

        encrypted_key = connection.recv(2048)
        shared_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),  # Fix this line
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
        context.set_ciphers("ECDHE-RSA-AES128-GCM-SHA256")
        context.load_dh_params("dhparams.pem")
        context.set_alpn_protocols(["http/1.1"])

        #connection = context.wrap_socket(connection, server_side=True)

        data = connection.recv(1024)
        print(f"Received: {data.decode()}")

        connection.sendall(b"Hello, client!")

        connection.close()

if __name__ == "__main__":
    server()
