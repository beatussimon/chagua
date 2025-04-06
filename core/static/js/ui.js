function toggleTheme() {
    document.body.classList.toggle('dark');
    const theme = document.body.classList.contains('dark') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
    fetch('/profile/' + document.body.dataset.username + '/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: `theme=${theme}`
    });
}

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('hidden');
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
}

function initMap(lat, lng, elementId) {
    const map = L.map(elementId).setView([lat || 0, lng || 0], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);
    L.marker([lat || 0, lng || 0]).addTo(map);
}

function pollComments(rentalId) {
    setInterval(() => {
        fetch(`/rental/${rentalId}/`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(response => response.json())
            .then(data => {
                const commentsDiv = document.getElementById('comments');
                if (commentsDiv) commentsDiv.innerHTML = data.comments.map(c => `<p>${c}</p>`).join('');
            });
    }, 5000);
}

function pollMessages(groupId = null) {
    setInterval(() => {
        const url = groupId ? `/messaging/group/${groupId}/` : '/messaging/';
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(response => response.json())
            .then(data => {
                const messagesDiv = document.getElementById('messages');
                if (messagesDiv) messagesDiv.innerHTML = data.messages.map(m => `<p>${m.sender}: ${m.content} (${m.timestamp})</p>`).join('');
            });
    }, 5000);
}

function initCalendar(rentalId) {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: `/rental/${rentalId}/`,
        selectable: true,
        select: function(info) {
            document.getElementById('start_date').value = info.startStr;
            document.getElementById('end_date').value = info.endStr;
        }
    });
    calendar.render();
}

function toggleMenu() {
    const menu = document.querySelector('.nav-menu');
    menu.classList.toggle('collapsed');
}

window.onload = () => {
    if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');
    document.querySelectorAll('.map').forEach(mapEl => {
        const lat = parseFloat(mapEl.dataset.lat);
        const lng = parseFloat(mapEl.dataset.lng);
        if (!isNaN(lat) && !isNaN(lng)) initMap(lat, lng, mapEl.id);
    });
    const rentalId = document.body.dataset.rentalId;
    if (rentalId) {
        pollComments(rentalId);
        initCalendar(rentalId);
    }
    const groupId = document.body.dataset.groupId;
    if (window.location.pathname.startsWith('/messaging/')) pollMessages(groupId);
    document.querySelector('.hamburger')?.addEventListener('click', toggleMenu);
};