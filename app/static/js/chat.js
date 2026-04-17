/* app/static/js/chat.js*/

// ================= CHAT MODULE =================

let chatSocket = null;

export function initChat(socket, roomCodeGetter) {
  chatSocket = socket;

  // receive messages
  chatSocket.on("chat_message", (data) => {
    appendMessage("peer", data.message);
  });

  // enter key support
  const input = document.getElementById("chatInput");
  if (input) {
    input.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        sendChatMessage(roomCodeGetter);
      }
    });
  }
}

export function sendChatMessage(roomCodeGetter) {
  const input = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message || !chatSocket) return;

  chatSocket.emit("chat_message", {
    room: roomCodeGetter(),
    message: message
  });

  appendMessage("me", message);
  input.value = "";
}

function appendMessage(sender, message) {
  const chatBox = document.getElementById("chatBox");
  if (!chatBox) return;

  const msg = document.createElement("div");

  msg.classList.add("chat-message");

  if (sender === "me") {
    msg.classList.add("chat-me");
  } else {
    msg.classList.add("chat-peer");
  }

  msg.textContent = message;

  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}