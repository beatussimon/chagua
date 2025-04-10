document.addEventListener('DOMContentLoaded', () => {
    const calendars = document.querySelectorAll('.calendar');
    calendars.forEach(calendar => {
        const availability = JSON.parse(calendar.dataset.availability || '{}');
        const today = new Date();
        const month = today.getMonth();
        const year = today.getFullYear();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        
        for (let i = 1; i <= daysInMonth; i++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            const dayDiv = document.createElement('div');
            dayDiv.textContent = i;
            dayDiv.classList.add('calendar-day');
            if (availability[dateStr] === 'booked') {
                dayDiv.classList.add('booked');
            } else {
                dayDiv.classList.add('available');
            }
            calendar.appendChild(dayDiv);
        }
    });
});