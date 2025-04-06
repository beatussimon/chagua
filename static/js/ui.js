// ui.js - God Level Final COMPLETE (Aligned + Collapsible Filter + inert Fix)

/**
 * Toggles theme between light/dark based on body class, saves to localStorage.
 */
function toggleTheme() {
    document.body.classList.toggle('dark');
    const theme = document.body.classList.contains('dark') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);

    // Optional: Persist explicit choice to backend
    const username = document.body.dataset.username;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (username && csrfToken) {
         fetch('/profile/update_theme/', {
             method: 'POST',
             headers: {'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken },
             body: `theme=${theme}`
         }).catch(error => console.error('Theme update error:', error));
    }
}

/**
 * Initializes the theme on page load based ONLY on localStorage.
 */
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    document.body.classList.remove('dark'); // Reset first
    if (savedTheme === 'dark') {
        document.body.classList.add('dark');
    }
}

/**
 * Toggles the full-screen hamburger menu visibility and interactivity.
 */
function toggleMenu() {
    const menu = document.getElementById('hamburger-menu');
    const toggleButton = document.getElementById('hamburger-toggle');
    if (menu && toggleButton) {
        const isOpen = menu.classList.toggle('open');
        if (isOpen) {
            menu.removeAttribute('inert');
            toggleButton.setAttribute('aria-expanded', 'true');
            setTimeout(() => { document.getElementById('close-hamburger')?.focus(); }, 300);
        } else {
            menu.setAttribute('inert', 'true');
            toggleButton.setAttribute('aria-expanded', 'false');
            toggleButton.focus();
        }
    }
}

/** Shows a modal dialog, managing inert and focus */
function showModal(id) {
    const modal = document.getElementById(id);
    const elementsToInert = ['header.navbar', '.secondary-nav', 'main', 'footer'];
    if (modal) {
        modal.classList.remove('hidden');
        modal.removeAttribute('inert');
        modal.setAttribute('aria-modal', 'true'); modal.setAttribute('role', 'dialog');
        elementsToInert.forEach(selector => { document.querySelector(selector)?.setAttribute('inert', true); });
        const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable) setTimeout(() => focusable.focus(), 50);
        modal.triggeredBy = document.activeElement;
    }
}

/** Hides a modal dialog, restoring inert and focus */
function hideModal(id) {
    const modal = document.getElementById(id);
    const elementsToInert = ['header.navbar', '.secondary-nav', 'main', 'footer'];
    if (modal) {
        modal.classList.add('hidden');
        modal.setAttribute('inert', 'true');
        modal.removeAttribute('aria-modal'); modal.removeAttribute('role');
        elementsToInert.forEach(selector => { document.querySelector(selector)?.removeAttribute('inert'); });
        if (modal.triggeredBy?.focus) { modal.triggeredBy.focus(); modal.triggeredBy = null; }
    }
}

/** Initializes a Leaflet map. */
function initMap(lat, lng, elementId) {
    if (typeof L === 'undefined') { console.error("Leaflet not loaded."); return; }
    try {
        const mapContainer = L.DomUtil.get(elementId);
        if(mapContainer?._leaflet_id) { return; }
        const map = L.map(elementId).setView([lat ?? 51.505, lng ?? -0.09], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
        if (lat != null && lng != null) { L.marker([lat, lng]).addTo(map); }
    } catch (e) { console.error(`Map init error ${elementId}:`, e); }
}

/**
 * Toggles the visibility of the filter section with smooth animation.
 */
function toggleFilters() {
    const filterSection = document.getElementById('filter-section');
    const toggleButton = document.getElementById('filter-toggle-button');
    const arrowDown = document.getElementById('filter-arrow-down');
    const arrowUp = document.getElementById('filter-arrow-up');

    if (filterSection && toggleButton) {
        const isOpen = filterSection.dataset.open === 'true';

        if (isOpen) {
            // Closing
            filterSection.style.maxHeight = '0px';
            filterSection.dataset.open = 'false';
            toggleButton.setAttribute('aria-expanded', 'false');
            if (arrowDown) arrowDown.classList.remove('hidden');
            if (arrowUp) arrowUp.classList.add('hidden');
            // Set inert after collapsing (optional)
            // setTimeout(() => filterSection.setAttribute('inert', 'true'), 400);
        } else {
            // Opening
            filterSection.classList.remove('hidden'); // Ensure display is not none
            filterSection.removeAttribute('inert');
            filterSection.style.maxHeight = filterSection.scrollHeight + "px";
            filterSection.dataset.open = 'true';
            toggleButton.setAttribute('aria-expanded', 'true');
            if (arrowDown) arrowDown.classList.add('hidden');
            if (arrowUp) arrowUp.classList.remove('hidden');
        }
    }
}


// --- Initialization on DOMContentLoaded ---
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme(); // Set initial theme

    // Hamburger listeners
    document.getElementById('hamburger-toggle')?.addEventListener('click', toggleMenu);
    document.getElementById('close-hamburger')?.addEventListener('click', toggleMenu);

    // Filter toggle listener
    document.getElementById('filter-toggle-button')?.addEventListener('click', toggleFilters);

    // Tooltip initialization
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        let tooltipElement = null;
        const showTooltip = () => {
            if (tooltipElement) return;
            tooltipElement = document.createElement('div');
            tooltipElement.className = 'absolute bg-gray-900 dark:bg-gray-700 text-white dark:text-gray-200 text-xs px-2 py-1 rounded shadow-lg z-50 whitespace-nowrap pointer-events-none';
            tooltipElement.textContent = el.dataset.tooltip || '';
            tooltipElement.setAttribute('role', 'tooltip');
            tooltipElement.id = `tooltip-${Math.random().toString(36).substring(7)}`;
            el.setAttribute('aria-describedby', tooltipElement.id);
            document.body.appendChild(tooltipElement);
            const rect = el.getBoundingClientRect();
            tooltipElement.style.left = `${rect.left + window.scrollX + rect.width / 2 - tooltipElement.offsetWidth / 2}px`;
            tooltipElement.style.top = `${rect.top + window.scrollY - tooltipElement.offsetHeight - 8}px`;
            tooltipElement.style.opacity = '0'; requestAnimationFrame(() => { tooltipElement.style.opacity = '1'; });
        };
        const hideTooltip = () => { if (tooltipElement) { tooltipElement.remove(); tooltipElement = null; el.removeAttribute('aria-describedby'); } };
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

    // Escape key listener
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const openModal = document.querySelector('[role="dialog"]:not(.hidden):not([inert])');
            if (openModal) hideModal(openModal.id);
            else { const menu = document.getElementById('hamburger-menu'); if (menu?.classList.contains('open')) toggleMenu(); }
        }
    });

    // Add polling/calendar calls here if backend is ready
    // ...
});