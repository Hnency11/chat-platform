# 🔐 Secure Real-Time Chat Platform

A full-stack, real-time messaging application built with **Python**, **WebSockets**, and **PostgreSQL**. Features end-to-end encryption for private messages, persistent group chats, and a modern dark-themed web interface.

![Project Status](https://img.shields.io/badge/status-active-success)
![Python Version](https://img.shields.io/badge/python-3.11+-blue)


## ✨ Key Features

- **Real-Time Communication**: Instant messaging using asynchronous WebSockets (`websockets` library).
- **End-to-End Encryption**: Private messages are encrypted using **RSA** (key exchange) and **Fernet/AES** (message encryption) via the `cryptography` library.
- **Persistent Data**: Users and group memberships are stored in a **PostgreSQL** database.
- **Microservices Architecture**: Decoupled backend (Python WS Server) and frontend (Static HTML/JS).
- **Group chats**: Create and join multiple channels.
- **Cross-Platform Clients**:
  - **CLI Client**: Full-featured Python terminal client with encryption support.
  - **Web Client**: Modern, responsive dark-mode interface (HTML5/TailwindCSS).

## 🛠 Tech Stack

- **Backend**: Python 3.11+, `asyncio`, `websockets`
- **Database**: PostgreSQL, `psycopg2`
- **Security**: `cryptography` (RSA + Fernet)
- **Frontend**: HTML5, CSS3, TailwindCSS, JS

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL installed and running

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/chat-platform.git
cd chat-platform
```

### 2. Set up Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgres://YOUR_USER:YOUR_PASSWORD@localhost:5432/chatdb
```
*Note: The server will automatically create the required tables on first run.*

## 💻 Usage

### Starting the Server
The backend server handles all WebSocket connections and database interactions.
```powershell
python server.py
# Server started on ws://localhost:8765
```

### Method A: Using the CLI Client (Recommended for Encryption)
The terminal client supports full RSA encryption.
```powershell
python client.py
```
**Commands:**
- `/msg <user> <message>` : Send private encrypted message.
- `/join <group>` : Join a group channel.
- `/group <group> <message>` : Send message to group.
- `/quit` : Exit.

### Method B: Using the Web Interface
A modern web UI for ease of use.

**Run the static file server:**
```powershell
python -m http.server 8000 --directory web
```
Then open your browser to: **[http://localhost:8000](http://localhost:8000)**


