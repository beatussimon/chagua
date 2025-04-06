// ui.js - God Level Final Complete (Aligned with OG CSS & Professional Menu + inert fix)

/**
 * Toggles theme between light/dark based on body class, saves to localStorage.
 */
function toggleTheme() {
    document.body.classList.toggle('dark');
    const theme = document.body.classList.contains('dark') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);

    // Persist explicit choice ('light' or 'dark') to the backend
    const username = document.body.dataset.username;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    // Only send if logged in and token exists
    if (username && csrfToken) {
         fetch('/profile/update_theme/', { // Ensure this URL is correct in core/urls.py
             method: 'POST',
             headers: {
                 'Content-Type': 'application/x-www-form-urlencoded',
                 'X-CSRFToken': csrfToken
             },
             body: `theme=${theme}` // Send 'light' or 'dark'
         }).catch(error => console.error('Error updating theme preference:', error));
    }
}

/**
 * Initializes the theme on page load based ONLY on localStorage.
 */
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    // Ensure clean state before applying saved theme
    document.body.classList.remove('dark');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark');
    }
    // NOTE: Removed 'auto' detection logic as per last user request.
}

/**
 * Toggles the full-screen hamburger menu visibility and interactivity.
 * Uses the 'open' class for visual transition and 'inert' attribute.
 */
function toggleMenu() {
    const menu = document.getElementById('hamburger-menu');
    const toggleButton = document.getElementById('hamburger-toggle');

    if (!menu || !toggleButton) {
        console.error("Hamburger menu or toggle button not found.");
        return;
    }

    const isOpen = menu.classList.toggle('open');

    if (isOpen) {
        menu.removeAttribute('inert');
        toggleButton.setAttribute('aria-expanded', 'true');
        // Focus the close button inside menu for accessibility after transition
        setTimeout(() => {
            document.getElementById('close-hamburger')?.focus();
        }, 300); // Match transition duration
    } else {
        menu.setAttribute('inert', 'true');
        toggleButton.setAttribute('aria-expanded', 'false');
        // Return focus to the hamburger button after closing
        toggleButton.focus();
    }
}


/** Shows a modal dialog, managing inert and focus */
function showModal(id) {
    const modal = document.getElementById(id);
    // Select main content areas to make inert
    const elementsToInert = ['header.navbar', '.secondary-nav', 'main', 'footer'];

    if (modal) {
        modal.classList.remove('hidden');
        modal.removeAttribute('inert');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('role', 'dialog');

        elementsToInert.forEach(selector => {
            document.querySelector(selector)?.setAttribute('inert', 'true');
        });

        // Focus management: focus first focusable element inside modal
        const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable) {
            setTimeout(() => focusable.focus(), 50); // Slight delay
        }

        // Store the element that triggered the modal
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
        modal.removeAttribute('aria-modal');
        modal.removeAttribute('role');

        // Make background interactive again
        elementsToInert.forEach(selector => {
            document.querySelector(selector)?.removeAttribute('inert');
        });

        // Return focus to the trigger, check if exists and is focusable
        if (modal.triggeredBy && typeof modal.triggeredBy.focus === 'function') {
            modal.triggeredBy.focus();
            modal.triggeredBy = null; // Clear reference
        }
    }
}

/** Initializes a Leaflet map. */
function initMap(lat, lng, elementId) {
    if (typeof L === 'undefined') { console.error("Leaflet library not loaded."); return; }
    try {
        const mapContainer = L.DomUtil.get(elementId);
        if(mapContainer?._leaflet_id) { return; } // Don't re-initialize if already done

        const map = L.map(elementId).setView([lat ?? 51.505, lng ?? -0.09], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        if (lat != null && lng != null) { L.marker([lat, lng]).addTo(map); }
    } catch (e) { console.error(`Map init error ${elementId}:`, e); }
}


// --- Initialization on DOMContentLoaded ---
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme(); // Set initial theme based on localStorage

    // Hamburger menu listeners
    document.getElementById('hamburger-toggle')?.addEventListener('click', toggleMenu);
    document.getElementById('close-hamburger')?.addEventListener('click', toggleMenu);

    // Tooltip initialization
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        let tooltipElement = null;
        const showTooltip = () => {
             if (tooltipElement) return;
             tooltipElement = document.createElement('div');
             tooltipElement.className = 'absolute bg-gray-900 dark:bg-gray-700 text-white dark:text-gray-200 text-xs px-2 py-1 rounded shadow-lg z-50 whitespace-nowrap pointer-events-none'; // Added pointer-events-none
             tooltipElement.textContent = el.dataset.tooltip || '';
             tooltipElement.setAttribute('role', 'tooltip');
             tooltipElement.id = `tooltip-${Math.random().toString(36).substring(7)}`; // Unique ID for aria
             el.setAttribute('aria-describedby', tooltipElement.id);
             document.body.appendChild(tooltipElement);
             const rect = el.getBoundingClientRect();
             tooltipElement.style.left = `${rect.left + window.scrollX + rect.width / 2 - tooltipElement.offsetWidth / 2}px`;
             tooltipElement.style.top = `${rect.top + window.scrollY - tooltipElement.offsetHeight - 8}px`; // 8px spacing
             tooltipElement.style.opacity = '0';
             requestAnimationFrame(() => { tooltipElement.style.opacity = '1'; });
         };
         const hideTooltip = () => {
             if (tooltipElement) {
                 tooltipElement.remove();
                 tooltipElement = null;
                 el.removeAttribute('aria-describedby');
             }
         };
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
            const openModal = document.querySelector('[role="dialog"]:not(.hidden):not([inert])');
            if (openModal) {
                hideModal(openModal.id);
            } else {
                 const hamburgerMenu = document.getElementById('hamburger-menu');
                 if (hamburgerMenu?.classList.contains('open')) {
                     toggleMenu();
                 }
            }
        }
    });

    // Add polling/calendar calls here if backend is ready
    // e.g., const rentalIdElement = document.querySelector('[data-rental-id]');
    // if (rentalIdElement) initCalendar(rentalIdElement.dataset.rentalId);
});