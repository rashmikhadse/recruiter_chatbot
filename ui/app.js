// Run code only after HTML is fully loaded
document.addEventListener("DOMContentLoaded", () => {

  // Chat messages container
  const chatMessages = document.getElementById("chat-messages");

  // Text input area
  const chatInput = document.getElementById("chat-input");

  // Send button
  const sendButton = document.getElementById("send-button");

  // Main send message function
  function sendMessage() {

    // Read and trim input
    const messageText = chatInput.value.trim();

    // Do nothing if input is empty
    if (messageText === "") return;

    // ---------- USER MESSAGE ----------
    const userMessage = document.createElement("div");
    userMessage.className = "message user-message";
    userMessage.textContent = messageText;
    chatMessages.appendChild(userMessage);

    // Clear input
    chatInput.value = "";

    // Scroll down
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // ---------- THINKING INDICATOR ----------
    const thinkingMessage = document.createElement("div");
    thinkingMessage.className = "message bot-message thinking";
    thinkingMessage.textContent = "Thinking...";
    chatMessages.appendChild(thinkingMessage);

    chatMessages.scrollTop = chatMessages.scrollHeight;

    // ---------- SIMULATED BOT RESPONSE ----------
    setTimeout(() => {

      // Remove thinking message
      thinkingMessage.remove();

      // Bot reply
      const botMessage = document.createElement("div");
      botMessage.className = "message bot-message";
      botMessage.textContent = "Got it! I’ve received your message.";
      chatMessages.appendChild(botMessage);

      chatMessages.scrollTop = chatMessages.scrollHeight;

    }, 1200);
  }

  // Send on button click
  sendButton.addEventListener("click", sendMessage);

  // Keyboard handling
  chatInput.addEventListener("keydown", (event) => {

    // Enter → send
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }

    // Shift + Enter → newline (default behavior)
  });
});
