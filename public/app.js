/**
 * PERSONAL JARVIS — HOLOGRAPHIC CLOUD CLIENT ENGINE
 * Handles Canvas Arc Reactor animation, Web Speech API (STT/TTS),
 * Wake-Word continuous detection, and Vercel Serverless communication.
 */

// 1. Language Mapping for Web Speech Recognition & Synthesis
const LANG_VOICE_MAP = {
  en: "en-US",
  ta: "ta-IN",
  hi: "hi-IN",
  te: "te-IN",
  ml: "ml-IN",
  kn: "kn-IN",
  de: "de-DE",
  fr: "fr-FR",
  es: "es-ES",
  ja: "ja-JP",
};

// 2. DOM Elements
const canvas = document.getElementById("arcCanvas");
const ctx = canvas.getContext("2d");
const hudStateLabel = document.getElementById("hudStateLabel");
const chatStream = document.getElementById("chatStream");
const commandInput = document.getElementById("commandInput");
const sendBtn = document.getElementById("sendBtn");
const voiceBtn = document.getElementById("voiceBtn");
const wakeBtn = document.getElementById("wakeBtn");
const stopVoiceBtn = document.getElementById("stopVoiceBtn");
const langSelect = document.getElementById("langSelect");
const bootTime = document.getElementById("bootTime");
const clearChatBtn = document.getElementById("clearChatBtn");

if (bootTime) {
  bootTime.textContent = new Date().toLocaleTimeString();
}

// 3. State Management
let hudState = "READY"; // READY, LISTENING, PROCESSING, SPEAKING, ERROR
let isRecording = false;
let isWakeEnabled = false;
let isSpeaking = false;
let recognition = null;
let wakeRecognition = null;
let rotationAngle = 0;
let pulsePhase = 0;
let audioLevel = 0.1;

// 4. Arc Reactor 60 FPS Canvas Renderer
function drawArcReactor() {
  const width = canvas.width;
  const height = canvas.height;
  const centerX = width / 2;
  const centerY = height / 2;

  ctx.clearRect(0, 0, width, height);

  // Determine state colors
  let primaryColor = "#00e5ff";
  let secondaryColor = "#007799";
  let pulseSpeed = 0.05;

  if (hudState === "LISTENING") {
    primaryColor = "#00ffff";
    secondaryColor = "#00aaff";
    pulseSpeed = 0.12;
  } else if (hudState === "PROCESSING") {
    primaryColor = "#38ef7d";
    secondaryColor = "#11998e";
    pulseSpeed = 0.15;
  } else if (hudState === "SPEAKING") {
    primaryColor = "#00f2fe";
    secondaryColor = "#4facfe";
    pulseSpeed = 0.09;
  } else if (hudState === "ERROR") {
    primaryColor = "#ff416c";
    secondaryColor = "#ff4b2b";
    pulseSpeed = 0.08;
  }

  // Update phases
  rotationAngle += (hudState === "PROCESSING" ? 0.04 : 0.015);
  pulsePhase += pulseSpeed;
  const pulseFactor = 0.85 + 0.15 * Math.sin(pulsePhase) + audioLevel * 0.25;

  // 1. Outer Holographic Glow Ring
  ctx.save();
  ctx.beginPath();
  const grad = ctx.createRadialGradient(centerX, centerY, 30, centerX, centerY, 90);
  grad.setColorAt(0, "rgba(0, 229, 255, 0.02)");
  grad.setColorAt(0.7, "rgba(0, 229, 255, 0.06)");
  grad.setColorAt(1, "rgba(0, 229, 255, 0)");
  ctx.fillStyle = grad;
  ctx.arc(centerX, centerY, 95, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  // 2. Outer Rotating Segment Ring
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(rotationAngle);
  ctx.lineWidth = 3;
  ctx.strokeStyle = primaryColor;
  const segments = 12;
  for (let i = 0; i < segments; i++) {
    const startA = (i * (Math.PI * 2) / segments) + 0.08;
    const endA = ((i + 1) * (Math.PI * 2) / segments) - 0.08;
    ctx.beginPath();
    ctx.arc(0, 0, 78 * pulseFactor, startA, endA);
    ctx.stroke();
  }
  ctx.restore();

  // 3. Counter-Rotating Inner Ring
  ctx.save();
  ctx.translate(centerX, centerY);
  ctx.rotate(-rotationAngle * 1.4);
  ctx.lineWidth = 2;
  ctx.strokeStyle = secondaryColor;
  for (let i = 0; i < 6; i++) {
    const angle = (i * Math.PI) / 3;
    const x1 = Math.cos(angle) * 52;
    const y1 = Math.sin(angle) * 52;
    const x2 = Math.cos(angle) * 62;
    const y2 = Math.sin(angle) * 62;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.arc(0, 0, 52, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  // 4. Central Glowing Core Node
  ctx.save();
  ctx.beginPath();
  const coreGrad = ctx.createRadialGradient(centerX, centerY, 5, centerX, centerY, 30);
  coreGrad.setColorAt(0, "#ffffff");
  coreGrad.setColorAt(0.4, primaryColor);
  coreGrad.setColorAt(1, "transparent");
  ctx.fillStyle = coreGrad;
  ctx.arc(centerX, centerY, 24 * pulseFactor, 0, Math.PI * 2);
  ctx.fill();

  ctx.lineWidth = 2;
  ctx.strokeStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(centerX, centerY, 12 * pulseFactor, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();

  requestAnimationFrame(drawArcReactor);
}
requestAnimationFrame(drawArcReactor);

function setHudState(state) {
  hudState = state;
  hudStateLabel.textContent = state;
  if (state === "READY") {
    hudStateLabel.style.color = "#00e5ff";
  } else if (state === "LISTENING") {
    hudStateLabel.style.color = "#00ffff";
  } else if (state === "PROCESSING") {
    hudStateLabel.style.color = "#38ef7d";
  } else if (state === "SPEAKING") {
    hudStateLabel.style.color = "#00f2fe";
  } else if (state === "ERROR") {
    hudStateLabel.style.color = "#ff416c";
  }
}

// 5. Chat UI Helpers
function appendMessage(speaker, text, meta = "") {
  const msgEl = document.createElement("div");
  msgEl.className = `chat-message ${speaker.toLowerCase()}-msg`;

  const header = document.createElement("div");
  header.className = "msg-header";

  const speakerEl = document.createElement("span");
  speakerEl.className = "speaker";
  speakerEl.textContent = speaker;

  header.appendChild(speakerEl);

  if (meta) {
    const metaEl = document.createElement("span");
    metaEl.className = "meta-tag";
    metaEl.textContent = `[${meta}]`;
    header.appendChild(metaEl);
  }

  const timeEl = document.createElement("span");
  timeEl.className = "time";
  timeEl.textContent = new Date().toLocaleTimeString();
  header.appendChild(timeEl);

  const bodyEl = document.createElement("div");
  bodyEl.className = "msg-body";
  bodyEl.textContent = text;

  msgEl.appendChild(header);
  msgEl.appendChild(bodyEl);

  chatStream.appendChild(msgEl);
  chatStream.scrollTop = chatStream.scrollHeight;
}

if (clearChatBtn) {
  clearChatBtn.addEventListener("click", () => {
    chatStream.innerHTML = "";
    appendMessage("SYSTEM", "Holographic stream cleared.", "RESET");
  });
}

// 6. Speech Synthesis (TTS)
function speakText(text, langCode = "en", callback) {
  if (!("speechSynthesis" in window)) {
    if (callback) callback();
    return;
  }

  window.speechSynthesis.cancel();
  isSpeaking = true;
  setHudState("SPEAKING");

  const utterance = new SpeechSynthesisUtterance(text);
  const targetTag = LANG_VOICE_MAP[langCode] || "en-US";
  utterance.lang = targetTag;
  utterance.rate = 1.0;
  utterance.pitch = 1.0;

  // Attempt to select an exact matching voice
  const voices = window.speechSynthesis.getVoices();
  const matchedVoice = voices.find(v => v.lang.startsWith(targetTag) || v.lang.startsWith(langCode));
  if (matchedVoice) {
    utterance.voice = matchedVoice;
  }

  utterance.onend = () => {
    isSpeaking = false;
    setHudState("READY");
    if (callback) callback();
  };

  utterance.onerror = () => {
    isSpeaking = false;
    setHudState("READY");
    if (callback) callback();
  };

  window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
  isSpeaking = false;
  setHudState("READY");
  appendMessage("SYSTEM", "Speech output halted.", "AUDIO CONTROL");
}

if (stopVoiceBtn) {
  stopVoiceBtn.addEventListener("click", stopSpeaking);
}

// 7. Backend Communication (/api)
async function transmitQuery(text) {
  if (!text || !text.trim()) return;

  const query = text.trim();
  appendMessage("YOU", query);
  commandInput.value = "";
  setHudState("PROCESSING");

  const prefLang = langSelect.value;

  try {
    const res = await fetch("/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: query,
        preferred_language: prefLang,
      }),
    });

    if (!res.ok) {
      throw new Error(`Cloud server returned HTTP ${res.status}`);
    }

    const data = await res.json();
    const reply = data.text || "Command acknowledged.";
    const detected = data.detected_language || "en";
    const respLang = data.response_language || "en";
    const provider = data.provider || "JARVIS Cloud";

    appendMessage("JARVIS", reply, `${provider} • ${respLang.toUpperCase()}`);

    // Synthesize speech output in target language
    speakText(reply, respLang);
  } catch (err) {
    console.warn("Serverless API unavailable, running client offline fallback:", err);
    // Offline local fallback
    handleOfflineQuery(query, prefLang);
  }
}

function handleOfflineQuery(query, prefLang) {
  const low = query.toLowerCase();
  let reply = "";
  let respLang = prefLang === "auto" ? "en" : prefLang;

  if (low.includes("time") || low.includes("neram") || low.includes("samay")) {
    reply = `The current client time is ${new Date().toLocaleTimeString()}.`;
  } else if (low.includes("date") || low.includes("thethi") || low.includes("tarikh")) {
    reply = `Today is ${new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}.`;
  } else if (low.includes("status") || low.includes("vitals")) {
    reply = "JARVIS Web Holographic Client is active and connected via HTTPS.";
  } else {
    reply = `Transmitted query: "${query}". Connecting to neural cloud stream...`;
  }

  appendMessage("JARVIS", reply, "OFFLINE CLIENT CORE");
  speakText(reply, respLang);
}

// 8. Push-to-Talk Speech Recognition
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("Web Speech API not supported in this browser.");
    voiceBtn.disabled = true;
    voiceBtn.title = "Speech Recognition not supported in this browser";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isRecording = true;
    voiceBtn.classList.add("danger");
    voiceBtn.innerHTML = '<span class="btn-icon">🔴</span> STOP RECORDING';
    setHudState("LISTENING");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    transmitQuery(transcript);
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    setHudState("READY");
    if (event.error !== "no-speech") {
      appendMessage("SYSTEM", `Voice recognition alert: ${event.error}`, "AUDIO ERROR");
    }
  };

  recognition.onend = () => {
    isRecording = false;
    voiceBtn.classList.remove("danger");
    voiceBtn.innerHTML = '<span class="btn-icon">🎤</span> START VOICE INPUT';
    if (hudState === "LISTENING") {
      setHudState("READY");
    }
  };
}

function toggleVoiceRecording() {
  if (!recognition) {
    setupSpeechRecognition();
  }
  if (!recognition) {
    appendMessage("SYSTEM", "Microphone access is not supported on this browser.", "VOICE ERROR");
    return;
  }

  if (!isRecording) {
    const selected = langSelect.value;
    recognition.lang = LANG_VOICE_MAP[selected] || "en-US";
    try {
      recognition.start();
    } catch (e) {
      console.warn("Recognition start error:", e);
    }
  } else {
    recognition.stop();
  }
}

if (voiceBtn) {
  voiceBtn.addEventListener("click", toggleVoiceRecording);
}

// 9. Continuous Hands-Free Wake-Word ("Hey Jarvis")
function setupWakeWordEngine() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  wakeRecognition = new SpeechRecognition();
  wakeRecognition.continuous = true;
  wakeRecognition.interimResults = true;
  wakeRecognition.lang = "en-US";

  wakeRecognition.onresult = (event) => {
    // If JARVIS is speaking, suppress wake-word processing (Echo Suppression)
    if (isSpeaking) return;

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const phrase = event.results[i][0].transcript.toLowerCase();
      if (phrase.includes("hey jarvis") || phrase.includes("jarvis")) {
        wakeRecognition.stop();
        appendMessage("SYSTEM", "Wake phrase detected! Listening for command...", "WAKE ACTIVATION");
        setHudState("LISTENING");
        speakText("Yes? I am listening.", "en", () => {
          setTimeout(toggleVoiceRecording, 400);
        });
        break;
      }
    }
  };

  wakeRecognition.onend = () => {
    if (isWakeEnabled && !isRecording) {
      try {
        wakeRecognition.start();
      } catch (e) {}
    }
  };
}

function toggleWakeWord() {
  if (!wakeRecognition) {
    setupWakeWordEngine();
  }
  isWakeEnabled = !isWakeEnabled;

  if (isWakeEnabled) {
    wakeBtn.classList.add("primary");
    wakeBtn.innerHTML = '<span class="btn-icon">⚡</span> DISABLE "HEY JARVIS"';
    appendMessage("SYSTEM", 'Continuous wake-word engine active. Say "Hey Jarvis" to activate.', "WAKE ENGINE");
    try {
      wakeRecognition.start();
    } catch (e) {}
  } else {
    wakeBtn.classList.remove("primary");
    wakeBtn.innerHTML = '<span class="btn-icon">⚡</span> ENABLE "HEY JARVIS"';
    appendMessage("SYSTEM", "Wake-word engine paused.", "WAKE ENGINE");
    try {
      wakeRecognition.stop();
    } catch (e) {}
  }
}

if (wakeBtn) {
  wakeBtn.addEventListener("click", toggleWakeWord);
}

// 10. Quick Action Chips
document.querySelectorAll(".chip-btn").forEach((chip) => {
  chip.addEventListener("click", () => {
    const q = chip.getAttribute("data-query");
    if (q) transmitQuery(q);
  });
});

// 11. Command Input Bar
if (sendBtn && commandInput) {
  sendBtn.addEventListener("click", () => {
    transmitQuery(commandInput.value);
  });
  commandInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      transmitQuery(commandInput.value);
    }
  });
}

// 12. Preload SpeechSynthesis Voices
if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
  };
}

setupSpeechRecognition();
