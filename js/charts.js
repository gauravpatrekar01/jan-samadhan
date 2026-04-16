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
    if (!el) return null;
    
    // Destroy previous chart before rendering
    const existingChart = Chart.getChart(id);
    if (existingChart) existingChart.destroy();
    
    // Log grievances before processing
    console.log('[renderTimelineChart] grievances:', grievances);
    
    grievances = grievances || [];
    const dateCounts = {};
    
    // Group data correctly
    grievances.forEach(g => {
        // Use ONLY g.createdAt
        if (!g.createdAt) return;
        
        // Convert using new Date
        const d = new Date(g.createdAt);
        // If invalid -> skip entry
        if (isNaN(d.getTime())) return;
        
        // Extract date in YYYY-MM-DD format
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        const dateStr = `${yyyy}-${mm}-${dd}`;
        
        // Count complaints per day
        if (dateCounts[dateStr] === undefined) {
            dateCounts[dateStr] = 0;
        }
        dateCounts[dateStr]++;
    });

    // Ensure chart gets valid data
    let labels = Object.keys(dateCounts);
    let data = Object.values(dateCounts);
    
    // If no valid data -> show fallback
    if (labels.length === 0) {
        labels = ['No Data'];
        data = [0];
    } else {
        // Sort dates chronologically natively and limit to last 14 if massive
        const sortedDates = labels.sort((a, b) => new Date(a) - new Date(b));
        labels = sortedDates.slice(-14);
        data = labels.map(l => dateCounts[l]);
    }
    
    // Log processed metrics
    console.log('[renderTimelineChart] dateCounts:', dateCounts);
    console.log('[renderTimelineChart] labels:', labels);
    console.log('[renderTimelineChart] data:', data);

    // Improve UI & Render
    return new Chart(el, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Complaints',
                data: data,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37,99,235,0.15)',
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#2563eb',
                pointBorderColor: '#fff',
                pointHoverRadius: 6,
                pointRadius: 4
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            layout: { padding: { top: 10, right: 10, left: 0, bottom: 0 } },
            scales: {
                y: { 
                    beginAtZero: true, 
                    ticks: { font: { size: 11 }, stepSize: 1, padding: 8 } 
                },
                x: { 
                    ticks: { font: { size: 10 }, maxRotation: 45, minRotation: 0 } 
                }
            },
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleFont: { size: 12 },
                    bodyFont: { size: 13 },
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.raw} complaints`;
                        }
                    }
                }
            }
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
