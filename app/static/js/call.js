/* app/static/js/call.js*/

import { initChat, sendChatMessage } from "./chat.js";

// ================= CONFIG =================
const MODEL_URL = '/static/models/mobilenet-slsl-1/model.json';
const CLASSES_URL = '/static/models/mobilenet-slsl-1/class_names.json';

const INPUT_SIZE = 128;
const CONFIDENCE_THRESHOLD = 0.55;
const TOTAL_SECONDS = 5;
const CAPTURE_AT_SECOND = 4; // seconds remaining on the countdown when we capture

const ICE_CONFIG = {
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

// ================= APP STATE =================
const App = {
    room: window.ROOM
        || (document.getElementById('waitRoomCode')?.textContent || '').trim(),

    stream: null,
    streamReady: null,

    model: null,
    classNames: [],

    socket: null,
    pc: null,

    pendingSignals: [],
    remoteDescSet: false,
    makingOffer: false,
    role: null,
    callActive: false
};

// ================= BOOT =================
async function bootApp() {
    try {
        if (!App.room) {
            console.error('No room code available; aborting boot.');
            setRecogStatus('Missing room code');
            return;
        }
        await initMedia();
        await initModel();
        initSocket();
        initUI();
        window.addEventListener('beforeunload', cleanup);
        window.addEventListener('pagehide', cleanup);
    } catch (err) {
        console.error('Boot failed:', err);
        setRecogStatus('Startup error: ' + (err?.message || err));
    }
}

// ================= MEDIA =================
async function initMedia() {
    try {
        App.streamReady = navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });

        App.stream = await App.streamReady;

        const preview = document.getElementById('waitPreview');
        if (preview) preview.srcObject = App.stream;
    } catch (err) {
        console.error('getUserMedia failed:', err);
        setRecogStatus('Camera/mic permission denied');
        throw err;
    }
}

// ================= MODEL =================
async function initModel() {
    setRecogStatus('Loading model…');

    const res = await fetch(CLASSES_URL);
    if (!res.ok) throw new Error('class_names.json HTTP ' + res.status);

    const raw = await res.json();
    App.classNames = Array.isArray(raw) ? raw : Object.values(raw);

    App.model = await tf.loadGraphModel(MODEL_URL);

    // Warmup pass so the first real capture is fast.
    try {
        const warm = tf.zeros([1, INPUT_SIZE, INPUT_SIZE, 3]);
        const out = App.model.predict(warm);
        // predict() may return a tensor or an array of tensors.
        const tensors = Array.isArray(out) ? out : [out];
        await Promise.all(tensors.map(t => t.data()));
        tensors.forEach(t => t.dispose());
        warm.dispose();
    } catch (e) {
        console.warn('Model warmup skipped:', e);
    }

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
        // Guard: only start a call flow once per peer session.
        if (App.callActive) return;
        App.callActive = true;
        await startCall();
    });

    App.socket.on('signal', async (msg) => {
        // If PC doesn't exist yet, queue everything.
        if (!App.pc) {
            App.pendingSignals.push(msg);
            return;
        }
        // PC exists but remote description may not yet be set — queue ICE.
        if (msg.type === 'ice-candidate' && !App.remoteDescSet) {
            App.pendingSignals.push(msg);
            return;
        }
        await handleSignal(msg);
    });

    App.socket.on('peer_left', () => {
        setCallStatus('Peer left', false);
        const remote = document.getElementById('remoteVideo');
        if (remote) remote.srcObject = null;
        tearDownPeer();
    });
}

// ================= CALL START =================
async function startCall() {
    enterCallPhase();

    await App.streamReady;

    if (!App.pc) {
        App.pc = new RTCPeerConnection(ICE_CONFIG);
        App.remoteDescSet = false;

        App.stream.getTracks().forEach(track => {
            App.pc.addTrack(track, App.stream);
        });

        App.pc.ontrack = (event) => {
            const remote = document.getElementById('remoteVideo');
            if (remote) remote.srcObject = event.streams[0];
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
            const state = App.pc?.connectionState;
            if (state === 'connected') {
                setCallStatus('Connected', true);
            } else if (state === 'failed' || state === 'disconnected') {
                setCallStatus('Disconnected', false);
            } else if (state === 'closed') {
                setCallStatus('Closed', false);
            }
        };
    }

    // Drain any signals that arrived before pc was ready.
    await drainPendingSignals();

    // Only the caller sends the initial offer, and only once.
    if (App.role === 'caller' && !App.makingOffer && !App.pc.currentLocalDescription) {
        try {
            App.makingOffer = true;
            const offer = await App.pc.createOffer();
            await App.pc.setLocalDescription(offer);

            App.socket.emit('signal', {
                room: App.room,
                type: 'offer',
                sdp: App.pc.localDescription
            });
        } catch (err) {
            console.error('Offer creation failed:', err);
        } finally {
            App.makingOffer = false;
        }
    }
}

async function drainPendingSignals() {
    // Process non-ICE first so remote description gets set before we add candidates.
    const nonIce = App.pendingSignals.filter(m => m.type !== 'ice-candidate');
    const ice = App.pendingSignals.filter(m => m.type === 'ice-candidate');
    App.pendingSignals = [];

    for (const m of nonIce) await handleSignal(m);
    for (const m of ice) await handleSignal(m);
}

// ================= SIGNALING =================
async function handleSignal({ type, sdp, candidate }) {
    if (!App.pc) return;

    try {
        switch (type) {
            case 'offer': {
                await App.pc.setRemoteDescription(new RTCSessionDescription(sdp));
                App.remoteDescSet = true;

                const answer = await App.pc.createAnswer();
                await App.pc.setLocalDescription(answer);

                App.socket.emit('signal', {
                    room: App.room,
                    type: 'answer',
                    sdp: App.pc.localDescription
                });

                // Flush any ICE candidates that arrived before the offer.
                await drainPendingSignals();
                break;
            }

            case 'answer': {
                await App.pc.setRemoteDescription(new RTCSessionDescription(sdp));
                App.remoteDescSet = true;
                await drainPendingSignals();
                break;
            }

            case 'ice-candidate': {
                if (!candidate) break;
                if (!App.remoteDescSet) {
                    // Shouldn't normally reach here, but be defensive.
                    App.pendingSignals.push({ type, candidate });
                    break;
                }
                try {
                    await App.pc.addIceCandidate(new RTCIceCandidate(candidate));
                } catch (e) {
                    // Benign races after close/teardown — log and continue.
                    console.warn('addIceCandidate failed:', e);
                }
                break;
            }
        }
    } catch (err) {
        console.error('Signal error:', err);
    }
}

function tearDownPeer() {
    if (App.pc) {
        try { App.pc.ontrack = null; App.pc.onicecandidate = null; } catch (_) { }
        try { App.pc.close(); } catch (_) { }
        App.pc = null;
    }
    App.remoteDescSet = false;
    App.pendingSignals = [];
    App.callActive = false;
    App.makingOffer = false;
}

// ================= UI =================
function initUI() {
    const wait = document.getElementById('waitRoomCode');
    const call = document.getElementById('callRoomCode');
    if (wait) wait.textContent = App.room;
    if (call) call.textContent = App.room;

    const startBtn = document.getElementById('btnStartRecog');
    if (startBtn) startBtn.addEventListener('click', startRecognition);

    const clearBtn = document.getElementById('btnClearTranscript');
    if (clearBtn) clearBtn.addEventListener('click', clearTranscript);
}

function enterCallPhase() {
    const waitRoom = document.getElementById('waiting-room');
    const callRoom = document.getElementById('calling-room');
    if (waitRoom) waitRoom.style.display = 'none';
    if (callRoom) callRoom.style.display = '';

    if (App.stream) {
        const localVideo = document.getElementById('localVideo');
        if (localVideo) localVideo.srcObject = App.stream;
    }

    // ✅ INIT CHAT HERE
    initChat(App.socket, () => App.room);

    // ✅ BIND SEND BUTTON HERE
    const btn = document.getElementById("sendChatBtn");
    if (btn) {
        btn.addEventListener("click", () => {
            sendChatMessage(() => App.room);
        });
    }
}

function setCallStatus(text, ok) {
    const el = document.getElementById('callStatus');
    if (!el) return;
    const dot = el.querySelector('.status-dot');
    const textEl = document.getElementById('callStatusText');

    el.className = `status-badge status-badge--${ok ? 'connected' : 'waiting'}`;
    if (dot) dot.style.background = ok ? '#27ae60' : '#e74c3c';
    if (textEl) textEl.textContent = text;
}

// ================= RECOGNITION =================
let countdownTimer = null;
let secondsRemaining = TOTAL_SECONDS;
let inferenceInFlight = false;

function startRecognition() {
    if (!App.model) return setRecogStatus('Model not ready');
    if (countdownTimer) return; // already running

    // Prefer the in-call video; fall back to the waiting-room preview so the
    // feature is usable before a peer has joined.
    const video = getActiveVideoEl();
    if (!video || video.readyState < 2) return setRecogStatus('Video not ready');

    const btn = document.getElementById('btnStartRecog');
    if (btn) btn.disabled = true;

    secondsRemaining = TOTAL_SECONDS;
    const timerEl = document.getElementById('timerDisplay');
    if (timerEl) {
        timerEl.style.display = 'block';
        timerEl.textContent = secondsRemaining;
    }

    countdownTimer = setInterval(() => {
        // Capture when the displayed number equals CAPTURE_AT_SECOND.
        if (secondsRemaining === CAPTURE_AT_SECOND) {
            captureAndInfer().catch(e => console.error(e));
        }

        secondsRemaining -= 1;

        if (secondsRemaining < 0) {
            clearInterval(countdownTimer);
            countdownTimer = null;
            if (timerEl) timerEl.style.display = 'none';
            if (btn) btn.disabled = false;
            setRecogStatus('Done — press ▶ again');
            return;
        }

        if (timerEl) timerEl.textContent = secondsRemaining;
    }, 1000);
}

function getActiveVideoEl() {
    const local = document.getElementById('localVideo');
    if (local && local.srcObject && local.readyState >= 2) return local;
    const wait = document.getElementById('waitPreview');
    if (wait && wait.srcObject && wait.readyState >= 2) return wait;
    return local || wait || null;
}

async function captureAndInfer() {
    if (inferenceInFlight) return;
    inferenceInFlight = true;

    const video = getActiveVideoEl();
    const canvas = document.getElementById('captureCanvas');
    if (!video || !canvas) {
        inferenceInFlight = false;
        return setRecogStatus('Missing video/canvas');
    }

    canvas.width = INPUT_SIZE;
    canvas.height = INPUT_SIZE;

    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.translate(INPUT_SIZE, 0);
    ctx.scale(-1, 1); // mirror to match the on-screen preview
    ctx.drawImage(video, 0, 0, INPUT_SIZE, INPUT_SIZE);
    ctx.restore();

    const inputTensor = tf.tidy(() =>
        tf.browser.fromPixels(canvas)
            .toFloat()
            .div(255.0)
            .expandDims(0)
    );

    let predTensor = null;
    try {
        // predict() is the safe API for converted Keras/TF graph models.
        const out = App.model.predict(inputTensor);
        predTensor = Array.isArray(out) ? out[0] : out;

        const predictions = await predTensor.data();

        // Argmax.
        let maxIdx = 0;
        for (let i = 1; i < predictions.length; i++) {
            if (predictions[i] > predictions[maxIdx]) maxIdx = i;
        }
        const confidence = predictions[maxIdx];
        const letter = App.classNames[maxIdx] ?? String(maxIdx);

        if (confidence < CONFIDENCE_THRESHOLD) {
            setRecogStatus(`Low confidence (${(confidence * 100).toFixed(1)}%)`);
            const det = document.getElementById('detectedLetter');
            if (det) det.textContent = '—';
            return;
        }

        const det = document.getElementById('detectedLetter');
        if (det) det.textContent = letter;
        appendToTranscript(letter);
        setRecogStatus(`Detected: ${letter} (${(confidence * 100).toFixed(1)}%)`);
    } catch (err) {
        console.error('Inference failed:', err);
        setRecogStatus('⚠ Inference error: ' + err.message);
    } finally {
        inputTensor.dispose();
        if (predTensor && typeof predTensor.dispose === 'function') {
            predTensor.dispose();
        }
        inferenceInFlight = false;
    }
}

// ================= TRANSCRIPT =================
function appendToTranscript(letter) {
    const box = document.getElementById('transcriptBox');
    if (!box) return;

    // Replace the placeholder exactly once, using a data attribute instead of
    // a style-selector (which would also match real entries).
    if (box.dataset.empty !== 'false') {
        box.innerHTML = '';
        box.dataset.empty = 'false';
    }

    const span = document.createElement('span');
    span.className = 'transcript-letter';
    span.textContent = letter;
    span.style.cssText = 'font-size:1.4rem;font-weight:700;margin:2px;';
    box.appendChild(span);
    box.scrollTop = box.scrollHeight;
}

function clearTranscript() {
    const box = document.getElementById('transcriptBox');
    if (box) {
        box.innerHTML =
            '<span class="transcript-placeholder" style="color:#aaa;font-style:italic;">Recognized letters will appear here…</span>';
        box.dataset.empty = 'true';
    }
    const det = document.getElementById('detectedLetter');
    if (det) det.textContent = '—';
}

function setRecogStatus(msg) {
    const el = document.getElementById('recognitionStatus');
    if (el) el.textContent = msg;
}

// ================= CLEANUP =================
function cleanup() {
    tearDownPeer();

    if (App.stream) {
        App.stream.getTracks().forEach(t => {
            try { t.stop(); } catch (_) { }
        });
        App.stream = null;
    }

    if (countdownTimer) {
        clearInterval(countdownTimer);
        countdownTimer = null;
    }

    if (App.socket) {
        try { App.socket.emit('leave_room', { room: App.room }); } catch (_) { }
        try { App.socket.disconnect(); } catch (_) { }
    }
}

// ================= START APP =================
bootApp();