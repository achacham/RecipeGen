// static/js/chat.js
console.log("CHAT MODULE ▶️ Loaded");

export function initChatModule() {
  const input      = document.getElementById("chatInput");
  const sendBtn    = document.getElementById("sendChat");
  const chatWindow = document.getElementById("chatMessages");

  if (!input || !sendBtn || !chatWindow) {
    console.error("Chat module: missing DOM elements");
    return;
  }

  sendBtn.onclick = () => {
    const message = input.value.trim();
    if (!message) return;

    // 1️⃣ Show the user’s message
    chatWindow.innerHTML += `
      <div class="mb-1 text-right text-sm text-gray-800">
        <strong>You:</strong> ${message}
      </div>`;
    input.value = "";
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // 2️⃣ Insert “thinking…” indicator
    const indicator = document.createElement("div");
    indicator.id = "typingIndicator";
    indicator.className = "text-left text-sm text-gray-600 italic";
    chatWindow.appendChild(indicator);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    let dots = 0;
    const dotInterval = setInterval(() => {
      dots = (dots + 1) % 4;
      indicator.textContent = "Bot is thinking" + ".".repeat(dots);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 500);

    // 3️⃣ Send the request (with your session cookie)
    fetch("/chat", {
      method: "POST",
      credentials: "include",            // ← send login cookie
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    })
      .then(response => {
        clearInterval(dotInterval);
        indicator.remove();
        if (!response.ok) {
          throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
      })
      .then(res => {
        const reply =
          res.reply ||
          res.message ||
          (res.choices?.[0]?.message?.content) ||
          "Error: No reply received.";

        // 4️⃣ Show the bot’s reply
        chatWindow.innerHTML += `
          <div class="mb-2 text-left text-sm text-gray-700">
            <strong>Bot:</strong> ${reply}
          </div>`;
      })
      .catch(err => {
        console.error("Chat error:", err);
        chatWindow.innerHTML += `
          <div class="mb-2 text-left text-sm text-red-600">
            <strong>Bot:</strong> Error—please try again.
          </div>`;
      })
      .finally(() => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
      });
  };
}
