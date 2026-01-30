console.log("APP.JS LOADED AT", new Date().toISOString());

// --------------------------------------------------
// GLOBAL STATE FLAGS
// --------------------------------------------------

// Indicates app loaded with NO conversations in DB
let isFreshStart = false;

// --------------------------------------------------
// MAIN BOOTSTRAP
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", async () => {

  // -------------------------------
  // DOM REFERENCES
  // -------------------------------

  const chatMessages = document.getElementById("chat-messages");
  const chatInput = document.getElementById("chat-input");
  const sendButton = document.getElementById("send-button");
  const fileInput = document.getElementById("file-input");
  const attachButton = document.getElementById("attach-button");
  const newChatButton = document.querySelector(".new-chat-btn");

  // -------------------------------
  // SEND MESSAGE
  // -------------------------------

  async function sendMessage() {

    // Remove welcome message if present
    const welcomeMessage = document.getElementById("welcome-message");
    if (welcomeMessage) welcomeMessage.remove();

    const messageText = chatInput.value.trim();
    if (!messageText) return;

    // Detect whether this is a NEW chat
    const previousConversationId = localStorage.getItem("conversation_id");
    const isNewChat = isFreshStart || !previousConversationId;

    // Render user message immediately
    appendUserMessage(messageText);

    chatInput.value = "";
    chatInput.style.height = "auto";

    // Thinking indicator
    const thinking = document.createElement("div");
    thinking.className = "bot-message";
    thinking.textContent = "Thinking...";
    chatMessages.appendChild(thinking);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: previousConversationId,
          message: messageText
        })
      });

      const data = await response.json();

      // Persist conversation_id
      localStorage.setItem("conversation_id", data.conversation_id);

      // If this was first message of a new chat → add sidebar item immediately
      if (isNewChat) {
        addConversationToSidebar({
          conversation_id: data.conversation_id,
          title: messageText.split(" ").slice(0, 6).join(" ")
        });

        // Cold-start handled — reset flag
        isFreshStart = false;
      }

      thinking.remove();
      appendAssistantMessage(data.reply);

    } catch (error) {
      thinking.remove();
      appendAssistantMessage("Something went wrong. Please try again.");
      console.error("Chat error:", error);
    }
  }

  // -------------------------------
  // EVENT LISTENERS
  // -------------------------------

  sendButton.addEventListener("click", sendMessage);

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + "px";
  });

  attachButton.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;
    appendUserMessage(`📎 Attached: ${file.name}`);
    fileInput.value = "";
  });

  // -------------------------------
  // LOAD SIDEBAR + RESTORE CHAT
  // -------------------------------

  try {
    const response = await fetch("/conversations?user_id=default_user");
    const conversations = await response.json();

    // 🔑 CRITICAL FIX: Detect empty DB
    if (conversations.length === 0) {
      isFreshStart = true;
      localStorage.removeItem("conversation_id");
    }

    conversations.forEach(addConversationToSidebar);

    const lastConversationId = localStorage.getItem("conversation_id");
    if (lastConversationId) {
      openConversation(lastConversationId);
    }

  } catch (error) {
    console.error("Failed to restore conversations:", error);
  }

  // -------------------------------
  // + NEW CHAT
  // -------------------------------

  newChatButton.addEventListener("click", () => {

    clearChatWindow();
    localStorage.removeItem("conversation_id");

    const welcome = document.createElement("div");
    welcome.id = "welcome-message";
    welcome.className = "bot-message";
    welcome.textContent = "Start a new conversation 👋";

    chatMessages.appendChild(welcome);
  });

});

// ==================================================
// GLOBAL HELPERS (INTENTIONALLY OUTSIDE DOM READY)
// ==================================================

async function openConversation(conversationId) {

  localStorage.setItem("conversation_id", conversationId);

  const response = await fetch(`/chat/history/${conversationId}`);
  const messages = await response.json();

  clearChatWindow();

  messages.forEach(msg => {
    msg.role === "user"
      ? appendUserMessage(msg.message)
      : appendAssistantMessage(msg.message);
  });
}

function addConversationToSidebar(convo) {

  const chatHistory = document.getElementById("chat-history");

  // Prevent duplicates
  if ([...chatHistory.children].some(el => el.dataset.id === convo.conversation_id)) {
    return;
  }

  const item = document.createElement("div");
  item.className = "chat-history-item";
  item.dataset.id = convo.conversation_id;
  item.textContent = convo.title || "New Chat";

  item.addEventListener("click", () => {
    openConversation(convo.conversation_id);
  });

  // Newest on top (ChatGPT-like)
  chatHistory.prepend(item);
}

function clearChatWindow() {
  document.getElementById("chat-messages").innerHTML = "";
}

function appendUserMessage(text) {
  const chatMessages = document.getElementById("chat-messages");
  const msg = document.createElement("div");
  msg.className = "user-message";
  msg.textContent = text;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendAssistantMessage(text) {
  const chatMessages = document.getElementById("chat-messages");
  const msg = document.createElement("div");
  msg.className = "bot-message";
  msg.textContent = text;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
