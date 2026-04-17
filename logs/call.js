// ================= CONFIG =================
const MODEL_URL = '/static/models/mobilenet-slsl-1/model.json';
const CLASSES_URL = '/static/models/mobilenet-slsl-1/class_names.json';

const INPUT_SIZE = 128;
const CONFIDENCE_THRESHOLD = 0.55;
const TOTAL_SECONDS = 5;
const CAPTURE_AT_SECOND = 4;

const ICE_CONFIG = {
    iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

// ================= APP STATE =================
const App = {
    room: window.ROOM || document.getElementById('waitRoomCode').textContent,

    stream: null,
    streamReady: null,

    model: null,
    classNames: [],

    socket: null,
    pc: null,

    pendingSignals: [],
    role: null
};

// ================= BOOT =================
async function bootApp() {
    try {
        await initMedia();
        await initModel();
        initSocket();
        initUI();
    } catch (err) {
        console.error("Boot failed:", err);
    }
}

// ================= MEDIA =================
async function initMedia() {
    App.streamReady = navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
    });

    App.stream = await App.streamReady;

    const preview = document.getElementById('waitPreview');
    if (preview) preview.srcObject = App.stream;
}

// ================= MODEL =================
async function initModel() {
  setRecogStatus('Loading model…');

  try {
    const res = await fetch(CLASSES_URL);

    if (!res.ok) {
      throw new Error("Failed to load class_names.json");
    }

    const raw = await res.json();

    App.classNames = Array.isArray(raw)
      ? raw
      : Object.values(raw);

    if (!App.classNames || App.classNames.length === 0) {
      throw new Error("Class names empty or invalid");
    }

    App.model = await tf.loadGraphModel(MODEL_URL);

    setRecogStatus('Model ready — press ▶ to start');
    document.getElementById('btnStartRecog').disabled = false;

  } catch (err) {
    console.error("Model init failed:", err);
    setRecogStatus("Model load error: " + err.message);
  }
}

// ================= SOCKET =================
function initSocket() {
    App.socket = io();

    App.socket.emit('join_room', { room: App.room });

    App.socket.on('role', ({ role }) => {
        App.role = role;
    });

    App.socket.on('peer_ready', async () => {
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
        document.getElementById('remoteVideo').srcObject = null;
    });
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
            document.getElementById('remoteVideo').srcObject =
                event.streams[0];
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
            const state = App.pc.connectionState;
            if (state === 'connected') {
                setCallStatus('Connected', true);
            } else if (state === 'failed' || state === 'disconnected') {
                setCallStatus('Disconnected', false);
            }
        };
    }

    // flush queued signals
    while (App.pendingSignals.length) {
        await handleSignal(App.pendingSignals.shift());
    }

    if (App.role === 'caller') {
        const offer = await App.pc.createOffer();
        await App.pc.setLocalDescription(offer);

        App.socket.emit('signal', {
            room: App.room,
            type: 'offer',
            sdp: App.pc.localDescription
        });
    }
}

// ================= SIGNALING =================
async function handleSignal({ type, sdp, candidate }) {
    try {
        switch (type) {
            case 'offer': {
                await App.pc.setRemoteDescription(
                    new RTCSessionDescription(sdp)
                );

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
                await App.pc.setRemoteDescription(
                    new RTCSessionDescription(sdp)
                );
                break;
            }

            case 'ice-candidate': {
                if (candidate) {
                    await App.pc.addIceCandidate(
                        new RTCIceCandidate(candidate)
                    );
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
    document.getElementById('waitRoomCode').textContent = App.room;
    document.getElementById('callRoomCode').textContent = App.room;
}

function enterCallPhase() {
    document.getElementById('waiting-room').style.display = 'none';
    document.getElementById('calling-room').style.display = '';

    if (App.stream) {
        document.getElementById('localVideo').srcObject = App.stream;
    }
}

function setCallStatus(text, ok) {
    const el = document.getElementById('callStatus');
    const dot = el.querySelector('.status-dot');
    const textEl = document.getElementById('callStatusText');

    el.className = `status-badge status-badge--${ok ? 'connected' : 'waiting'}`;
    dot.style.background = ok ? '#27ae60' : '#e74c3c';
    textEl.textContent = text;
}

// ================= RECOGNITION =================
let countdownTimer = null;
let secondsRemaining = TOTAL_SECONDS;

function startRecognition() {
    if (!App.model) return setRecogStatus('Model not ready');

    const video = document.getElementById('localVideo');
    if (!video || video.readyState < 2)
        return setRecogStatus('Video not ready');

    document.getElementById('btnStartRecog').disabled = true;

    secondsRemaining = TOTAL_SECONDS;
    document.getElementById('timerDisplay').style.display = 'block';

    countdownTimer = setInterval(() => {
        if (secondsRemaining === CAPTURE_AT_SECOND) {
            captureAndInfer();
        }

        document.getElementById('timerDisplay').textContent =
            secondsRemaining--;

        if (secondsRemaining < 0) {
            clearInterval(countdownTimer);
            countdownTimer = null;

            document.getElementById('timerDisplay').style.display = 'none';
            document.getElementById('btnStartRecog').disabled = false;

            setRecogStatus('Done — press ▶ again');
        }
    }, 1000);
}

async function captureAndInfer() {
    const video = document.getElementById('localVideo');
    const canvas = document.getElementById('captureCanvas');

    canvas.width = INPUT_SIZE;
    canvas.height = INPUT_SIZE;

    const ctx = canvas.getContext('2d');

    ctx.save();
    ctx.translate(INPUT_SIZE, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, INPUT_SIZE, INPUT_SIZE);
    ctx.restore();

    const tensor = tf.tidy(() => {
        return tf.browser.fromPixels(canvas)
            .toFloat()
            .div(255.0)
            .expandDims(0);
    });

    // 🔥 DEBUG #1: input going into model
    console.log("INPUT SHAPE:", tensor.shape);
    console.log("INPUT SAMPLE:", tensor.dataSync().slice(0, 10));

    let predTensor;

    try {
        console.log("MODEL INPUTS:", App.model.inputs);
        console.log("MODEL OUTPUTS:", App.model.outputs);
        console.log("USING EXECUTE()");
        predTensor = App.model.execute(tensor);
        const predictions = await predTensor.data();
        console.log("CLASS COUNT:", classNames.length);
        console.log("MODEL OUTPUT SIZE:", predictions.length);
        console.log("TOP RAW OUTPUT:", predictions);

        let maxIdx = 0;
        for (let i = 1; i < predictions.length; i++) {
            if (predictions[i] > predictions[maxIdx]) maxIdx = i;
        }

        const confidence = predictions[maxIdx];
        const letter = App.classNames[maxIdx] ?? String(maxIdx);

        if (confidence < CONFIDENCE_THRESHOLD) {
            setRecogStatus('No confident prediction');
            return;
        }

        document.getElementById('detectedLetter').textContent = letter;
        appendToTranscript(letter);

        setRecogStatus(
            `Detected: ${letter} (${(confidence * 100).toFixed(1)}%)`
        );

    } catch (err) {
        setRecogStatus('⚠ Inference error: ' + err.message);
    } finally {
        tensor.dispose();
        if (predTensor) predTensor.dispose();
    }
}

// ================= TRANSCRIPT =================
function appendToTranscript(letter) {
    const box = document.getElementById('transcriptBox');

    if (box.querySelector('span[style]')) box.innerHTML = '';

    const span = document.createElement('span');
    span.textContent = letter;
    span.style.cssText =
        'font-size:1.4rem;font-weight:700;margin:2px;';
    box.appendChild(span);

    box.scrollTop = box.scrollHeight;
}

function clearTranscript() {
    document.getElementById('transcriptBox').innerHTML =
        '<span style="color:#aaa;font-style:italic;">Recognized letters will appear here…</span>';

    document.getElementById('detectedLetter').textContent = '—';
}

function setRecogStatus(msg) {
    document.getElementById('recognitionStatus').textContent = msg;
}

// ================= CLEANUP =================
function cleanup() {
    if (App.pc) {
        App.pc.close();
        App.pc = null;
    }

    if (App.stream) {
        App.stream.getTracks().forEach(t => t.stop());
        App.stream = null;
    }

    App.pendingSignals = [];
}

// ================= START APP =================
bootApp();