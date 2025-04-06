// ui.js - Final Final Final (Aligned with User's OG CSS & JS)

/**
 * Toggles theme between light/dark based on body class, saves to localStorage.
 * Based on user's provided function structure.
 */
function toggleTheme() {
    document.body.classList.toggle('dark');
    const theme = document.body.classList.contains('dark') ? 'dark' : 'light';
    localStorage.setItem('theme', theme); // Save the resulting theme state

    // Optional: Persist explicit choice to backend (if needed)
    // const username = document.body.dataset.username;
    // const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    // if (username && csrfToken) { fetch(...) }
}

/**
 * Initializes the theme on page load based *only* on localStorage.
 * (Removed system detection and backend check to strictly follow user's JS)
 */
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme'); // Only check localStorage
    if (savedTheme === 'dark') {
        document.body.classList.add('dark');
    } else {
        document.body.classList.remove('dark'); // Default to light if not 'dark'
    }
    // Note: No 'auto' logic here, strictly follows user's original JS intent.
    // The theme <select> dropdowns were removed from HTML as they don't fit this simple toggle.
}

/**
 * Toggles the visibility of the full-screen mobile menu.
 * Uses the #hamburger-menu and .open class logic for the overlay effect.
 */
function toggleMenu() { // This function manages the full-screen menu
    const menu = document.getElementById('hamburger-menu');
    const toggleButton = document.getElementById('hamburger-toggle');
    if (menu && toggleButton) {
        const isOpen = menu.classList.toggle('open');
        // Add aria attributes for accessibility
        toggleButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        menu.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
    }
}

/**
 * Shows a modal dialog. (User's function)
 */
function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('hidden'); // Assuming Tailwind's hidden class
        modal.setAttribute('aria-hidden', 'false');
        // Focus management for accessibility
        const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable) focusable.focus();
    }
}

/**
 * Hides a modal dialog. (User's function)
 */
function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('hidden'); // Assuming Tailwind's hidden class
        modal.setAttribute('aria-hidden', 'true');
    }
}

/**
 * Initializes a Leaflet map. (User's function)
 */
function initMap(lat, lng, elementId) {
    if (typeof L === 'undefined') { console.error("Leaflet not loaded."); return; }
    try {
        const mapContainer = L.DomUtil.get(elementId);
        if(mapContainer != null && mapContainer._leaflet_id != null) { mapContainer._leaflet_id = null; }
        const map = L.map(elementId).setView([lat || 0, lng || 0], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        L.marker([lat || 0, lng || 0]).addTo(map);
    } catch (e) { console.error(`Error initializing map ${elementId}:`, e); }
}

// --- Initialization on DOMContentLoaded ---
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme(); // Set initial theme based on localStorage

    // Hamburger menu listeners
    document.getElementById('hamburger-toggle')?.addEventListener('click', toggleMenu);
    document.getElementById('close-hamburger')?.addEventListener('click', toggleMenu);

    // Tooltip initialization (Re-added)
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        let tooltipElement = null;
        const showTooltip = () => {
             if (tooltipElement) return;
             tooltipElement = document.createElement('div');
             tooltipElement.className = 'absolute bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg z-50 whitespace-nowrap';
             tooltipElement.textContent = el.dataset.tooltip || '';
             tooltipElement.setAttribute('role', 'tooltip');
             document.body.appendChild(tooltipElement);
             const rect = el.getBoundingClientRect();
             tooltipElement.style.left = `${rect.left + window.scrollX + rect.width / 2 - tooltipElement.offsetWidth / 2}px`;
             tooltipElement.style.top = `${rect.top + window.scrollY - tooltipElement.offsetHeight - 8}px`;
             tooltipElement.style.opacity = '0'; requestAnimationFrame(() => { tooltipElement.style.opacity = '1'; });
         };
         const hideTooltip = () => { if (tooltipElement) { tooltipElement.remove(); tooltipElement = null; } };
         el.addEventListener('mouseenter', showTooltip);
         el.addEventListener('mouseleave', hideTooltip);
         el.addEventListener('focus', showTooltip);
         el.addEventListener('blur', hideTooltip);
    });

    // Map initialization
    document.querySelectorAll('.map').forEach(mapEl => {
        const lat = parseFloat(mapEl.dataset.lat);
        const lng = parseFloat(mapEl.dataset.lng);
        if (!isNaN(lat) && !isNaN(lng)) initMap(lat, lng, mapEl.id);
    });

    // Close modals/menu on Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelectorAll('[id^="media-modal-"], [id^="reply-"]').forEach(modal => {
                if (!modal.classList.contains('hidden')) hideModal(modal.id);
            });
            const hamburgerMenu = document.getElementById('hamburger-menu');
            if (hamburgerMenu && hamburgerMenu.classList.contains('open')) toggleMenu();
        }
    });

    // Add user's polling/calendar init logic here if needed
    // const rentalId = document.body.dataset.rentalId;
    // if (rentalId) { pollComments(rentalId); initCalendar(rentalId); }
    // const groupId = document.body.dataset.groupId;
    // if (window.location.pathname.startsWith('/messaging/')) pollMessages(groupId);
});