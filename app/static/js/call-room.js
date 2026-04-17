// ================= CONFIG =================
const ROOM = window.ROOM || document.getElementById('waitRoomCode').textContent;

const ICE_CONFIG = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' }
  ]
};

// ================= STATE =================
const socket = io();

let pc = null;
// BUG FIX 1: Do NOT cache window.localStream at module load time.
// call-model.js resolves getUserMedia asynchronously, so window.localStream
// is null when this script initialises. All reads must go through
// window.localStream directly so they see the value once it is set.
const pendingSignals = [];

let isPeerReady = false;
let isCreatingPC = false;

// ================= INIT ROOM =================
document.getElementById('waitRoomCode').textContent = ROOM;
document.getElementById('callRoomCode').textContent = ROOM;

socket.emit('join_room', { room: ROOM });

// ================= SOCKET EVENTS =================
socket.off('signal');
socket.off('role');
socket.off('peer_ready');
socket.off('peer_left');

socket.on('role', ({ role }) => {
  socket._role = role;
});

socket.on('peer_ready', async () => {
  isPeerReady = true;

  enterCallPhase();

  if (isCreatingPC) {
    await waitForPC();
  } else {
    await createPeerConnection();
  }

  if (socket._role === 'caller') {
    try {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      send({
        type: 'offer',
        sdp: pc.localDescription
      });
    } catch (err) {
      console.error('Offer creation failed:', err);
    }
  }
});

socket.on('signal', async (msg) => {
  if (!pc) {
    pendingSignals.push(msg);
    return;
  }

  await handleSignal(msg);
});

socket.on('peer_left', () => {
  setCallStatus('Peer left', false);
  document.getElementById('remoteVideo').srcObject = null;
});

// ================= WEBRTC =================

// BUG FIX 3: Added a timeout so waitForPC() cannot hang indefinitely if
// createPeerConnection() fails silently (e.g. an unhandled exception leaves
// isCreatingPC=true but pc still null).
function waitForPC(timeout = 5000) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeout;
    const interval = setInterval(() => {
      if (pc) {
        clearInterval(interval);
        resolve();
      } else if (Date.now() >= deadline) {
        clearInterval(interval);
        reject(new Error('Timed out waiting for PeerConnection to be created'));
      }
    }, 20);
  });
}

async function createPeerConnection() {
  if (pc || isCreatingPC) return;
  isCreatingPC = true;

  try {
    pc = new RTCPeerConnection(ICE_CONFIG);

    // BUG FIX 1 (continued): read window.localStream here, not a stale local copy.
    const stream = await window.localStreamReady;
    if (stream) {
      stream.getTracks().forEach(track => pc.addTrack(track, stream));
    } else {
      console.warn('localStream not available yet');
    }

    pc.ontrack = (event) => {
      const remoteStream = event.streams && event.streams[0];
      if (remoteStream) {
        document.getElementById('remoteVideo').srcObject = remoteStream;
      }
    };

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        socket.emit('signal', {
          room: ROOM,
          type: 'ice-candidate',
          candidate: event.candidate
        });
      }
    };

    pc.onconnectionstatechange = () => {
      const state = pc.connectionState;

      if (state === 'connected') {
        setCallStatus('Connected', true);
      } else if (state === 'failed' || state === 'disconnected') {
        setCallStatus('Disconnected', false);
      }
    };

    while (pendingSignals.length) {
      await handleSignal(pendingSignals.shift());
    }

  } catch (err) {
    console.error('PeerConnection creation failed:', err);
  } finally {
    isCreatingPC = false;
  }
}

// ================= SIGNAL HANDLING =================
async function handleSignal({ type, sdp, candidate }) {
  if (!pc) return;

  try {
    switch (type) {
      case 'offer': {
        await pc.setRemoteDescription(new RTCSessionDescription(sdp));

        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        send({
          type: 'answer',
          sdp: pc.localDescription
        });

        break;
      }

      case 'answer': {
        await pc.setRemoteDescription(new RTCSessionDescription(sdp));
        break;
      }

      case 'ice-candidate': {
        if (candidate) {
          try {
            await pc.addIceCandidate(new RTCIceCandidate(candidate));
          } catch (err) {
            console.warn('Invalid ICE candidate:', err);
          }
        }
        break;
      }

      default:
        console.warn('Unknown signal type:', type);
    }
  } catch (err) {
    console.error('Signal handling error:', err);
  }
}

// ================= HELPERS =================
async function send(data) {
  socket.emit('signal', { room: ROOM, ...data });
}

async function enterCallPhase() {
  document.getElementById('waiting-room').style.display = 'none';
  document.getElementById('calling-room').style.display = '';

  const stream = await window.localStreamReady;
  document.getElementById('localVideo').srcObject = stream;
}

function setCallStatus(text, ok) {
  const el = document.getElementById('callStatus');
  const dot = el.querySelector('.status-dot');
  const textEl = document.getElementById('callStatusText');

  el.className = `status-badge status-badge--${ok ? 'connected' : 'waiting'}`;
  dot.style.background = ok ? '#27ae60' : '#e74c3c';
  textEl.textContent = text;
}

// ================= CLEANUP =================
async function cleanup() {
  if (pc) {
    pc.ontrack = null;
    pc.onicecandidate = null;
    pc.onconnectionstatechange = null;

    pc.close();
    pc = null;
  }

  pendingSignals.length = 0;

  // BUG FIX 2: null out window.localStream (not just a stale local variable)
  // so that enterCallPhase / addTrack checks don't treat the dead stream as valid.
  const stream = await window.localStreamReady;
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    window.localStream = null;
  }
}

function leaveCall() {
  cleanup();
  socket.disconnect();
  window.location.href = '/';
}

function cancelAndLeave() {
  cleanup();
  socket.disconnect();
  window.history.back();
}
