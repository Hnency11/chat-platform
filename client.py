import asyncio
import websockets
import json
import threading
import sys
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# Store my keys
MY_PRIVATE_KEY = None
MY_PUBLIC_PEM = None

# Store others' public keys: {username: rsa_public_key_object}
key_store = {}

# Pending key requests: {target_username: asyncio.Event}
key_events = {}

# Hardcoded key for Groups (Fallback)
GROUP_KEY = b'Z7w1B8td3b1N0c9n0m8-j0n7I6k5l4m3n2o1p0q9r8s=' 
group_cipher = Fernet(GROUP_KEY)

def generate_keys():
    global MY_PRIVATE_KEY, MY_PUBLIC_PEM
    print("Generating RSA keys...")
    MY_PRIVATE_KEY = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = MY_PRIVATE_KEY.public_key()
    MY_PUBLIC_PEM = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

async def listen(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if "status" in data:
                print(f"[Server] {data['message']}")
                # If server advertises a default model, show it
                default_model = data.get("default_model")
                if default_model:
                    print(f"[Server] Default model: {default_model}")
            
            elif "type" in data:
                msg_type = data["type"]

                if msg_type == "pub_key":
                    # Received a requested public key
                    username = data["username"]
                    pem = data["key"]
                    pub_key = serialization.load_pem_public_key(pem.encode('utf-8'))
                    key_store[username] = pub_key
                    if username in key_events:
                        key_events[username].set() # Wake up sender
                
                elif msg_type == "private":
                    sender = data['from']
                    try:
                        # 1. Decrypt Fernet Key with My Private Key
                        encrypted_key_b64 = data.get('encrypted_key')
                        if not encrypted_key_b64:
                            print(f"\n[Private from {sender}]: <Missing Key>")
                            continue
                        
                        encrypted_key = base64.b64decode(encrypted_key_b64)
                        
                        fernet_key = MY_PRIVATE_KEY.decrypt(
                            encrypted_key,
                            padding.OAEP(
                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(),
                                label=None
                            )
                        )
                        
                        # 2. Decrypt Content using Fernet Key
                        temp_cipher = Fernet(fernet_key)
                        encrypted_content = data['content']
                        decrypted_content = temp_cipher.decrypt(encrypted_content.encode()).decode()
                        print(f"\n[Private from {sender}]: {decrypted_content}")
                        
                    except Exception as e:
                        print(f"\n[Private from {sender}]: <Decryption Error: {e}>")

                elif msg_type == "group":
                    # Fallback to shared key for groups
                    try:
                        encrypted_content = data['content']
                        decrypted_content = group_cipher.decrypt(encrypted_content.encode()).decode()
                        print(f"\n[Group {data['group']} - {data['from']}]: {decrypted_content}")
                    except Exception as e:
                         print(f"\n[Group {data['group']} - {data['from']}]: <Decryption Error: {e}>")

    except websockets.exceptions.ConnectionClosed:
        print("\nDisconnected from server.")
        sys.exit(0)

def handle_input(loop, websocket):
    print("Commands: /msg <user> <text>, /join <group>, /group <group> <text>, /quit")
    while True:
        try:
            text = input()
            if not text:
                continue
            
            if text.startswith("/quit"):
                print("Quitting...")
                asyncio.run_coroutine_threadsafe(websocket.close(), loop)
                break
            
            elif text.startswith("/msg"):
                parts = text.split(" ", 2)
                if len(parts) >= 3:
                    target = parts[1]
                    content = parts[2]
                    
                    # Logic to ensure we have the key, then encrypt
                    asyncio.run_coroutine_threadsafe(send_private_message(websocket, target, content), loop)
                else:
                    print("Usage: /msg <user> <text>")
            
            elif text.startswith("/join"):
                parts = text.split(" ", 1)
                if len(parts) >= 2:
                    group = parts[1]
                    msg = {"action": "join_group", "group": group}
                    asyncio.run_coroutine_threadsafe(websocket.send(json.dumps(msg)), loop)
                else:
                    print("Usage: /join <group>")

            elif text.startswith("/group"):
                parts = text.split(" ", 2)
                if len(parts) >= 3:
                    group = parts[1]
                    content = parts[2]
                    # Encrypt content with shared group key
                    encrypted_content = group_cipher.encrypt(content.encode()).decode()
                    
                    msg = {"action": "group", "group": group, "content": encrypted_content}
                    asyncio.run_coroutine_threadsafe(websocket.send(json.dumps(msg)), loop)
                else:
                    print("Usage: /group <group> <text>")

            else:
                print("Unknown command.")
        except EOFError:
            break

async def send_private_message(websocket, target, content):
    # 1. Check if we have the key
    if target not in key_store:
        print(f"Fetching public key for {target}...")
        key_events[target] = asyncio.Event()
        await websocket.send(json.dumps({"action": "get_key", "target": target}))
        
        try:
            # Wait for key response (timeout 5s)
            await asyncio.wait_for(key_events[target].wait(), timeout=5.0)
            del key_events[target]
        except asyncio.TimeoutError:
            print(f"Error: Could not retrieve public key for {target}")
            return # Abort

    # 2. Generate a One-Time Session Key (Fernet)
    session_key = Fernet.generate_key()
    session_cipher = Fernet(session_key)
    
    # 3. Encrypt Content with Session Key
    encrypted_content = session_cipher.encrypt(content.encode()).decode()
    
    # 4. Encrypt Session Key with Target's RSA Key
    target_pub_key = key_store[target]
    encrypted_key = target_pub_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    # Base64 encode the binary encrypted key to send via JSON
    encrypted_key_b64 = base64.b64encode(encrypted_key).decode('utf-8')
    
    # 5. Send
    msg = {
        "action": "private", 
        "target": target, 
        "content": encrypted_content,
        "encrypted_key": encrypted_key_b64
    }
    await websocket.send(json.dumps(msg))


async def start_client():
    generate_keys()
    
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        username = input("Enter your username: ")
        # Send Public Key on Login
        await websocket.send(json.dumps({
            "action": "login", 
            "username": username,
            "public_key": MY_PUBLIC_PEM
        }))
        
        loop = asyncio.get_running_loop()
        input_thread = threading.Thread(target=handle_input, args=(loop, websocket))
        input_thread.daemon = True
        input_thread.start()
        
        await listen(websocket)

if __name__ == "__main__":
    try:
        asyncio.run(start_client())
    except KeyboardInterrupt:
        print("\nClient stopped.")
