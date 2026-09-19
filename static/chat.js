(function () {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('message');
  const messages = document.getElementById('messages');
  const toggle = document.getElementById('chat-toggle');
  const drawer = document.getElementById('chat-drawer');

  function addMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  toggle.addEventListener('click', () => {
    drawer.hidden = !drawer.hidden;
  });

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
        body: JSON.stringify({ message: text }),
      });

      const data = await response.json();
      addMessage(data.reply || 'No response returned.', 'assistant');

      // Whatever the agent just did (schedule, adjust stock, add an order...)
      // should show up on the calendar/strip immediately, not just as text.
      if (window.refreshCalendar) window.refreshCalendar();
      if (window.refreshInventory) window.refreshInventory();
      if (window.refreshPendingBadge) window.refreshPendingBadge();
    } catch (error) {
      addMessage('Something went wrong while contacting the server.', 'assistant');
      console.error(error);
    }
  });

  addMessage(
    "Hi! Ask me to check fabric, plan today, or add a commitment — I'll update the calendar and inventory directly.",
    'assistant'
  );
})();
