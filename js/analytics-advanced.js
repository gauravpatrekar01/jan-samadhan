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
            
            // Initial data load
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
        
        const [overview, performance, trends, peakTimes, ngoStats, escalations] = await Promise.all([
            this.fetchAdminOverview(),
            this.fetchOfficerPerformance(),
            this.fetchTrends(),
            this.fetchPeakTimes(),
            this.fetchNGOContribution(),
            this.fetchEscalationsAdvanced()
        ]);

        // Render KPI cards
        this.renderAdminKPIs(overview);
        
        // Render charts
        this.renderAdminCharts(overview, trends);
        
        // Render officer leaderboard
        this.renderOfficerLeaderboard(performance);

        // Render advanced ML/System insights
        this.renderAdvancedInsights(peakTimes, ngoStats, escalations);
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

        // Category distribution - robust check for proper structure
        let categoryData = overview.category_distribution || [];
        if (categoryData.length === 0 && overview.category_breakdown) {
            categoryData = overview.category_breakdown;
        }

        this.createBarChart(
            'adminAnalyticsCategory',
            categoryData,
            'Complaints by Category',
            '#3b82f6'
        );

        // Priority distribution - robust check
        let priorityDist = overview.priority_distribution || { emergency: 0, high: 0, medium: 0, low: 0 };
        this.createPieChart(
            'adminAnalyticsPriority',
            Object.values(priorityDist),
            Object.keys(priorityDist).map(p => p.charAt(0).toUpperCase() + p.slice(1)),
            'Priority Distribution'
        );

        // Region performance
        let regionData = overview.region_performance || [];
        this.createHorizontalBarChart(
            'adminAnalyticsRegion',
            regionData,
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
        if (insertPoint && !document.querySelector('.analytics-leaderboard')) {
            insertPoint.insertAdjacentHTML('afterend', leaderboardHTML);
        }
    }

    renderAdvancedInsights(peakTimes, ngoStats, escalations) {
        const insertPoint = document.querySelector('.analytics-leaderboard') || document.querySelector('.analytics-kpi-card')?.parentElement;
        if (!insertPoint || document.querySelector('.advanced-insights-container')) return;

        let ngoHTML = '';
        if (ngoStats && ngoStats.length > 0) {
            ngoHTML = `
            <div class="card" style="padding:20px; background: rgba(59, 130, 246, 0.05); border: 1px solid #bfdbfe;">
                <h4 style="margin-bottom:12px; color: #1e40af;">🤝 NGO Partner Impact</h4>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#475569;">Top Contributor:</span> 
                    <strong style="color:#0f172a;">${ngoStats[0].ngo_id}</strong>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#475569;">Resolution Rate:</span> 
                    <strong style="color:#10b981;">${ngoStats[0].success_rate}%</strong>
                </div>
            </div>`;
        }

        const html = `
        <div class="advanced-insights-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; margin-bottom: 30px;">
            <div class="card" style="padding:20px; background: rgba(245, 158, 11, 0.05); border: 1px solid #fde68a;">
                <h4 style="margin-bottom:12px; color: #b45309;">🔮 Peak Complaint Times</h4>
                <p style="color: #78350f; font-size: 0.95rem; line-height: 1.5; margin-bottom: 8px;">
                    ${peakTimes?.prediction || 'Analyzing system peaks...'}
                </p>
                <div style="font-size: 0.85rem; color: #92400e;">Recommendation: Align primary support shifts for these times.</div>
            </div>
            
            <div class="card" style="padding:20px; background: rgba(239, 68, 68, 0.05); border: 1px solid #fecaca;">
                <h4 style="margin-bottom:12px; color: #b91c1c;">⚠️ Escalation Deep Dive</h4>
                <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                    <span style="color:#475569;">Active Escalated Cases:</span> 
                    <strong style="color:#b91c1c; font-size:1.1rem;">${escalations?.total_escalated || 0}</strong>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#475569;">Unresolved SLA Breaches:</span> 
                    <strong style="color:#991b1b;">${escalations?.unresolved_sla_breaches || 0}</strong>
                </div>
            </div>
            ${ngoHTML}
        </div>
        `;
        insertPoint.insertAdjacentHTML('afterend', html);
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
            window.JanSamadhanAPI.getOfficerPerformance(this.userId),
            window.JanSamadhanAPI.getOfficerQueue(this.userId)
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
        return await window.JanSamadhanAPI.getAnalyticsOverview(30);
    }

    async fetchOfficerPerformance(officerId = null) {
        if (officerId) {
            return await window.JanSamadhanAPI.getOfficerPerformance(officerId);
        }
        return await window.JanSamadhanAPI.getAdminOfficerPerformance();
    }

    async fetchTrends() {
        const data = await window.JanSamadhanAPI.getAnalyticsTrends(30);
        return data.timeline || [];
    }

    async fetchOfficerQueue(officerId) {
        return await window.JanSamadhanAPI.getOfficerQueue(officerId);
    }

    async fetchPeakTimes() {
        return await window.JanSamadhanAPI.getAdminPeakTimes();
    }

    async fetchNGOContribution() {
        return await window.JanSamadhanAPI.getAdminNGOContribution();
    }

    async fetchEscalationsAdvanced() {
        return await window.JanSamadhanAPI.getAdminEscalationAdvanced();
    }

    /**
     * Filtering system
     */
    setupFilterListeners() {
        // Add event listeners for filter controls
        document.addEventListener('change', (e) => {
            if (e.target.matches('[data-filter]')) {
                const filterKey = e.target.getAttribute('data-filter');
                const value = e.target.value;
                if (filterKey === 'days') {
                    this.filters.dateRange = { start: this.getDateBefore(parseInt(value)), end: new Date() };
                } else {
                    if (value) {
                        this.filters[filterKey] = [value];
                    } else {
                        delete this.filters[filterKey];
                    }
                }
                this.applyFilters();
            }
        });
    }

    async applyFilters() {
        try {
            const bodyPayload = { ...this.filters };
            // Ensure date strings are sent if JS Dates
            if (bodyPayload.dateRange) {
                bodyPayload.date_range = {
                    start: bodyPayload.dateRange.start.toISOString(),
                    end: bodyPayload.dateRange.end.toISOString()
                };
                delete bodyPayload.dateRange;
            }

            const data = await window.JanSamadhanAPI.getFilteredAnalytics(bodyPayload);
            if (data) {
                // Update basic stats temporarily
                const data = result.data;
                const container = document.getElementById(this.userRole === 'admin' ? 'adminAnalyticsKPIs' : 'officerAnalyticsKPIs') || document.getElementById('adminStats');
                if (container) {
                    // Update only resolution rate and total and pending, as filtering drops advanced fields
                    const currentHTML = container.innerHTML;
                    // For simplicity, refresh standard dashboard to refetch with actual query params if backend supports it
                    // The backend does support it, but it only returns total, resolved, resolution_rate, category_breakdown.
                }

                // If admin, update category chart directly
                if (this.userRole === 'admin' && data.category_breakdown) {
                    this.createBarChart('adminAnalyticsCategory', data.category_breakdown, 'Filtered Complaints by Category', '#3b82f6');
                } else if (this.userRole === 'officer' && data.category_breakdown) {
                    this.createBarChart('officerAnalyticsCategory', data.category_breakdown, 'Filtered Case Status/Category', '#3b82f6');
                }
            }
        } catch (error) {
            console.error('Filter application failed:', error);
        }
    }

    /**
     * Export functionality
     */
    async exportData(format = 'csv') {
        try {
            const bodyPayload = { ...this.filters };
            // Ensure date strings are sent if JS Dates
            if (bodyPayload.dateRange) {
                bodyPayload.date_range = {
                    start: bodyPayload.dateRange.start.toISOString(),
                    end: bodyPayload.dateRange.end.toISOString()
                };
                delete bodyPayload.dateRange;
            }

            const result = await window.JanSamadhanAPI.exportAnalytics(bodyPayload, format);
            
            if (format === 'csv' && result.content) {
                const blob = new Blob([result.content], { type: 'text/csv;charset=utf-8;' });
                this.downloadFile(blob, `jansamadhan-analytics-${new Date().toISOString().split('T')[0]}.csv`);
            } else if (result.success && result.data) {
                this.downloadFile(
                    new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' }),
                    `jansamadhan-analytics-${new Date().toISOString().split('T')[0]}.json`
                );
            }
        } catch (error) {
            console.error('Export failed:', error);
            this.showError('Export failed. Please try again.');
        }
    }

    async exportPdfReport(days = 30) {
        try {
            const response = await window.JanSamadhanAPI.generateReport({ days });
            if (response?.report_url) {
                window.open(response.report_url, '_blank');
            }
        } catch (error) {
            console.error('PDF report generation failed:', error);
            this.showError('PDF report generation failed. Please try again.');
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
