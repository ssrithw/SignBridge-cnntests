// ================= MODEL CONFIG =================
const MODEL_URL = '/static/models/mobilenet-slsl-1/model.json';
const CLASSES_URL = '/static/models/mobilenet-slsl-1/class_names.json';

const INPUT_SIZE = 128;
const CONFIDENCE_THRESHOLD = 0.55;
const TOTAL_SECONDS = 5;
const CAPTURE_AT_SECOND = 4;

// ================= STATE =================
let model = null;
let classNames = [];
let countdownTimer = null;
let secondsRemaining = TOTAL_SECONDS;

// exposed so room.js can use it
window.localStream = null;
window.localStreamReady = null;

// ================= INIT =================
(async function initModelAndCamera() {
  try {
    window.localStreamReady = navigator.mediaDevices.getUserMedia({
      video: true,
      audio: true
    });

    window.localStream = await window.localStreamReady;

    const preview = document.getElementById('waitPreview');
    if (preview) preview.srcObject = window.localStream;

  } catch (err) {
    const status = document.getElementById('waitPreviewStatus');
    if (status) status.textContent =
      'Camera / mic access denied — please allow and reload.';
    return;
  }

  loadModel();
})();

// ================= MODEL LOADING =================
async function loadModel() {
  setRecogStatus('Loading model…');

  try {
    const res = await fetch(CLASSES_URL);
    const raw = await res.json();
    classNames = Array.isArray(raw) ? raw : Object.values(raw);

    model = await tf.loadGraphModel(MODEL_URL);

    setRecogStatus('Model ready — press ▶ to start');
    document.getElementById('btnStartRecog').disabled = false;
  } catch (err) {
    console.error(err);
    setRecogStatus('⚠ Model failed: ' + err.message);
  }
}

// ================= RECOGNITION =================
function startRecognition() {
  if (!model) return setRecogStatus('Model not ready');

  const video = document.getElementById('localVideo');
  if (!video || video.readyState < 2) return setRecogStatus('Video not ready');

  document.getElementById('btnStartRecog').disabled = true;

  secondsRemaining = TOTAL_SECONDS;
  document.getElementById('timerDisplay').style.display = 'block';

  countdownTimer = setInterval(() => {
    if (secondsRemaining === CAPTURE_AT_SECOND) {
      captureAndInfer();
    }

    document.getElementById('timerDisplay').textContent = secondsRemaining--;

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

  const tensor = tf.tidy(() =>
    tf.browser.fromPixels(canvas).toFloat().expandDims(0)
  );

  let predTensor;
  try {
    predTensor = model.execute(tensor);
    const predictions = await predTensor.data();

    let maxIdx = 0;
    for (let i = 1; i < predictions.length; i++) {
      if (predictions[i] > predictions[maxIdx]) maxIdx = i;
    }

    const confidence = predictions[maxIdx];
    const letter = classNames[maxIdx] ?? String(maxIdx);

    if (confidence < CONFIDENCE_THRESHOLD) {
      setRecogStatus('No confident prediction');
      return;
    }

    document.getElementById('detectedLetter').textContent = letter;
    appendToTranscript(letter);

    setRecogStatus(`Detected: ${letter} (${(confidence * 100).toFixed(1)}%)`);

  } catch (err) {
    setRecogStatus('⚠ Inference error: ' + err.message);
  } finally {
    tensor.dispose();
    if (predTensor) predTensor.dispose();
  }
}

// ================= UI HELPERS =================
function appendToTranscript(letter) {
  const box = document.getElementById('transcriptBox');

  if (box.querySelector('span[style]')) box.innerHTML = '';

  const span = document.createElement('span');
  span.textContent = letter;
  span.style.cssText = 'font-size:1.4rem;font-weight:700;margin:2px;';
  box.appendChild(span);

  box.scrollTop = box.scrollHeight;
}

function setRecogStatus(msg) {
  document.getElementById('recognitionStatus').textContent = msg;
}

function clearTranscript() {
  document.getElementById('transcriptBox').innerHTML =
    '<span style="color:#aaa;font-style:italic;">Recognized letters will appear here…</span>';

  document.getElementById('detectedLetter').textContent = '—';
}