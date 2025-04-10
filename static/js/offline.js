if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js').then(reg => {
            console.log('Service Worker registered:', reg);
        }).catch(err => {
            console.error('Service Worker registration failed:', err);
        });
    });
}