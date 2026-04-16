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
        options: { 
            maintainAspectRatio: false, 
            responsive: true,
            cutout: '70%', 
            plugins: { 
                legend: { 
                    position: 'bottom', 
                    labels: { 
                        boxWidth: 12, 
                        font: { size: 10 },
                        padding: 15
                    } 
                } 
            },
            // Enhanced responsive behavior
            onResize: (chart, size) => {
                if (size.width < 400) {
                    chart.options.plugins.legend.labels.font.size = 8;
                    chart.options.cutout = '60%';
                } else if (size.width > 600) {
                    chart.options.plugins.legend.labels.font.size = 12;
                    chart.options.cutout = '70%';
                }
            }
        }
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
        options: { 
            maintainAspectRatio: false, 
            responsive: true,
            scales: { 
                y: { 
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                }
            }, 
            plugins: { 
                legend: { 
                    display: false 
                } 
            },
            // Enhanced responsive behavior
            onResize: (chart, size) => {
                if (size.width < 400) {
                    chart.options.scales.y.ticks.font.size = 8;
                    chart.options.scales.x.ticks.font.size = 8;
                } else if (size.width > 600) {
                    chart.options.scales.y.ticks.font.size = 12;
                    chart.options.scales.x.ticks.font.size = 12;
                }
            }
        }
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
        options: { 
            maintainAspectRatio: false, 
            responsive: true,
            plugins: { 
                legend: { 
                    position: 'bottom', 
                    labels: { 
                        boxWidth: 12, 
                        font: { size: 10 },
                        padding: 15
                    } 
                } 
            },
            // Enhanced responsive behavior
            onResize: (chart, size) => {
                if (size.width < 400) {
                    chart.options.plugins.legend.labels.font.size = 8;
                } else if (size.width > 600) {
                    chart.options.plugins.legend.labels.font.size = 12;
                }
            }
        }
    });
}

function renderTimelineChart(id, grievances) {
    const el = document.getElementById(id);
    if (!el || !grievances || !grievances.length) return null;
    
    // Group grievances by date
    const dateCounts = {};
    grievances.forEach(g => {
        const d = new Date(g.createdAt || g.created_at || g.timestamp || Date.now());
        const dateStr = d.toISOString().split('T')[0];
        dateCounts[dateStr] = (dateCounts[dateStr] || 0) + 1;
    });

    const sortedDates = Object.keys(dateCounts).sort((a,b) => new Date(a) - new Date(b));
    const displayDates = sortedDates.slice(-14);
    const dataPoints = displayDates.map(d => dateCounts[d]);
    const formattedLabels = displayDates.map(d => new Date(d).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }));

    return new Chart(el, {
        type: 'line',
        data: {
            labels: formattedLabels.length ? formattedLabels : ['Today'],
            datasets: [{
                label: 'Complaints',
                data: dataPoints.length ? dataPoints : [0],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37,99,235,0.1)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#2563eb',
                pointRadius: 4
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            scales: {
                y: { beginAtZero: true, ticks: { font: { size: 10 }, stepSize: 1 } },
                x: { ticks: { font: { size: 10 } } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// Global hook for admin panel charting
async function initCharts() {
    let stats = { priority_distribution:{}, status_distribution:{}, byCategory:{} };
    let allG = [];
    try {
        stats = await window.JanSamadhanAPI.getAdminAnalytics();
        
        // Count categories because admin analytics doesn't return categories directly yet
        allG = await window.JanSamadhanAPI.getAllGrievances();
        const cats = {};
        for(let g of allG) {
           cats[g.category] = (cats[g.category] || 0) + 1;
        }
        stats.byCategory = cats;
    } catch(e) {
        console.warn("Failed admin analytics, fallback to public", e);
        try { stats = await window.JanSamadhanAPI.getAnalytics(); } catch(err) {}
    }
    
    if (window._adminCharts && window._adminCharts.cat) window._adminCharts.cat.destroy();
    if (window._adminCharts && window._adminCharts.pri) window._adminCharts.pri.destroy();
    if (window._adminCharts && window._adminCharts.sta) window._adminCharts.sta.destroy();
    if (window._adminCharts && window._adminCharts.timeline) window._adminCharts.timeline.destroy();
    window._adminCharts = {};
    
    // For admin.html canvases
    if (document.getElementById('adminCatPie')) window._adminCharts.cat = renderCategoryPie('adminCatPie', stats);
    if (document.getElementById('adminCatBar')) window._adminCharts.catBar = renderCategoryPie('adminCatBar', stats); // reuse
    if (document.getElementById('adminPriorityPie')) window._adminCharts.pri = renderPriorityBar('adminPriorityPie', stats);
    if (document.getElementById('adminTimeline')) window._adminCharts.timeline = renderTimelineChart('adminTimeline', allG);
    // offCatPie, offPriorityBar, offStatusPie is handled directly by officer.html
}
