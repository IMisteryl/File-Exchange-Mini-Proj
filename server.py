import socket
import threading
import os
from pathlib import Path
from datetime import datetime

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

STORAGE_FOLDER = './Home Depot/'

os.makedirs(STORAGE_FOLDER, exist_ok=True)

registered_users = set()

def timestamp():
    return datetime.now().strftime("<%Y-%m-%d %H:%M:%S>")

# Handles registration
def registrar(client_socket, msg):
    try:
        _, handle = msg.split()

        if handle in registered_users:
            client_socket.send("REGISTER_ERROR: Handle already exists.".encode())
        else:
            registered_users.add(handle)
            client_socket.send(f"REGISTER_OK: Welcome {handle}!".encode())
            print(f"{timestamp()} [NOTICE] Handle '{handle}' has been registered in the session")

    except Exception as e:
        client_socket.send(f"REGISTER_ERROR: {e}".encode())

# Handles the storing of files
def courier(client_socket, msg, client_handle):
    if client_handle is None:
        client_socket.send("STORE_ERROR: You must register first.".encode())
        return

    try:
        _, filename = msg.split(maxsplit=1)
        sanitized_filename = Path(filename).name
        filepath = os.path.join(STORAGE_FOLDER, sanitized_filename)

        client_socket.send("STORE_READY".encode())

        file_size = int(client_socket.recv(BUFFER_SIZE).decode())
        bytes_received = 0

        with open(filepath, 'wb') as file:
            while bytes_received <  file_size :
                chunk = client_socket.recv(BUFFER_SIZE)
                if not chunk: 
                    break

                file.write(chunk)
                bytes_received += len(chunk)
            
            if bytes_received == file_size:
                client_socket.send(f"STORE_OK: File '{sanitized_filename}' uploaded successfully.".encode())
            else:
                client_socket.send(f"STORE_ERROR: Incomplete file transfer. Recieved {bytes_received}/{file_size} bytes.".encode())
    except Exception as e:
        client_socket.send(f"STORE_ERROR: {e}".encode())

# Handles the directory
def inventory(client_socket, client_handle):
    if client_handle is None:
        client_socket.send("You must register first.".encode())
        return
    
    try:
        files = os.listdir(STORAGE_FOLDER)
        if files:
            directory_list = "DIR_OK:\n" + "\n".join(files)
            client_socket.send(directory_list.encode())
        else:
            client_socket.send("DIR_EMPTY".encode())

    except Exception as e:
        client_socket.send(f"DIR_ERROR: {e}".encode())

# handles the /get commande
def delivery_rider(client_socket, msg, client_handle):
    if client_handle is None:
        client_socket.send("GET_ERROR: You must register first.".encode())
        return

    try:
        _, filename = msg.split()
        sanitized_filename = Path(filename).name
        filepath = os.path.join(STORAGE_FOLDER, sanitized_filename)

        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            client_socket.send(f"GET_READY {file_size}".encode())

            with open(filepath, 'rb') as file:
                while chunk := file.read(BUFFER_SIZE):
                    client_socket.send(chunk)
        else:
            client_socket.send("GET_ERROR: File not found.".encode())

    except Exception as e:
        client_socket.send(f"GET_ERROR: {e}".encode())

# Handles the client
def boss_man(client_socket, client_address):
    client_handle = None
    print(f"{timestamp()} [NEW CONNECTION] {client_address} connected.")

    try:
        while True:
            msg = client_socket.recv(BUFFER_SIZE).decode()
            if not msg:
                print(f"{timestamp()} [DISCONNECTED] {client_address} has disconnected.")
                break

            if msg.startswith("/register"):
                registrar(client_socket, msg)
                client_handle = msg.split()[1]
            elif msg.startswith("/store"):
                courier(client_socket, msg, client_handle)
            elif msg.startswith("/dir"):
                inventory(client_socket, client_handle)
            elif msg.startswith("/get"):
                delivery_rider(client_socket, msg, client_handle)
            else:
                client_socket.send("ERROR: Unknown command.".encode())
    except Exception as e:
        print(f"{timestamp()} [ERROR] {e}")

    finally:
        if client_handle and client_handle in registered_users:
            registered_users.remove(client_handle)
            print(f"{timestamp()} [NOTICE] Handle '{client_handle}' removed from this session's registered users.") 
        client_socket.close()

# Start Server
def locked_in():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen()
    print(f"{timestamp()} [LISTENING] Server is listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server.accept()
        thread = threading.Thread(target=boss_man, args=(client_socket, client_address))
        thread.start()
        print(f"{timestamp()} [ACTIVE CONNECTIONS] {threading.active_count() - 1}")

locked_in()