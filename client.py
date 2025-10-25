import socket
import threading
import time
import sys

nickname = input("Enter your nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect(('127.0.0.1', 5555))
    print("[Connected to Main Server]")
except ConnectionRefusedError:
    print("[!] Main server down, attempting to connect to backup...")
    try:
        client.connect(('127.0.0.1', 5556))
        print("[Connected to Backup Server]")
    except ConnectionRefusedError:
        print("[!] Both servers are down. Exiting.")
        sys.exit()

stop_thread = False

def receive():
    global stop_thread
    while not stop_thread:
        try:
            message = client.recv(1024).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            elif not message:
                raise ConnectionResetError
            else:
                sys.stdout.write('\r' + ' ' * 80 + '\r')
                print(message)  
                print(f"{nickname}> ", end="", flush=True)

        except:
            if not stop_thread:
                print("\r[!] Connection to the server has been lost.")
                stop_thread = True
            break

def write():
    print("You can now start chatting. Type /exit to leave.")
    while not stop_thread:
        try:
            msg = input(f"{nickname}> ")
            if stop_thread:
                break
            
            if msg.lower() == "/exit":
                client.close()
                break
            
            # Send the message only if it's not empty
            if msg:
                client.send(msg.encode('utf-8'))

        except (EOFError, KeyboardInterrupt):
            client.close()
            break
        except:
            break

def heartbeat():
    while not stop_thread:
        try:
            client.send(b"[ping]")
            time.sleep(10)
        except:
            break

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

receive_thread.join()
write_thread.join()
print("Client has shut down.")
