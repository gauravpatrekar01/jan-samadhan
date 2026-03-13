// Chart.js helper functions for the dashboard
// The map renderer has been moved to app.js for broader availability.

function renderCategoryPie(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    return new Chart(el, {
        type: 'doughnut',
        data: {
            labels: ['Infrastructure', 'Water Supply', 'Electricity', 'Sanitation', 'Other'],
            datasets: [{
                data: [4, 3, 2, 2, 1],
                backgroundColor: ['#3b82f6', '#0ea5e9', '#eab308', '#8b5cf6', '#64748b'],
                borderWidth: 0
            }]
        },
        options: { cutout: '70%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } } }
    });
}

function renderPriorityBar(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    return new Chart(el, {
        type: 'bar',
        data: {
            labels: ['Emergency', 'High', 'Medium', 'Low'],
            datasets: [{
                label: 'Complaints',
                data: [2, 3, 5, 2],
                backgroundColor: ['#7f1d1d', '#dc2626', '#d97706', '#16a34a']
            }]
        },
        options: { scales: { y: { beginAtZero: true } }, plugins: { legend: { display: false } } }
    });
}

function renderStatusPie(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    return new Chart(el, {
        type: 'pie',
        data: {
            labels: ['Submitted', 'In Progress', 'Resolved'],
            datasets: [{
                data: [4, 3, 5],
                backgroundColor: ['#64748b', '#3b82f6', '#16a34a']
            }]
        },
        options: { plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } } }
    } );
}
