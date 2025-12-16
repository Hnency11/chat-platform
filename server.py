import asyncio
import websockets
import json
import database

# Initialize Database
database.init_db()
import os

# Store connected users: {username: websocket}
# Store connected users: {username: websocket}
connected_users = {}
# Store public keys: {username: pem_string}
public_keys = database.get_all_users()

# Store groups: {group_name: {set of usernames}}
groups = database.get_all_groups()

async def handle_connection(websocket):
    username = None
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")

            if action == "login":
                username = data.get("username")
                pub_key = data.get("public_key")
                
                if username in connected_users:
                    await websocket.send(json.dumps({"status": "error", "message": "Username already taken"}))
                    username = None 
                else:
                    connected_users[username] = websocket
                    if pub_key:
                        public_keys[username] = pub_key
                        database.add_user(username, pub_key)
                    print(f"User logged in: {username}")
                    # Advertise default model to clients (can be overridden via env)
                    default_model = os.environ.get("DEFAULT_MODEL", "claude-haiku-4.5")
                    await websocket.send(json.dumps({
                        "status": "success",
                        "message": f"Welcome {username}!",
                        "default_model": default_model
                    }))

            elif action == "get_key":
                target_user = data.get("target")
                if target_user in public_keys:
                    await websocket.send(json.dumps({
                        "type": "pub_key",
                        "username": target_user,
                        "key": public_keys[target_user]
                    }))
                else:
                    await websocket.send(json.dumps({
                        "status": "error", 
                        "message": f"User {target_user} not found or no key"
                    }))

            elif action == "private":
                if not username:
                    await websocket.send(json.dumps({"status": "error", "message": "Not logged in"}))
                    continue
                
                target_user = data.get("target")
                content = data.get("content")
                
                if target_user in connected_users:
                    try:
                        await connected_users[target_user].send(json.dumps({
                            "type": "private",
                            "from": username,
                            "content": content
                        }))
                    except websockets.exceptions.ConnectionClosed:
                        del connected_users[target_user]
                else:
                     await websocket.send(json.dumps({"status": "error", "message": f"User {target_user} not found"}))

            elif action == "join_group":
                if not username:
                    await websocket.send(json.dumps({"status": "error", "message": "Not logged in"}))
                    continue

                group_name = data.get("group")
                if group_name not in groups:
                    groups[group_name] = set()
                groups[group_name].add(username)
                database.add_to_group(username, group_name)
                print(f"{username} joined group {group_name}")
                await websocket.send(json.dumps({"status": "success", "message": f"Joined group {group_name}"}))

            elif action == "group":
                if not username:
                    await websocket.send(json.dumps({"status": "error", "message": "Not logged in"}))
                    continue

                group_name = data.get("group")
                content = data.get("content")

                if group_name in groups and username in groups[group_name]:
                    # Broadcast to others in the group
                    for member in groups[group_name]:
                        if member != username: # Don't echo back to sender
                            if member in connected_users:
                                try:
                                    await connected_users[member].send(json.dumps({
                                        "type": "group",
                                        "group": group_name,
                                        "from": username,
                                        "content": content
                                    }))
                                except websockets.exceptions.ConnectionClosed:
                                    pass # Handle lazy cleanup elsewhere or let it fail
                else:
                     await websocket.send(json.dumps({"status": "error", "message": f"You are not in group {group_name}"}))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if username:
            print(f"User disconnected: {username}")
            if username in connected_users:
                del connected_users[username]
            # Remove from all groups - DISABLED FOR PERSISTENCE
            # for group_name in groups:
            #     if username in groups[group_name]:
            #         groups[group_name].remove(username)

async def main():
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("Server started on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
