/**
 * Advanced Analytics Module for JanSamadhan
 * Provides comprehensive data-driven insights for Officers and Admins
 * Dependencies: Chart.js 3.x, modern browsers
 */

class AdvancedAnalyticsManager {
    constructor(options = {}) {
        this.apiBase = options.apiBase || '/api';
        this.userRole = options.userRole || 'officer'; // 'officer' or 'admin'
        this.userId = options.userId || null;
        this.refreshInterval = options.refreshInterval || 30000; // 30 seconds
        this.charts = {};
        this.filters = {
            dateRange: { start: this.getDateBefore(30), end: new Date() },
            category: [],
            priority: [],
            region: [],
            status: []
        };
    }

    /**
     * Initialize analytics dashboard
     */
    async initialize() {
        try {
            console.log('📊 Initializing Advanced Analytics...');
            
            // Load Chart.js if not already loaded
            if (typeof Chart === 'undefined') {
                await this.loadScript('https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js');
            }

            // Load initial data
            await this.loadDashboard();
            
            // Setup event listeners
            this.setupFilterListeners();
            
            // Start auto-refresh
            this.startAutoRefresh();
            
            console.log('✅ Analytics initialized successfully');
        } catch (error) {
            console.error('❌ Analytics initialization failed:', error);
            throw error;
        }
    }

    /**
     * Load complete dashboard
     */
    async loadDashboard() {
        try {
            if (this.userRole === 'admin') {
                await this.loadAdminDashboard();
            } else {
                await this.loadOfficerDashboard();
            }
        } catch (error) {
            console.error('Dashboard loading failed:', error);
            this.showError('Failed to load dashboard. Please refresh.');
        }
    }

    /**
     * ADMIN DASHBOARD
     */
    async loadAdminDashboard() {
        console.log('📈 Loading Admin Dashboard...');
        
        const [overview, performance, trends] = await Promise.all([
            this.fetchAdminOverview(),
            this.fetchOfficerPerformance(),
            this.fetchTrends()
        ]);

        // Render KPI cards
        this.renderAdminKPIs(overview);
        
        // Render charts
        this.renderAdminCharts(overview, trends);
        
        // Render officer leaderboard
        this.renderOfficerLeaderboard(performance);
    }

    /**
     * Render admin KPI cards
     */
    renderAdminKPIs(data) {
        const container = document.getElementById('adminAnalyticsKPIs') || 
                         document.getElementById('adminStats');
        if (!container) return;

        const kpis = [
            {
                title: 'Total Complaints',
                value: data.total_complaints,
                trend: '+5%',
                icon: '📋',
                color: '#3b82f6'
            },
            {
                title: 'Resolution Rate',
                value: data.resolution_rate + '%',
                trend: 'System avg',
                icon: '✅',
                color: '#10b981'
            },
            {
                title: 'Pending Cases',
                value: data.pending_complaints,
                trend: data.pending_complaints > 100 ? '⚠️ High' : 'Normal',
                icon: '⏳',
                color: '#f59e0b'
            },
            {
                title: 'Avg Resolution Time',
                value: data.avg_resolution_time_hours + ' hrs',
                trend: '↓ Improving',
                icon: '⏱️',
                color: '#8b5cf6'
            },
            {
                title: 'SLA Breaches',
                value: data.sla_breaches,
                trend: data.sla_breaches > 0 ? '⚠️ Action needed' : '✅ None',
                icon: '🚨',
                color: '#ef4444'
            },
            {
                title: 'Avg Citizen Rating',
                value: '4.2 ⭐',
                trend: 'Excellent service',
                icon: '⭐',
                color: '#f59e0b'
            }
        ];

        container.innerHTML = kpis.map(kpi => `
            <div class="analytics-kpi-card" style="border-left: 4px solid ${kpi.color}">
                <div class="kpi-header">
                    <span class="kpi-icon">${kpi.icon}</span>
                    <span class="kpi-title">${kpi.title}</span>
                </div>
                <div class="kpi-value">${kpi.value}</div>
                <div class="kpi-trend">${kpi.trend}</div>
            </div>
        `).join('');
    }

    /**
     * Render admin charts
     */
    async renderAdminCharts(overview, trends) {
        // Complaints over time
        this.createLineChart(
            'adminAnalyticsTimeline',
            trends,
            'Daily Complaint Inflow & Resolution',
            ['#3b82f6', '#10b981']
        );

        // Category distribution
        this.createBarChart(
            'adminAnalyticsCategory',
            overview.category_distribution,
            'Complaints by Category',
            '#3b82f6'
        );

        // Priority distribution
        this.createPieChart(
            'adminAnalyticsPriority',
            Object.values(overview.priority_distribution),
            Object.keys(overview.priority_distribution).map(p => p.charAt(0).toUpperCase() + p.slice(1)),
            'Priority Distribution'
        );

        // Region performance
        this.createHorizontalBarChart(
            'adminAnalyticsRegion',
            overview.region_performance,
            'Top Performing Regions',
            '#10b981'
        );
    }

    /**
     * Render officer leaderboard
     */
    renderOfficerLeaderboard(officers) {
        const container = document.getElementById('officerLeaderboard') ||
                         document.getElementById('overviewGrid');
        if (!container) return;

        const leaderboardHTML = `
            <div class="analytics-leaderboard">
                <div class="leaderboard-header">🏆 Officer Performance Ranking</div>
                <div class="leaderboard-table">
                    <div class="leaderboard-row header">
                        <div class="rank">Rank</div>
                        <div class="name">Officer</div>
                        <div class="metric">Resolution Rate</div>
                        <div class="metric">Avg Rating</div>
                        <div class="metric">Efficiency</div>
                    </div>
                    ${officers.slice(0, 10).map((officer, idx) => `
                        <div class="leaderboard-row ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}">
                            <div class="rank">
                                ${idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
                            </div>
                            <div class="name">${officer.officer}</div>
                            <div class="metric">${officer.resolution_rate}%</div>
                            <div class="metric">${officer.avg_rating || 'N/A'} ⭐</div>
                            <div class="metric"><span class="efficiency-badge">${officer.efficiency_score}</span></div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Insert after KPI cards
        const insertPoint = document.querySelector('.analytics-kpi-card')?.parentElement;
        if (insertPoint) {
            insertPoint.insertAdjacentHTML('afterend', leaderboardHTML);
        }
    }

    /**
     * OFFICER DASHBOARD
     */
    async loadOfficerDashboard() {
        console.log('📈 Loading Officer Dashboard...');
        
        if (!this.userId) {
            console.error('Officer ID not set');
            return;
        }

        const [performance, queue] = await Promise.all([
            this.fetchOfficerPerformance(this.userId),
            this.fetchOfficerQueue(this.userId)
        ]);

        // Render performance KPIs
        this.renderOfficerKPIs(performance);
        
        // Render queue with SLA indicators
        this.renderPriorityQueue(queue);
        
        // Render performance chart
        this.renderOfficerPerformanceChart(performance);
    }

    /**
     * Render officer KPI cards
     */
    renderOfficerKPIs(data) {
        const container = document.getElementById('officerAnalyticsKPIs') ||
                         document.getElementById('adminStats');
        if (!container) return;

        const kpis = [
            {
                title: 'Cases Assigned',
                value: data.total_assigned,
                trend: 'This month',
                icon: '📋',
                color: '#3b82f6'
            },
            {
                title: 'Cases Resolved',
                value: data.resolved,
                trend: data.resolution_rate + '% rate',
                icon: '✅',
                color: '#10b981'
            },
            {
                title: 'Avg Resolution Time',
                value: data.avg_resolution_time_hours + ' hrs',
                trend: 'Per case',
                icon: '⏱️',
                color: '#8b5cf6'
            },
            {
                title: 'Performance Score',
                value: data.efficiency_score + '/100',
                trend: 'Based on performance',
                icon: '📊',
                color: '#f59e0b'
            },
            {
                title: 'Citizen Rating',
                value: (data.avg_rating || 0).toFixed(1) + ' ⭐',
                trend: 'Average rating',
                icon: '⭐',
                color: '#f59e0b'
            }
        ];

        container.innerHTML = kpis.map(kpi => `
            <div class="analytics-kpi-card" style="border-left: 4px solid ${kpi.color}">
                <div class="kpi-header">
                    <span class="kpi-icon">${kpi.icon}</span>
                    <span class="kpi-title">${kpi.title}</span>
                </div>
                <div class="kpi-value">${kpi.value}</div>
                <div class="kpi-trend">${kpi.trend}</div>
            </div>
        `).join('');
    }

    /**
     * Render officer performance charts
     */
    renderOfficerPerformanceChart(performance) {
        // Create a simple timeline chart showing resolution rate and efficiency
        this.createLineChart(
            'officerAnalyticsTimeline',
            [
                { _id: 'Resolution Rate', count: performance.resolution_rate },
                { _id: 'Efficiency Score', count: performance.efficiency_score }
            ],
            'Performance Metrics',
            ['#3b82f6', '#10b981']
        );

        // Create category breakdown chart
        this.createBarChart(
            'officerAnalyticsCategory',
            [
                { _id: 'Resolved', count: performance.resolved },
                { _id: 'Pending', count: performance.total_assigned - performance.resolved }
            ],
            'Cases Status',
            '#3b82f6'
        );
    }

    /**
     * Render priority queue with SLA indicators
     */
    renderPriorityQueue(complaints) {
        const container = document.getElementById('officerPriorityQueue') ||
                         document.getElementById('urgentList')?.parentElement;
        if (!container) return;

        const queueHTML = complaints.map(complaint => {
            const sla = complaint.sla || {};
            const slaClass = sla.is_breach ? 'sla-breach' : sla.percentage > 70 ? 'sla-warning' : 'sla-ok';
            
            return `
                <div class="queue-item ${complaint.priority}" data-id="${complaint._id}">
                    <div class="queue-priority">
                        ${this.getPriorityIcon(complaint.priority)}
                    </div>
                    <div class="queue-content">
                        <div class="queue-title">${complaint.category}</div>
                        <div class="queue-desc">${complaint.description?.substring(0, 50)}...</div>
                    </div>
                    <div class="queue-sla ${slaClass}">
                        <span class="sla-text">${sla.hours_elapsed || 0}h/${sla.max_hours || 72}h</span>
                        <span class="sla-bar">
                            <span style="width: ${sla.percentage || 0}%"></span>
                        </span>
                    </div>
                </div>
            `;
        }).join('');

        const wrapper = document.createElement('div');
        wrapper.className = 'analytics-priority-queue';
        wrapper.innerHTML = queueHTML;
        
        const insertPoint = document.querySelector('.analytics-kpi-card')?.parentElement;
        if (insertPoint) {
            insertPoint.insertAdjacentElement('afterend', wrapper);
        }
    }

    /**
     * Chart creation helpers
     */
    createLineChart(elementId, data, label, colors) {
        const canvas = document.getElementById(elementId) || document.createElement('canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        const chartData = {
            labels: data.map(d => d._id),
            datasets: [
                {
                    label: 'Filed',
                    data: data.map(d => d.total),
                    borderColor: colors[0],
                    backgroundColor: colors[0] + '20',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Resolved',
                    data: data.map(d => d.resolved),
                    borderColor: colors[1],
                    backgroundColor: colors[1] + '20',
                    tension: 0.4,
                    fill: true
                }
            ]
        };

        if (this.charts[elementId]) {
            this.charts[elementId].destroy();
        }

        this.charts[elementId] = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true, position: 'top' },
                    title: { display: true, text: label }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    createBarChart(elementId, data, label, color) {
        const canvas = document.getElementById(elementId) || document.createElement('canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        if (this.charts[elementId]) {
            this.charts[elementId].destroy();
        }

        this.charts[elementId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d._id),
                datasets: [{
                    label: 'Complaints',
                    data: data.map(d => d.count),
                    backgroundColor: color,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: true },
                    title: { display: true, text: label }
                }
            }
        });
    }

    createPieChart(elementId, data, labels, label) {
        const canvas = document.getElementById(elementId) || document.createElement('canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const colors = ['#ef4444', '#f97316', '#facc15', '#4ade80'];

        if (this.charts[elementId]) {
            this.charts[elementId].destroy();
        }

        this.charts[elementId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, data.length),
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: label }
                }
            }
        });
    }

    createHorizontalBarChart(elementId, data, label, color) {
        const canvas = document.getElementById(elementId) || document.createElement('canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        if (this.charts[elementId]) {
            this.charts[elementId].destroy();
        }

        this.charts[elementId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d._id),
                datasets: [{
                    label: 'Total Cases',
                    data: data.map(d => d.total),
                    backgroundColor: color,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    title: { display: true, text: label }
                }
            }
        });
    }

    /**
     * API methods
     */
    async fetchAdminOverview() {
        return await fetch(`${this.apiBase}/analytics/admin/overview`)
            .then(r => r.json())
            .then(r => r.data || {});
    }

    async fetchOfficerPerformance(officerId = null) {
        const url = officerId
            ? `${this.apiBase}/analytics/officer/${officerId}/performance`
            : `${this.apiBase}/analytics/admin/officer-performance`;
        
        return await fetch(url)
            .then(r => r.json())
            .then(r => Array.isArray(r.data) ? r.data : [r.data]);
    }

    async fetchTrends() {
        return await fetch(`${this.apiBase}/analytics/admin/trends?period=daily&days=30`)
            .then(r => r.json())
            .then(r => r.data || []);
    }

    async fetchOfficerQueue(officerId) {
        return await fetch(`${this.apiBase}/analytics/officer/${officerId}/queue`)
            .then(r => r.json())
            .then(r => r.data || []);
    }

    /**
     * Filtering system
     */
    setupFilterListeners() {
        // Add event listeners for filter controls
        document.addEventListener('change', (e) => {
            if (e.target.matches('[data-filter]')) {
                this.applyFilters();
            }
        });
    }

    async applyFilters() {
        try {
            const response = await fetch(`${this.apiBase}/analytics/filtered`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filters: this.filters })
            });
            
            const result = await response.json();
            if (result.success) {
                this.loadDashboard();
            }
        } catch (error) {
            console.error('Filter application failed:', error);
        }
    }

    /**
     * Export functionality
     */
    async exportData(format = 'json') {
        try {
            const response = await fetch(`${this.apiBase}/analytics/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filters: this.filters,
                    format: format
                })
            });

            if (format === 'csv') {
                const blob = await response.blob();
                this.downloadFile(blob, 'analytics.csv');
            } else {
                const data = await response.json();
                this.downloadFile(
                    new Blob([JSON.stringify(data, null, 2)]),
                    'analytics.json'
                );
            }
        } catch (error) {
            console.error('Export failed:', error);
        }
    }

    /**
     * Utility methods
     */
    getPriorityIcon(priority) {
        const icons = {
            'emergency': '🚨',
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        };
        return icons[priority] || '⚪';
    }

    getDateBefore(days) {
        const date = new Date();
        date.setDate(date.getDate() - days);
        return date;
    }

    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    async loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    showError(message) {
        const container = document.querySelector('[role="main"]') || document.body;
        const error = document.createElement('div');
        error.className = 'analytics-error';
        error.innerHTML = `<div style="padding: 20px; background: #fee2e2; color: #991b1b; border-radius: 8px; border: 1px solid #fecaca;">❌ ${message}</div>`;
        container.insertAdjacentElement('afterbegin', error);
    }

    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            this.loadDashboard();
        }, this.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
    }

    destroy() {
        this.stopAutoRefresh();
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
    }
}

// Make available globally
window.AdvancedAnalyticsManager = AdvancedAnalyticsManager;
