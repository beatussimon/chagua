document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('theme-toggle');
    const sun = document.getElementById('sun-icon');
    const moon = document.getElementById('moon-icon');
    const html = document.documentElement;

    if (localStorage.theme === 'light') {
        html.classList.remove('dark');
        sun.classList.remove('hidden');
        moon.classList.add('hidden');
    } else {
        html.classList.add('dark');
        moon.classList.remove('hidden');
        sun.classList.add('hidden');
    }

    toggle.addEventListener('click', () => {
        if (html.classList.contains('dark')) {
            html.classList.remove('dark');
            localStorage.theme = 'light';
            sun.classList.remove('hidden');
            moon.classList.add('hidden');
        } else {
            html.classList.add('dark');
            localStorage.theme = 'dark';
            moon.classList.remove('hidden');
            sun.classList.add('hidden');
        }
    });
});