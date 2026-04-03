// Chart.js helper functions for the dashboard

function getChartStats(stats) {
    if (!stats) return null;
    return {
        catLabels: Object.keys(stats.byCategory || {}),
        catData: Object.values(stats.byCategory || {}),
        priData: [
            stats.priority_distribution?.emergency || 0,
            stats.priority_distribution?.high || 0,
            stats.priority_distribution?.medium || 0,
            stats.priority_distribution?.low || 0
        ],
        staData: [
            stats.status_distribution?.submitted || 0,
            stats.status_distribution?.in_progress || 0,
            stats.status_distribution?.resolved || 0
        ]
    };
}

function renderCategoryPie(id, stats) {
    const el = document.getElementById(id);
    if (!el || !stats) return null;
    let data = getChartStats(stats);
    return new Chart(el, {
        type: 'doughnut',
        data: {
            labels: data.catLabels.length ? data.catLabels : ['Infrastructure', 'Water Supply', 'Electricity', 'Sanitation', 'Other'],
            datasets: [{
                data: data.catData.length ? data.catData : [1, 1, 1, 1, 1], // fallback visually if empty
                backgroundColor: ['#3b82f6', '#0ea5e9', '#eab308', '#8b5cf6', '#64748b', '#f43f5e', '#10b981'],
                borderWidth: 0
            }]
        },
        options: { cutout: '70%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } } }
    });
}

function renderPriorityBar(id, stats) {
    const el = document.getElementById(id);
    if (!el || !stats) return null;
    let data = getChartStats(stats);
    return new Chart(el, {
        type: 'bar',
        data: {
            labels: ['Emergency', 'High', 'Medium', 'Low'],
            datasets: [{
                label: 'Complaints',
                data: data.priData,
                backgroundColor: ['#7f1d1d', '#dc2626', '#d97706', '#16a34a']
            }]
        },
        options: { scales: { y: { beginAtZero: true } }, plugins: { legend: { display: false } } }
    });
}

function renderStatusPie(id, stats) {
    const el = document.getElementById(id);
    if (!el || !stats) return null;
    let data = getChartStats(stats);
    return new Chart(el, {
        type: 'pie',
        data: {
            labels: ['Submitted', 'In Progress', 'Resolved'],
            datasets: [{
                data: data.staData,
                backgroundColor: ['#64748b', '#3b82f6', '#16a34a']
            }]
        },
        options: { plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } } } }
    });
}

// Global hook for admin panel charting
async function initCharts() {
    let stats = { priority_distribution:{}, status_distribution:{}, byCategory:{} };
    try {
        stats = await window.JanSamadhanAPI.getAnalytics();
        
        // Count categories because admin analytics doesn't return categories directly yet
        const allG = await window.JanSamadhanAPI.getAllGrievances();
        const cats = {};
        for(let g of allG) {
           cats[g.category] = (cats[g.category] || 0) + 1;
        }
        stats.byCategory = cats;
    } catch(e) {}
    
    if (window._adminCharts && window._adminCharts.cat) window._adminCharts.cat.destroy();
    if (window._adminCharts && window._adminCharts.pri) window._adminCharts.pri.destroy();
    if (window._adminCharts && window._adminCharts.sta) window._adminCharts.sta.destroy();
    window._adminCharts = {};
    
    // For admin.html canvases
    if (document.getElementById('adminCatPie')) window._adminCharts.cat = renderCategoryPie('adminCatPie', stats);
    if (document.getElementById('adminCatBar')) window._adminCharts.catBar = renderCategoryPie('adminCatBar', stats); // reuse
    if (document.getElementById('adminPriorityPie')) window._adminCharts.pri = renderPriorityBar('adminPriorityPie', stats);
    // offCatPie, offPriorityBar, offStatusPie is handled directly by officer.html
}
