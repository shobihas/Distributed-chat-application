import socket
import threading

HOST = '127.0.0.1'
PORT = 5556

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = {}
print(f"[BACKUP SERVER RUNNING] on {HOST}:{PORT}")

def broadcast(message, _client=None):
    for client in clients:
        if client != _client:
            try:
                client.send(message)
            except:
                client.close()
                del clients[client]

def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break
            if message.decode('utf-8') != "[ping]":
                broadcast(message, client)
        except:
            break

    nickname = clients[client]
    print(f"[DISCONNECT] {nickname} left the backup chat")
    broadcast(f"{nickname} has left the backup chat.\n".encode('utf-8'))
    del clients[client]
    client.close()

def receive():
    while True:
        client, address = server.accept()
        client.send("NICK".encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        clients[client] = nickname
        print(f"[NEW CONNECTION] {nickname} connected to BACKUP from {address}")
        broadcast(f"{nickname} joined backup chat!\n".encode('utf-8'))
        client.send("Connected to backup server!\n".encode('utf-8'))
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

receive()
