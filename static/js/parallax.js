document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('parallax-container');
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        const bg = container.querySelector('.parallax-bg');
        if (bg) {
            bg.style.transform = `translateY(${scrollY * 0.5}px)`;
        }
    });
});