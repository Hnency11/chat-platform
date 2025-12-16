# Chat Platform Instructions

## 1. Prerequisites
Ensure your virtual environment is set up (I have already done this for you).

## 2. Run the Server
1. Open a terminal in the project folder.
2. Activate the environment:
   ```powershell
   .\.venv\Scripts\Activate
   ```
3. Start the server:
   ```powershell
   python server.py
   ```
   *You should see: `Server started on ws://localhost:8765`*

## 3. Run the Client
1. Open a **new** terminal window.
2. Activate the environment:
   ```powershell
   .\.venv\Scripts\Activate
   ```
3. Start the client:
   ```powershell
   python client.py
   ```
4. Enter a **username** when prompted.

## 4. Chat Commands
- **Private Message**: `/msg <username> <message>`
- **Join Group**: `/join <group_name>`
- **Group Message**: `/group <group_name> <message>`
- **Quit**: `/quit`

## 5. Web Client (Optional)
You can also use the web interface.

**Option A (Simple)**:
1. Go to `chat-platform/web` folder.
2. Double-click `index.html`.

**Option B (Professional)**:
1. Open a terminal.
2. Run: `python -m http.server 8000 --directory web`
3. Visit: `http://localhost:8000`

> **Note**: The web client connect to the same server (`ws://localhost:8765`), so web users and python terminal users can chat together (in Groups)!
