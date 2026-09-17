const form = document.getElementById('chat-form');
const input = document.getElementById('message');
const messages = document.getElementById('messages');

function addMessage(text, role) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, 'user');
  input.value = '';

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    const data = await response.json();
    addMessage(data.reply || 'No response returned.', 'assistant');
  } catch (error) {
    addMessage('Something went wrong while contacting the server.', 'assistant');
    console.error(error);
  }
});

addMessage('Hi! Ask: “What should I work on today?” or “Do I have enough fabric for ORD-024?”', 'assistant');
