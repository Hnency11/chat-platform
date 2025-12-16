let socket;
let username = null;
let currentTarget = { type: null, name: null };
let myPublicKey = "WEB_CLIENT_NO_ENCRYPTION"; // Placeholder

const messagesArea = document.getElementById('messages-area');
const messageInput = document.getElementById('message-input');
const chatTargetLabel = document.getElementById('chat-target');
const groupsList = document.getElementById('groups-list');

function login() {
    const input = document.getElementById('username-input');
    const user = input.value.trim();
    if (!user) return alert("Please enter a username");

    username = user;
    connectWebSocket();
}

function connectWebSocket() {
    socket = new WebSocket("ws://localhost:8765");

    socket.onopen = () => {
        console.log("Connected to server");
        // Send Login
        socket.send(JSON.stringify({
            action: "login",
            username: username,
            public_key: null // Web client is plain text for now
        }));

        document.getElementById('login-modal').classList.add('hidden');
        document.getElementById('current-user').innerText = `Logged in as: ${username}`;
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    socket.onclose = () => {
        alert("Disconnected from server");
        location.reload();
    };
}

function handleMessage(data) {
    if (data.status === "success") {
        addSystemMessage(data.message);
    } else if (data.status === "error") {
        addSystemMessage(`Error: ${data.message}`);
    } else if (data.type === "group") {
        // Group Message
        if (currentTarget.type === 'group' && currentTarget.name === data.group) {
            addMessageBubble(data.from, data.content, false);
        } else {
            // Notification (simple log for now)
            console.log(`New message in ${data.group} from ${data.from}`);
        }
    } else if (data.type === "private") {
        // Private Message (Encrypted - we might see garbage if not handled)
        // Since we didn't send a public key, server might not send encrypted?
        // Actually server logic sends if target matches.
        // We will just display raw content for now.
        addMessageBubble(data.from, "[Encrypted Message] (Web client cannot decrypt yet)", false);
    }
}

function joinGroupPrompt() {
    const groupName = prompt("Enter Group Name to Join:");
    if (groupName) {
        socket.send(JSON.stringify({
            action: "join_group",
            group: groupName
        }));
        // Add to sidebar
        addGroupToSidebar(groupName);
        switchToGroup(groupName);
    }
}

function addGroupToSidebar(groupName) {
    // Check if exists
    const existing = document.getElementById(`group-btn-${groupName}`);
    if (existing) return;

    const btn = document.createElement('button');
    btn.id = `group-btn-${groupName}`;
    btn.className = "w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 rounded-md transition-colors flex items-center gap-2";
    btn.innerHTML = `<span class="text-blue-400">#</span> ${groupName}`;
    btn.onclick = () => switchToGroup(groupName);

    // Insert before the "+ Join" button
    groupsList.insertBefore(btn, groupsList.lastElementChild);
}

function switchToGroup(groupName) {
    currentTarget = { type: 'group', name: groupName };
    chatTargetLabel.innerText = `# ${groupName}`;
    messagesArea.innerHTML = ''; // Clear view
    addSystemMessage(`Switched to channel #${groupName}`);
}

function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    if (!currentTarget.name) {
        return alert("Please select a group or user first!");
    }

    if (currentTarget.type === 'group') {
        socket.send(JSON.stringify({
            action: "group",
            group: currentTarget.name,
            content: text
        }));
        // Echo locally not needed as server will broadcast? 
        // Wait, server logic: line 91 server.py says "if member != username".
        // So we must echo locally.
        addMessageBubble("Me", text, true);
    }

    messageInput.value = "";
}

function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

function addMessageBubble(sender, content, isOwn) {
    const div = document.createElement('div');
    div.className = `max-w-[70%] px-4 py-2 mb-2 flex flex-col message-enter ${isOwn ? 'message-own' : 'message-other'}`;

    const meta = document.createElement('span');
    meta.className = "text-xs opacity-75 mb-1";
    meta.innerText = isOwn ? "You" : sender;

    const body = document.createElement('span');
    body.innerText = content;

    div.appendChild(meta);
    div.appendChild(body);

    // Wrapper for alignment
    const wrapper = document.createElement('div');
    wrapper.className = "flex w-full flex-col";
    wrapper.appendChild(div);

    messagesArea.appendChild(wrapper);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function addSystemMessage(text) {
    const div = document.createElement('div');
    div.className = "flex justify-center mb-4";
    div.innerHTML = `<span class="text-xs text-gray-500 bg-gray-800/50 px-3 py-1 rounded-full border border-gray-700">${text}</span>`;
    messagesArea.appendChild(div);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}
