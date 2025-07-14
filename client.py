import socket
import os
from pathlib import Path

BUFFER_SIZE = 1024

client_socket = None
is_connected = False
registered_user = None

DOWNLOADS_FOLDER = Path.home() / "Downloads" / "Calvara's Server Dump"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

CLIENT_SEND_FOLDER = os.path.join(os.getcwd(), "Shopee Delivery")
os.makedirs(CLIENT_SEND_FOLDER, exist_ok=True)

# Connect to the server
def Im_In(ip, port):
    global client_socket, is_connected

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((ip, port))
        is_connected = True
        print("\nYou have connected to the Calvara Server!")

    except Exception as e:
        print(f"[ERROR] Something went wrong, server connection failed :(\n{e}")

# Disconnect from the server
def red_button():
    global client_socket, is_connected, registered_user

    if is_connected:
        try:
            client_socket.close()
        except OSError:
            pass

        is_connected = False
        registered_user = None

        print("Connection closed. Your files are safe here!")

# License and registration please
def enlistment(handle):
    global registered_user

    if registered_user is not None:
        print("[ERROR]: Only one person can be registered at a time.\nCurrent user must leave the session to register again.")
        return
    
    try:
        client_socket.send(f"/register {handle}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()

        if response.startswith("REGISTER_OK"):
            registered_user = handle

            print(f"Registration successful:{response[12:]}")
        else:
            print(f"Registration failed:{response[15:]}")
    except (ConnectionResetError, BrokenPipeError, OSError):
        global is_connected
        is_connected = False
        print("[SERVER ERROR] Connection lost. Please reconnect to the server")

# Drops the file to the server
def dump_file(filename):
    try:    
        filepath = os.path.join(CLIENT_SEND_FOLDER, filename)
        if os.path.exists(filepath):
            try:
                client_socket.send(f"/store {filename}".encode())
                response = client_socket.recv(BUFFER_SIZE).decode()

                if response == "STORE_READY":
                    file_size = os.path.getsize(filepath)
                    client_socket.send(str(file_size).encode())

                    with open(filepath, 'rb') as file:
                        while chunk := file.read(BUFFER_SIZE):
                            client_socket.send(chunk)

                    response = client_socket.recv(BUFFER_SIZE).decode()
                    if response.startswith("STORE_OK"):
                        print(response[9:])  # Success message
                    else:
                        print(f"[Server Error]{response[12:]}")
                else:
                    print(f"Unexpected server response:{response[12:]}")
            except Exception as e:
                print(f"[ERROR] {e}")
        else:
            print(f"[ERROR] File '{filename}' not found in the '{CLIENT_SEND_FOLDER}' folder.")

    except (ConnectionResetError, BrokenPipeError, OSError):
        global is_connected
        is_connected = False
        print("[SERVER ERROR] Connection lost. Please reconnect to the server")  

# Politely asks the server if they can see what they have
def file_peeper():
    try:    
        client_socket.send("/dir".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()

        if response.startswith("DIR_OK"):
            print("Server Directory:")
            print(response[7:])
        elif response == "DIR_EMPTY":
            print("Server Directory is empty.")
        else:
            print(response)
    except (ConnectionResetError, BrokenPipeError, OSError):
        global is_connected
        is_connected = False
        print("[SERVER ERROR] Connection lost. Please reconnect to the server")  
      
# Politely asks the server if they can take the file :)
def yoink_file(filename):
    try:
        client_socket.send(f"/get {filename}".encode())
        response = client_socket.recv(BUFFER_SIZE).decode()

        if response.startswith("GET_READY"):
            _, file_size = response.split()
            file_size = int(file_size)
            filepath = os.path.join(DOWNLOADS_FOLDER, filename)
            bytes_received = 0

            with open(filepath, 'wb') as file:
                while bytes_received < file_size:
                    chunk = client_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    file.write(chunk)
                    bytes_received += len(chunk)

                if bytes_received == file_size:
                    print(f"File '{filename}' downloaded to {DOWNLOADS_FOLDER}.")
                else:
                    print(f"[SERVER ERROR] Incomplete file received. {bytes_received}/{file_size} bytes.")
        else:
            print(f"[ERROR]{response[9:]}")
    except (ConnectionResetError, BrokenPipeError, OSError):
        global is_connected
        is_connected = False
        print("[SERVER ERROR] Connection lost. Please reconnect to the server")

# Display help (/?) menu
def helppp():
    print("""
    Available commands:
    /join <server_ip> <port>        - Connect to the server
    /leave                          - Disconnect from the server
    /register <handle>              - Register a unique handle
    /store <filename>               - Send a file to the server
    /dir                            - Request directory file list
    /get <filename>                 - Fetch a file from the server
    /?                              - Show command help
    """)

def hello_there():
    print("""
    Welcome to the Calvara File Exchange Service!
    For commands type /?""")

# Main client loop
def client_program():
    global is_connected
    hello_there()

    while True:
        command = input("\nEnter command: ").strip()
        
        if not is_connected and not command.startswith(("/join", "/?")):
            if not command.startswith(("/register", "/leave", "/store", "/dir", "/get")):
                print("[ERROR] Invalid command")
                continue
            else:
                print("[ERROR] You must be connected to the server first to use this command.")
                continue

        if command.startswith("/join"):
            try:
                _, ip, port = command.split()
                Im_In(ip, int(port))
            except ValueError:
                print("[ERROR] Invalid syntax. Use /join <server_ip> <port>.")
        
        elif command.startswith("/leave"):
            red_button()
        
        elif command.startswith("/register"):
            try:
                _, handle = command.split()
                enlistment(handle)
            except ValueError:
                print("[ERROR] Invalid syntax. Use /register <handle>.")
        
        elif command.startswith("/store"):
            try:
                _, filename = command.split()
                dump_file(filename)
            except ValueError:
                print("[ERROR] Invalid syntax. Use /store <filename>.")
        
        elif command == "/dir":
            file_peeper()
        
        elif command.startswith("/get"):
            try:
                _, filename = command.split()
                yoink_file(filename)
            except ValueError:
                print("[ERROR] Invalid syntax. Use /get <filename>.")
        
        elif command == "/?":
            helppp()
        
        else:
            print("[ERROR] Invalid command.")

client_program()