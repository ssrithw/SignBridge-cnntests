/* app/static/js/call.js */

import { initChat } from '/static/js/chat.js';

// ================= CONFIG =================
const MODEL_URL   = '/static/models/mobilenet-slsl-1/model.json';
const CLASSES_URL = '/static/models/mobilenet-slsl-1/class_names.json';

const INPUT_SIZE           = 128;
const CONFIDENCE_THRESHOLD = 0.55;
const TOTAL_SECONDS        = 5;
// Capture near the END of the countdown so the user has time to pose.
const CAPTURE_AT_SECOND    = 2;

const ICE_CONFIG = {
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

// ================= APP STATE =================
const App = {
    room: window.ROOM ||
          (document.getElementById('waitRoomCode') &&
           document.getElementById('waitRoomCode').textContent.trim()) || '',

    stream: null,
    streamReady: null,

    model: null,
    classNames: [],

    socket: null,
    pc: null,

    pendingSignals: [],
    role: null,

    // recognition state
    countdownTimer: null,
    secondsRemaining: TOTAL_SECONDS,
    isRecognizing: false,

    // call state
    callStarted: false
};

// ================= BOOT =================
async function bootApp() {
    try {
        initUI();
        await initMedia();
        await initModel();
        initSocket();
        wireUnloadCleanup();
    } catch (err) {
        console.error('Boot failed:', err);
        setRecogStatus('⚠ Startup failed: ' + (err.message || err));
    }
}

// ================= MEDIA =================
async function initMedia() {
    try {
        App.streamReady = navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 } },
            audio: true
        });
        App.stream = await App.streamReady;

        const preview = document.getElementById('waitPreview');
        if (preview) {
            preview.srcObject  = App.stream;
            preview.muted      = true;
            preview.playsInline = true;
        }

        const waitStatus = document.getElementById('waitPreviewStatus');
        if (waitStatus) waitStatus.textContent = '';
    } catch (err) {
        const waitStatus = document.getElementById('waitPreviewStatus');
        if (waitStatus) waitStatus.textContent = 'Camera/mic access denied.';
        setRecogStatus('⚠ Camera/mic access denied');
        throw err;
    }
}

// ================= MODEL =================
async function initModel() {
    setRecogStatus('Loading model…');

    const res = await fetch(CLASSES_URL);
    if (!res.ok) throw new Error('Failed to load class_names.json');
    const raw = await res.json();
    App.classNames = raw.class_names;
    App.classIndex  = raw.class_index;

    App.model = await tf.loadGraphModel(MODEL_URL);

    // Warm up so the first real inference isn't slow.
    tf.tidy(() => {
        const dummy = tf.zeros([1, INPUT_SIZE, INPUT_SIZE, 3]);
        const out = App.model.predict(dummy);
        if (Array.isArray(out)) out.forEach(t => t.dispose());
        else out.dispose();
    });

    setRecogStatus('Model ready — press ▶ to start');
    const btn = document.getElementById('btnStartRecog');
    if (btn) btn.disabled = false;
}

// ================= SOCKET =================
function initSocket() {
    App.socket = io();

    App.socket.emit('join_room', { room: App.room });

    App.socket.on('role', ({ role }) => {
        App.role = role;
    });

    App.socket.on('peer_ready', async () => {
        if (App.callStarted) return;       // idempotent against repeat emits
        App.callStarted = true;
        await startCall();
    });

    App.socket.on('signal', async (msg) => {
        if (!App.pc) {
            App.pendingSignals.push(msg);
            return;
        }
        await handleSignal(msg);
    });

    App.socket.on('peer_left', () => {
        setCallStatus('Peer left', false);
        const remote = document.getElementById('remoteVideo');
        if (remote) remote.srcObject = null;

        // Tear down so a fresh peer_ready can build a clean connection.
        if (App.pc) {
            try { App.pc.close(); } catch (_) {}
            App.pc = null;
        }
        App.pendingSignals = [];
        App.callStarted    = false;
    });

    App.socket.on('error', (data) => {
        const msg = (data && data.message) || 'Signaling error';
        setRecogStatus('⚠ ' + msg);
    });

    // Hook the chat module onto the SAME socket — no second io() connection.
    initChat(App.socket, () => App.room);
}

// ================= CALL START =================
async function startCall() {
    enterCallPhase();
    await App.streamReady;

    if (!App.pc) {
        App.pc = new RTCPeerConnection(ICE_CONFIG);

        App.stream.getTracks().forEach(track => {
            App.pc.addTrack(track, App.stream);
        });

        App.pc.ontrack = (event) => {
            const remote = document.getElementById('remoteVideo');
            if (remote) {
                remote.srcObject   = event.streams[0];
                remote.playsInline = true;
            }
        };

        App.pc.onicecandidate = (event) => {
            if (event.candidate) {
                App.socket.emit('signal', {
                    room: App.room,
                    type: 'ice-candidate',
                    candidate: event.candidate
                });
            }
        };

        App.pc.onconnectionstatechange = () => {
            const state = App.pc ? App.pc.connectionState : 'closed';
            if (state === 'connected') {
                setCallStatus('Connected', true);
            } else if (
                state === 'failed' ||
                state === 'disconnected' ||
                state === 'closed'
            ) {
                setCallStatus('Disconnected', false);
            }
        };
    }

    // Flush any signals that arrived before App.pc existed.
    while (App.pendingSignals.length) {
        await handleSignal(App.pendingSignals.shift());
    }

    if (App.role === 'caller') {
        try {
            if (App.pc.signalingState !== 'stable') return; // glare guard
            const offer = await App.pc.createOffer();
            await App.pc.setLocalDescription(offer);

            App.socket.emit('signal', {
                room: App.room,
                type: 'offer',
                sdp: App.pc.localDescription
            });
        } catch (err) {
            console.error('createOffer failed:', err);
        }
    }
}

// ================= SIGNALING =================
async function handleSignal({ type, sdp, candidate }) {
    if (!App.pc) return;
    try {
        switch (type) {
            case 'offer': {
                await App.pc.setRemoteDescription(new RTCSessionDescription(sdp));
                const answer = await App.pc.createAnswer();
                await App.pc.setLocalDescription(answer);
                App.socket.emit('signal', {
                    room: App.room,
                    type: 'answer',
                    sdp: App.pc.localDescription
                });
                break;
            }
            case 'answer': {
                if (App.pc.signalingState === 'have-local-offer') {
                    await App.pc.setRemoteDescription(new RTCSessionDescription(sdp));
                }
                break;
            }
            case 'ice-candidate': {
                if (candidate) {
                    try {
                        await App.pc.addIceCandidate(new RTCIceCandidate(candidate));
                    } catch (e) {
                        // Usually benign — ICE arrived before remote SDP was set.
                        console.warn('addIceCandidate:', e.message);
                    }
                }
                break;
            }
        }
    } catch (err) {
        console.error('Signal error:', err);
    }
}

// ================= UI =================
function initUI() {
    const waitCode = document.getElementById('waitRoomCode');
    const callCode = document.getElementById('callRoomCode');
    if (waitCode) waitCode.textContent = App.room;
    if (callCode) callCode.textContent = App.room;

    const startBtn = document.getElementById('btnStartRecog');
    if (startBtn) startBtn.disabled = true;   // enabled after model loads

    const stopBtn = document.getElementById('btnStopRecog');
    if (stopBtn) stopBtn.disabled = true;
}

function enterCallPhase() {
    const wait = document.getElementById('waiting-room');
    const call = document.getElementById('calling-room');
    if (wait) wait.style.display = 'none';
    if (call) call.style.display = '';

    const local = document.getElementById('localVideo');
    if (local && App.stream) {
        local.srcObject   = App.stream;
        local.muted       = true;
        local.playsInline = true;
    }
}

function setCallStatus(text, ok) {
    const el = document.getElementById('callStatus');
    if (!el) return;

    el.className = `status-badge status-badge--${ok ? 'connected' : 'waiting'}`;

    const dot = el.querySelector('.status-dot');
    if (dot) dot.style.background = ok ? '#27ae60' : '#e74c3c';

    const textEl = document.getElementById('callStatusText');
    if (textEl) textEl.textContent = text;
}

// ================= RECOGNITION =================
function startRecognition() {
    if (App.isRecognizing) return;
    if (!App.model) return setRecogStatus('Model not ready');

    const video = document.getElementById('localVideo');
    if (!video || video.readyState < 2 || !video.videoWidth) {
        return setRecogStatus('Video not ready');
    }

    App.isRecognizing = true;

    const startBtn = document.getElementById('btnStartRecog');
    const stopBtn  = document.getElementById('btnStopRecog');
    if (startBtn) startBtn.disabled = true;
    if (stopBtn)  stopBtn.disabled  = false;

    App.secondsRemaining = TOTAL_SECONDS;
    const timerEl = document.getElementById('timerDisplay');
    if (timerEl) {
        timerEl.style.display = 'block';
        timerEl.textContent   = App.secondsRemaining;   // show starting value immediately
    }

    if (App.countdownTimer) {
        clearInterval(App.countdownTimer);
        App.countdownTimer = null;
    }

    App.countdownTimer = setInterval(() => {
        if (App.secondsRemaining === CAPTURE_AT_SECOND) {
            captureAndInfer();
        }

        if (timerEl) timerEl.textContent = App.secondsRemaining;
        App.secondsRemaining--;

        if (App.secondsRemaining < 0) {
            finishRecognition('Done — press ▶ again');
        }
    }, 1000);
}

function stopRecognition() {
    if (!App.isRecognizing) return;
    finishRecognition('Stopped');
}

function finishRecognition(statusMsg) {
    if (App.countdownTimer) {
        clearInterval(App.countdownTimer);
        App.countdownTimer = null;
    }
    App.isRecognizing = false;

    const timerEl = document.getElementById('timerDisplay');
    if (timerEl) timerEl.style.display = 'none';

    const startBtn = document.getElementById('btnStartRecog');
    const stopBtn  = document.getElementById('btnStopRecog');
    if (startBtn) startBtn.disabled = !App.model;
    if (stopBtn)  stopBtn.disabled  = true;

    setRecogStatus(statusMsg);
}

async function captureAndInfer() {
    const video  = document.getElementById('localVideo');
    const canvas = document.getElementById('captureCanvas');
    if (!video || !canvas || !video.videoWidth) {
        setRecogStatus('Video not ready for capture');
        return;
    }

    canvas.width  = INPUT_SIZE;
    canvas.height = INPUT_SIZE;

    const ctx = canvas.getContext('2d');
    // Draw the non-mirrored frame so orientation matches training data.
    ctx.drawImage(video, 0, 0, INPUT_SIZE, INPUT_SIZE);

    const tensor = tf.tidy(() => {
        return tf.browser.fromPixels(canvas)
            .toFloat()
            .div(255.0)
            .expandDims(0);
    });

    let predTensor   = null;
    let extraTensors = [];
    try {
        // predict() is safer than execute() for standard input-output graphs.
        const out = App.model.predict(tensor);
        if (Array.isArray(out)) {
            predTensor   = out[0];
            extraTensors = out.slice(1);
        } else {
            predTensor = out;
        }

        const predictions = await predTensor.data();

        let maxIdx = 0;
        for (let i = 1; i < predictions.length; i++) {
            if (predictions[i] > predictions[maxIdx]) maxIdx = i;
        }

        const confidence = predictions[maxIdx];
        const letter     = App.classNames[maxIdx] ?? String(maxIdx);

        if (confidence < CONFIDENCE_THRESHOLD) {
            setRecogStatus(
                `No confident prediction (best: ${letter} @ ${(confidence * 100).toFixed(1)}%)`
            );
            return;
        }

        const letterEl = document.getElementById('detectedLetter');
        if (letterEl) letterEl.textContent = letter;

        appendToTranscript(letter);
        setRecogStatus(`Detected: ${letter} (${(confidence * 100).toFixed(1)}%)`);
    } catch (err) {
        console.error('Inference error:', err);
        setRecogStatus('⚠ Inference error: ' + err.message);
    } finally {
        tensor.dispose();
        if (predTensor) { try { predTensor.dispose(); } catch (_) {} }
        extraTensors.forEach(t => { try { t.dispose(); } catch (_) {} });
    }
}

// ================= TRANSCRIPT =================
function appendToTranscript(letter) {
    const box = document.getElementById('transcriptBox');
    if (!box) return;

    // Placeholder is the only span with italic styling — target it specifically
    // so real letter spans are never wiped.
    const placeholder = box.querySelector('span[style*="italic"]');
    if (placeholder) placeholder.remove();

    const span = document.createElement('span');
    span.textContent   = letter;
    span.className     = 'transcript-letter';
    span.style.cssText = 'font-size:1.4rem;font-weight:700;margin:2px;';
    box.appendChild(span);

    box.scrollTop = box.scrollHeight;
}

function clearTranscript() {
    const box = document.getElementById('transcriptBox');
    if (box) {
        box.innerHTML =
            '<span style="color:#aaa;font-style:italic;">Recognized letters will appear here…</span>';
    }
    const letterEl = document.getElementById('detectedLetter');
    if (letterEl) letterEl.textContent = '—';
}

function setRecogStatus(msg) {
    const el = document.getElementById('recognitionStatus');
    if (el) el.textContent = msg;
}

// ================= LEAVE / CANCEL / CLEANUP =================
function leaveCall() {
    cleanup();
    // Let the rest of the app's navigation take over — send the user home.
    window.location.href = '/';
}

function cancelAndLeave() {
    cleanup();
    window.location.href = '/';
}

function cleanup() {
    if (App.countdownTimer) {
        clearInterval(App.countdownTimer);
        App.countdownTimer = null;
    }
    App.isRecognizing = false;

    if (App.pc) {
        try { App.pc.close(); } catch (_) {}
        App.pc = null;
    }

    if (App.stream) {
        App.stream.getTracks().forEach(t => {
            try { t.stop(); } catch (_) {}
        });
        App.stream = null;
    }

    if (App.socket) {
        try { App.socket.disconnect(); } catch (_) {}
    }

    App.pendingSignals = [];
    App.callStarted    = false;
}

function wireUnloadCleanup() {
    window.addEventListener('beforeunload', cleanup);
    window.addEventListener('pagehide',     cleanup);
}

// ================= EXPOSE TO window =================
// call.html uses inline onclick="…" handlers. Because this file is loaded as
// an ES module, top-level declarations are NOT on window, so the handlers
// referenced from HTML must be published explicitly.
window.startRecognition = startRecognition;
window.stopRecognition  = stopRecognition;
window.clearTranscript  = clearTranscript;
window.leaveCall        = leaveCall;
window.cancelAndLeave   = cancelAndLeave;

// ================= START APP =================
// Modules are deferred, so DOM is already parsed — but guard anyway.
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootApp);
} else {
    bootApp();
}
