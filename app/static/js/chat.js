/* app/static/js/chat.js */

// Chat module — shares its Socket.IO connection with call.js.
// Must be initialized by call.js: initChat(App.socket, () => App.room).

let chatSocket = null;
let roomGetter = null;
let wired      = false;

export function initChat(socket, roomCodeGetter) {
    if (wired) return;   // idempotent — don't attach listeners twice
    chatSocket = socket;
    roomGetter = roomCodeGetter;

    // Incoming messages. Backend tags 'system' on join/leave notifications
    // and 'peer' on regular messages (via include_self=False).
    chatSocket.on('chat_message', (data) => {
        if (!data || !data.message) return;
        const sender = data.sender === 'system' ? 'system' : 'peer';
        appendMessage(sender, data.message);
    });

    const input = document.getElementById('chatInput');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    // The HTML has no onclick on the Send button — wire it here.
    const sendBtn = document.getElementById('sendChatBtn');
    if (sendBtn) sendBtn.addEventListener('click', sendChatMessage);

    wired = true;
}

export function sendChatMessage() {
    if (!chatSocket || !roomGetter) return;

    const input = document.getElementById('chatInput');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    chatSocket.emit('chat_message', {
        room: roomGetter(),
        message: message
    });

    appendMessage('me', message);
    input.value = '';
}

function appendMessage(sender, message) {
    const chatBox = document.getElementById('chatBox');
    if (!chatBox) return;

    const msg = document.createElement('div');
    msg.style.margin       = '6px 0';
    msg.style.padding      = '6px 10px';
    msg.style.borderRadius = '6px';
    msg.style.maxWidth     = '80%';
    msg.style.wordWrap     = 'break-word';

    if (sender === 'me') {
        msg.style.background = '#2d6cdf';
        msg.style.color      = '#fff';
        msg.style.marginLeft = 'auto';
    } else if (sender === 'system') {
        msg.style.background = 'transparent';
        msg.style.color      = '#888';
        msg.style.fontStyle  = 'italic';
        msg.style.fontSize   = '0.8rem';
        msg.style.textAlign  = 'center';
        msg.style.maxWidth   = '100%';
    } else {
        // peer
        msg.style.background = '#222';
        msg.style.color      = '#ddd';
    }

    msg.textContent = message;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}
