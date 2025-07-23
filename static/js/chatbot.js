const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const chatWindow = document.getElementById("chatWindow");
const replySound = document.getElementById("replySound");
const micButton = document.getElementById("micButton");
const micLoader = document.getElementById("micLoader");

// Handle form submission
chatForm.addEventListener("submit", async function (e) {
  e.preventDefault();
  const message = userInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  userInput.value = "";
  showTyping();

  try {
    const res = await fetch("/chatbot-response", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    const data = await res.json();

    setTimeout(() => {
      removeTyping();
      typeBotMessage(data.response || "Sorry, no response from AURA.");
      replySound.play();
      speak(data.response || "Sorry, I'm unable to respond at the moment.");
      showSuggestions(data.suggestions);
    }, 2000);
  } catch (error) {
    console.error("Error talking to AURA:", error);
    removeTyping();
    appendMessage("bot", "Oops! Something went wrong.");
  }
});

// Append message
function appendMessage(sender, text) {
  const msg = document.createElement("div");
  msg.classList.add("message", sender);
  msg.innerHTML = `<div class="bubble">${text}</div>`;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Typing dots
function showTyping() {
  const typing = document.createElement("div");
  typing.classList.add("typing", "bot");
  typing.innerHTML = `<div class="bubble typing-dots"><span></span><span></span><span></span></div>`;
  chatWindow.appendChild(typing);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTyping() {
  const typing = document.querySelector(".typing");
  if (typing) typing.remove();
}

// Bot message typing animation
function typeBotMessage(text) {
  const msg = document.createElement("div");
  msg.classList.add("message", "bot");

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  msg.appendChild(bubble);
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  let i = 0;
  const typingSpeed = 20;

  const typeInterval = setInterval(() => {
    if (i < text.length) {
      bubble.innerHTML += text.charAt(i);
      chatWindow.scrollTop = chatWindow.scrollHeight;
      i++;
    } else {
      clearInterval(typeInterval);
    }
  }, typingSpeed);
}

// Voice output with tone effect
function speak(text) {
  const synth = window.speechSynthesis;
  const utter = new SpeechSynthesisUtterance(text);
  utter.pitch = 1.8; // Higher pitch for robotic tone
  utter.rate = 0.85; // Slightly slower
  utter.volume = 1;

  const voices = synth.getVoices();
  if (!voices.length) {
    synth.onvoiceschanged = () => speak(text);
    return;
  }

  utter.voice = voices.find(v => v.name.includes("Zira") || v.name.includes("Samantha")) || voices[0];
  synth.cancel();
  synth.speak(utter);
}

// Clear chat
document.getElementById("clearChat").addEventListener("click", () => {
  chatWindow.innerHTML = `<div class="text-center text-muted small">Say “hello” to get started…</div>`;
});

// Suggestions
function showSuggestions(suggestions) {
  const sugList = document.getElementById("suggestions");
  sugList.innerHTML = "";

  if (suggestions && suggestions.length) {
    suggestions.forEach(s => {
      const li = document.createElement("li");
      li.className = "list-group-item list-group-item-action";
      li.textContent = s;
      li.onclick = () => {
        userInput.value = s;
        userInput.focus();
      };
      sugList.appendChild(li);
    });
  }
}

// Mic speech recognition with loader
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();

  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  micButton.addEventListener("click", () => {
    recognition.start();
    micButton.classList.add("active", "waveform");
    micLoader.style.display = "inline";
  });

  recognition.onresult = function (event) {
    const transcript = event.results[0][0].transcript;
    userInput.value = transcript;
    micButton.classList.remove("active", "waveform");
    micLoader.style.display = "none";
    chatForm.dispatchEvent(new Event("submit"));
  };

  recognition.onerror = function (event) {
    console.error("Speech recognition error:", event.error);
    micButton.classList.remove("active", "waveform");
    micLoader.style.display = "none";
  };

  recognition.onend = function () {
    micButton.classList.remove("active", "waveform");
    micLoader.style.display = "none";
  };
} else {
  console.warn("Speech recognition not supported.");
  micButton.disabled = true;
  micButton.title = "Speech recognition not supported in this browser.";
}
