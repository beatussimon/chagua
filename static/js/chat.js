document.addEventListener('DOMContentLoaded', () => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/chat/`);
    ws.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const messages = document.getElementById('chat-messages');
        messages.innerHTML += `
            <div class="text-left">
                <p class="inline-block p-3 rounded-lg bg-gray-200 dark:bg-gray-600 dark:text-gray-200 shadow-sm">${data.message.content}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">${new Date(data.message.timestamp).toLocaleString()}</p>
            </div>`;
        messages.scrollTop = messages.scrollHeight;
    };
    ws.onclose = function() {
        console.error('Chat WebSocket closed unexpectedly');
    };
});