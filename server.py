import socket
import threading
from datetime import datetime 

HOST = '127.0.0.1'
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = {}  # client socket -> nickname
last_dm_partner = {} # client socket -> last DM sender socket

print(f"[SERVER RUNNING] on {HOST}:{PORT}")

def broadcast(message, _client=None):
    """Send message to all clients except _client if specified"""
    for client in list(clients.keys()):
        if client != _client:
            try:
                client.send(message)
            except:
                client.close()
                if client in clients:
                    del clients[client]
                if client in last_dm_partner:
                    del last_dm_partner[client]

def send_user_list(client):
    """Send numbered list of current users to a client"""
    if len(clients) > 1:
        message = "[INFO] Current users:\n"
        client_list = list(clients.keys())
        for idx, c in enumerate(client_list):
            name = clients[c]
            message += f"{idx + 1}) {name}\n"
        client.send(message.encode('utf-8'))
    else:
        client.send("[INFO] You are the only one here.\n".encode('utf-8'))

def handle_client(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break

            msg_decoded = message.decode('utf-8')

            if msg_decoded == "[ping]":
                continue

            # ## MODIFIED ## Add timestamp to all messages
            timestamp = datetime.now().strftime('%H:%M')

            if msg_decoded.lower() == "/users":
                send_user_list(client)

            elif msg_decoded.startswith("/msg"):
                try:
                    parts = msg_decoded.split(" ", 2)
                    num = int(parts[1]) - 1
                    text = parts[2]
                    client_list = list(clients.keys())
                    
                    if 0 <= num < len(client_list):
                        target_client = client_list[num]
                        sender = clients[client]
                        
                        # ## MODIFIED ## Add timestamp and better formatting
                        dm = f"({timestamp}) [DM from {sender}]: {text}"
                        target_client.send(dm.encode('utf-8'))
                        
                        last_dm_partner[target_client] = client
                        client.send(f"[INFO] Message sent to {clients[target_client]}.\n".encode('utf-8'))
                    else:
                         client.send("[!] User number is out of range.\n".encode('utf-8'))
                except (IndexError, ValueError):
                    client.send("[!] Invalid DM format. Use: /msg <number> <message>\n".encode('utf-8'))

            elif msg_decoded.startswith("/r ") or msg_decoded.startswith("/reply "):
                try:
                    text = msg_decoded.split(" ", 1)[1]
                    if client in last_dm_partner:
                        target_client = last_dm_partner[client]
                        sender = clients[client]
                        
                        if target_client in clients:
                            # ## MODIFIED ## Add timestamp and better formatting
                            dm = f"({timestamp}) [DM from {sender}]: {text}"
                            target_client.send(dm.encode('utf-8'))
                            last_dm_partner[target_client] = client
                        else:
                            client.send("[!] The user you are replying to has disconnected.\n".encode('utf-8'))
                    else:
                        client.send("[!] You have no one to reply to.\n".encode('utf-8'))
                except IndexError:
                    client.send("[!] Invalid reply format. Use: /r <message>\n".encode('utf-8'))

            else:
                # ## MODIFIED ## Add timestamp to broadcast message
                full_message = f"({timestamp}) {clients[client]}: {msg_decoded}".encode('utf-8')
                broadcast(full_message, client)

        except:
            break

    if client in clients:
        nickname = clients[client]
        print(f"[DISCONNECT] {nickname} left the chat")
        broadcast(f"({datetime.now().strftime('%H:%M')}) {nickname} has left the chat.\n".encode('utf-8'))
        del clients[client]
        if client in last_dm_partner:
            del last_dm_partner[client]
    client.close()

def receive():
    while True:
        try:
            client, address = server.accept()
            client.send("NICK".encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            clients[client] = nickname
            print(f"[NEW CONNECTION] {nickname} connected from {address}")

            # ## MODIFIED ## Added a hint about replying to DMs
            client.send("Connected! Commands: /users, /msg <num> <msg>, /r <msg>\n".encode('utf-8'))
            
            broadcast(f"({datetime.now().strftime('%H:%M')}) {nickname} joined the chat!\n".encode('utf-8'), client)
            send_user_list(client)

            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()
        except OSError:
            break

def server_console():
    while True:
        msg = input('')
        if msg.lower() == "/disconnect":
            print("[SERVER] Shutting down.")
            broadcast("[SERVER] Server is shutting down.\n".encode('utf-8'))
            for client in list(clients.keys()): client.close()
            server.close()
            break
        else:
            broadcast(f"[SERVER] {msg}".encode('utf-8'))

threading.Thread(target=server_console, daemon=True).start()
receive()
print("[SERVER] Closed.")