// Run this code only after the HTML page is fully loaded
document.addEventListener("DOMContentLoaded", () => {

  // Reference to the container where messages are shown
  const chatMessages = document.getElementById("chat-messages");

  // Reference to the textarea where user types
  const chatInput = document.getElementById("chat-input");

  // Reference to the send button
  const sendButton = document.getElementById("send-button");

  // Main function to send a message
  function sendMessage() {

    // Read user input and remove extra spaces
    const messageText = chatInput.value.trim();

    // Stop if input is empty
    if (messageText === "") return;

    // ---------- USER MESSAGE ----------

    // Create a div for user's message
    const userMessage = document.createElement("div");

    // Apply user message styling
    userMessage.className = "user-message";

    // Preserve formatting exactly as typed
    userMessage.textContent = messageText;

    // Add message to chat
    chatMessages.appendChild(userMessage);

    // Clear textarea after sending
    chatInput.value = "";

    // Reset textarea height back to original
    chatInput.style.height = "auto";

    // Scroll chat to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // ---------- THINKING INDICATOR ----------

    // Create bot "Thinking..." message
    const thinking = document.createElement("div");

    // Apply bot styling
    thinking.className = "bot-message";

    // Show thinking text
    thinking.textContent = "Thinking...";

    // Add to chat
    chatMessages.appendChild(thinking);

    // Scroll again
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // ---------- SIMULATED BOT RESPONSE ----------

    // Simulate backend delay
    setTimeout(() => {

      // Remove thinking indicator
      thinking.remove();

      // Create actual bot response
      const botMessage = document.createElement("div");

      // Apply bot styling
      botMessage.className = "bot-message";

      // Temporary response text
      botMessage.textContent = "Got it! I’ve received your message.";

      // Add to chat
      chatMessages.appendChild(botMessage);

      // Scroll to bottom
      chatMessages.scrollTop = chatMessages.scrollHeight;

    }, 1200);
  }

  // Send message when send button is clicked
  sendButton.addEventListener("click", sendMessage);

  // Keyboard behavior inside textarea
  chatInput.addEventListener("keydown", (e) => {

    // Enter without Shift → send message
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();            // Prevent new line
      sendMessage();                 // Send message
    }

    // Shift + Enter → default behavior (new line)
  });

  // Auto-resize textarea while typing
  chatInput.addEventListener("input", () => {

    // Reset height so shrinking works
    chatInput.style.height = "auto";

    // Expand height up to 200px max
    chatInput.style.height =
      Math.min(chatInput.scrollHeight, 200) + "px";
  });

  // Reference to hidden file input
const fileInput = document.getElementById("file-input");

// Reference to attach (+) button
const attachButton = document.getElementById("attach-button");

// When + button is clicked, open file picker
attachButton.addEventListener("click", () => {
  fileInput.click(); // Opens system file dialog
});

// When a file is selected
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];

  // If no file selected, do nothing
  if (!file) return;

  // Temporary UI feedback (later we’ll upload it)
  const fileMessage = document.createElement("div");
  fileMessage.className = "user-message";
  fileMessage.textContent = `📎 Attached: ${file.name}`;
  chatMessages.appendChild(fileMessage);

  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Reset input so same file can be re-selected later
  fileInput.value = "";
});


});
