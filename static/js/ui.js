function toggleTheme() {
    document.body.classList.toggle('dark');
    localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
}

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('hidden');
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('hidden');
}

function filterMessages(filter) {
    console.log(`Filtering by: ${filter}`);
    // Placeholder for future client-side filtering if needed
}

window.onload = () => {
    if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.addEventListener('mouseover', () => {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute bg-gray-800 text-white p-2 rounded text-sm shadow-lg z-10';
            tooltip.innerText = el.dataset.tooltip || 'No tooltip'; // Fallback for missing data-tooltip
            document.body.appendChild(tooltip);
            const rect = el.getBoundingClientRect();
            tooltip.style.top = `${rect.top - 40}px`;
            tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
        });
        el.addEventListener('mouseout', () => {
            document.querySelectorAll('.absolute').forEach(t => t.remove());
        });
    });
};