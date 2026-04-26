/**
 * 🎯 Advanced Analytics Module for JanSamadhan
 * Comprehensive data-driven insights, visualizations, and intelligence
 * Features: Real-time dashboards, filtering, exports, AI-based recommendations
 */

class AdvancedAnalytics {
  constructor(options = {}) {
    this.apiBase = options.apiBase || '/api';
    this.userRole = options.userRole || 'officer'; // 'officer' or 'admin'
    this.userId = options.userId || null;
    this.refreshInterval = options.refreshInterval || 30000;
    
    this.charts = {};
    this.data = {};
    this.filters = {
      dateRange: { start: this.getDateBefore(30), end: new Date() },
      category: [],
      priority: [],
      region: [],
      status: []
    };
    
    this.cache = {};
    this.cacheExpiry = {};
    this.autoRefreshEnabled = true;
  }

  /**
   * Initialize analytics system
   */
  async init() {
    try {
      console.log('📊 Initializing Advanced Analytics...');
      
      // Load Chart.js
      if (typeof Chart === 'undefined') {
        await this.loadScript('https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js');
      }
      
      // Initialize UI
      this.initializeUI();
      
      // Load initial data
      await this.loadDashboard();
      
      // Setup event listeners
      this.setupEventListeners();
      
      // Start auto-refresh
      this.startAutoRefresh();
      
      console.log('✅ Analytics initialized');
    } catch (error) {
      console.error('❌ Analytics init failed:', error);
      this.showError('Failed to initialize analytics');
    }
  }

  /**
   * Initialize UI elements
   */
  initializeUI() {
    // Filter listeners
    const dateStartInput = document.getElementById('filterDateStart');
    const dateEndInput = document.getElementById('filterDateEnd');
    
    if (dateStartInput) {
      dateStartInput.value = this.formatDate(this.filters.dateRange.start);
      dateStartInput.addEventListener('change', (e) => {
        this.filters.dateRange.start = new Date(e.target.value);
        this.applyFilters();
      });
    }
    
    if (dateEndInput) {
      dateEndInput.value = this.formatDate(this.filters.dateRange.end);
      dateEndInput.addEventListener('change', (e) => {
        this.filters.dateRange.end = new Date(e.target.value);
        this.applyFilters();
      });
    }

    // Filter buttons
    document.querySelectorAll('[data-filter-type]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const type = btn.dataset.filterType;
        const value = btn.dataset.filterValue;
        this.toggleFilter(type, value);
      });
    });

    // Export button
    document.getElementById('exportBtn')?.addEventListener('click', () => this.exportData());
    
    // Refresh button
    document.getElementById('refreshBtn')?.addEventListener('click', () => this.loadDashboard());
  }

  /**
   * Load full dashboard based on role
   */
  async loadDashboard() {
    try {
      if (this.userRole === 'admin') {
        await Promise.all([
          this.loadAdminOverview(),
          this.loadOfficerPerformance(),
          this.loadTrends(),
          this.loadNGOContribution(),
          this.loadEscalations(),
          this.loadPeakTimes()
        ]);
      } else {
        await Promise.all([
          this.loadOfficerMetrics(),
          this.loadQueue(),
          this.loadRegionalHeatmap()
        ]);
      }
      
      this.updateDashboard();
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  }

  /**
   * ════════════════════════════════════════════
   * ADMIN ANALYTICS
   * ════════════════════════════════════════════
   */

  async loadAdminOverview() {
    try {
      const cached = this.getCache('adminOverview');
      if (cached) {
        this.data.adminOverview = cached;
        return;
      }

      const response = await fetch(`${this.apiBase}/analytics/admin/overview`);
      const result = await response.json();
      
      if (result.success) {
        this.data.adminOverview = result.data;
        this.setCache('adminOverview', result.data);
      }
    } catch (error) {
      console.error('Error loading admin overview:', error);
    }
  }

  async loadOfficerPerformance() {
    try {
      const cached = this.getCache('officerPerf');
      if (cached) {
        this.data.officerPerformance = cached;
        return;
      }

      const response = await fetch(`${this.apiBase}/analytics/admin/officer-performance?limit=20`);
      const result = await response.json();
      
      if (result.success) {
        this.data.officerPerformance = result.data;
        this.setCache('officerPerf', result.data);
      }
    } catch (error) {
      console.error('Error loading officer performance:', error);
    }
  }

  async loadTrends() {
    try {
      const cached = this.getCache('trends');
      if (cached) {
        this.data.trends = cached;
        return;
      }

      const response = await fetch(`${this.apiBase}/analytics/admin/trends?period=daily&days=30`);
      const result = await response.json();
      
      if (result.success) {
        this.data.trends = result.data;
        this.setCache('trends', result.data);
      }
    } catch (error) {
      console.error('Error loading trends:', error);
    }
  }

  async loadNGOContribution() {
    try {
      const response = await fetch(`${this.apiBase}/analytics/admin/ngo-contribution`);
      const result = await response.json();
      
      if (result.success) {
        this.data.ngoContribution = result.data;
      }
    } catch (error) {
      console.error('Error loading NGO contribution:', error);
    }
  }

  async loadEscalations() {
    try {
      const response = await fetch(`${this.apiBase}/analytics/admin/escalation-advanced`);
      const result = await response.json();
      
      if (result.success) {
        this.data.escalations = result.data;
      }
    } catch (error) {
      console.error('Error loading escalations:', error);
    }
  }

  async loadPeakTimes() {
    try {
      const response = await fetch(`${this.apiBase}/analytics/admin/peak-times`);
      const result = await response.json();
      
      if (result.success) {
        this.data.peakTimes = result.data;
      }
    } catch (error) {
      console.error('Error loading peak times:', error);
    }
  }

  /**
   * ════════════════════════════════════════════
   * OFFICER ANALYTICS
   * ════════════════════════════════════════════
   */

  async loadOfficerMetrics() {
    try {
      if (!this.userId) return;
      
      const response = await fetch(`${this.apiBase}/analytics/officer/${this.userId}/performance`);
      const result = await response.json();
      
      if (result.success) {
        this.data.officerMetrics = result.data;
      }
    } catch (error) {
      console.error('Error loading officer metrics:', error);
    }
  }

  async loadQueue() {
    try {
      if (!this.userId) return;
      
      const response = await fetch(`${this.apiBase}/analytics/officer/${this.userId}/queue`);
      const result = await response.json();
      
      if (result.success) {
        this.data.queue = result.data;
      }
    } catch (error) {
      console.error('Error loading queue:', error);
    }
  }

  async loadRegionalHeatmap() {
    // This would use geographical data from the officer's complaints
    // Implementation depends on your data structure
    try {
      if (!this.userId) return;
      
      const response = await fetch(`${this.apiBase}/analytics/officer/${this.userId}/performance`);
      const result = await response.json();
      
      if (result.success) {
        // Use this data to create heatmap visualization
        this.data.regionalHeatmap = result.data;
      }
    } catch (error) {
      console.error('Error loading regional heatmap:', error);
    }
  }

  /**
   * ════════════════════════════════════════════
   * VISUALIZATION & RENDERING
   * ════════════════════════════════════════════
   */

  updateDashboard() {
    if (this.userRole === 'admin') {
      this.renderAdminDashboard();
    } else {
      this.renderOfficerDashboard();
    }
  }

  renderAdminDashboard() {
    const overview = this.data.adminOverview || {};
    
    // Update KPI cards
    this.updateKPI('kpiTotal', overview.total_complaints || 0);
    this.updateKPI('kpiResolved', overview.resolved_complaints || 0);
    this.updateKPI('kpiResolutionRate', (overview.resolution_rate || 0) + '%');
    this.updateKPI('kpiPending', overview.pending_complaints || 0);
    this.updateKPI('kpiSLABreach', overview.sla_breaches || 0);
    this.updateKPI('kpiAvgTime', Math.round(overview.avg_resolution_time_hours || 0) + 'h');

    // Render charts
    this.renderCategoryChart(overview);
    this.renderPriorityChart(overview);
    this.renderTrendChart();
    this.renderOfficerLeaderboard();
    this.renderEscalationChart();
    this.renderPeakTimesChart();
  }

  renderOfficerDashboard() {
    const metrics = this.data.officerMetrics || {};
    
    // Update KPI cards
    this.updateKPI('kpiAssigned', metrics.total_assigned || 0);
    this.updateKPI('kpiResolved', metrics.resolved || 0);
    this.updateKPI('kpiResolutionRate', (metrics.resolution_rate || 0) + '%');
    this.updateKPI('kpiEfficiency', Math.round(metrics.efficiency_score || 0));
    this.updateKPI('kpiAvgRating', (metrics.avg_rating || 0).toFixed(1) + '★');
    this.updateKPI('kpiAvgTime', Math.round(metrics.avg_resolution_time_hours || 0) + 'h');

    // Render priority queue
    this.renderPriorityQueue();
  }

  updateKPI(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
      const valueEl = element.querySelector('.kpi-value');
      if (valueEl) {
        valueEl.textContent = value;
        valueEl.style.animation = 'pulse 0.5s ease';
      }
    }
  }

  renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart')?.getContext('2d');
    if (!ctx) return;

    const categories = data.category_distribution || [];
    const labels = categories.map(c => c._id || 'Unknown');
    const values = categories.map(c => c.count || 0);

    this.destroyChart('categoryChart');
    this.charts.categoryChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: values,
          backgroundColor: [
            '#3b82f6', '#0ea5e9', '#eab308', '#8b5cf6', '#64748b',
            '#f43f5e', '#10b981', '#f97316', '#6366f1', '#ec4899'
          ],
          borderColor: '#fff',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${ctx.parsed} complaints`
            }
          }
        }
      }
    });
  }

  renderPriorityChart(data) {
    const ctx = document.getElementById('priorityChart')?.getContext('2d');
    if (!ctx) return;

    const priority = data.priority_distribution || {};
    const priorities = ['emergency', 'high', 'medium', 'low'];
    const colors = ['#dc2626', '#f97316', '#eab308', '#10b981'];

    this.destroyChart('priorityChart');
    this.charts.priorityChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: priorities.map(p => p.charAt(0).toUpperCase() + p.slice(1)),
        datasets: [{
          label: 'Complaints',
          data: priorities.map(p => priority[p] || 0),
          backgroundColor: colors,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }

  renderTrendChart() {
    const ctx = document.getElementById('trendChart')?.getContext('2d');
    if (!ctx) return;

    const trends = this.data.trends || [];
    const labels = trends.map(t => t._id || 'N/A');
    const totalData = trends.map(t => t.total || 0);
    const resolvedData = trends.map(t => t.resolved || 0);

    this.destroyChart('trendChart');
    this.charts.trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Total Filed',
            data: totalData,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 235, 0.1)',
            tension: 0.4
          },
          {
            label: 'Resolved',
            data: resolvedData,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }

  renderOfficerLeaderboard() {
    const leaderboard = this.data.officerPerformance || [];
    const container = document.getElementById('leaderboardContainer');
    
    if (!container) return;

    container.innerHTML = leaderboard.slice(0, 10).map((officer, idx) => `
      <div class="leaderboard-item" style="animation-delay: ${idx * 50}ms">
        <div class="rank">#${idx + 1}</div>
        <div class="info">
          <div class="name">${officer.officer}</div>
          <div class="stats">
            <span>📋 ${officer.total_assigned} assigned</span>
            <span>✅ ${officer.resolved} resolved</span>
          </div>
        </div>
        <div class="score">
          <div class="score-value">${officer.efficiency_score}</div>
          <div class="score-label">efficiency</div>
        </div>
      </div>
    `).join('');
  }

  renderEscalationChart() {
    const escalations = this.data.escalations || {};
    const container = document.getElementById('escalationContainer');
    
    if (!container) return;

    const total = escalations.total_escalated || 0;
    const unresolved = escalations.unresolved_sla_breaches || 0;
    const resolved = total - unresolved;

    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <div class="stat-card">
          <div class="stat-value" style="color: var(--danger)">${total}</div>
          <div class="stat-label">Total Escalated</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" style="color: var(--warning)">${unresolved}</div>
          <div class="stat-label">SLA Breaches</div>
        </div>
      </div>
    `;
  }

  renderPeakTimesChart() {
    const peakTimes = this.data.peakTimes?.peak_hours || [];
    const ctx = document.getElementById('peakTimesChart')?.getContext('2d');
    
    if (!ctx) return;

    const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`);
    const counts = new Array(24).fill(0);
    
    peakTimes.forEach(pt => {
      const hour = parseInt(pt.hour.split(':')[0]);
      counts[hour] = pt.count;
    });

    this.destroyChart('peakTimesChart');
    this.charts.peakTimesChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: hours,
        datasets: [{
          label: 'Complaints Filed',
          data: counts,
          backgroundColor: '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  renderPriorityQueue() {
    const queue = this.data.queue || [];
    const container = document.getElementById('queueContainer');
    
    if (!container) return;

    container.innerHTML = queue.slice(0, 10).map(complaint => `
      <div class="queue-item priority-${complaint.priority}">
        <div class="priority-badge">${complaint.priority.toUpperCase()}</div>
        <div class="complaint-info">
          <div class="complaint-id">${complaint.grievanceID || complaint.id}</div>
          <div class="complaint-desc">${complaint.title || complaint.description?.substring(0, 50)}</div>
        </div>
        <div class="sla-status ${complaint.sla?.is_breach ? 'breach' : 'ok'}">
          ${Math.round(complaint.sla?.percentage || 0)}% SLA
        </div>
      </div>
    `).join('');
  }

  /**
   * ════════════════════════════════════════════
   * FILTERING & INTERACTIONS
   * ════════════════════════════════════════════
   */

  toggleFilter(type, value) {
    if (!this.filters[type]) this.filters[type] = [];
    
    const index = this.filters[type].indexOf(value);
    if (index > -1) {
      this.filters[type].splice(index, 1);
    } else {
      this.filters[type].push(value);
    }
    
    this.applyFilters();
  }

  async applyFilters() {
    try {
      // Debounce filter updates
      clearTimeout(this.filterTimeout);
      this.filterTimeout = setTimeout(async () => {
        const response = await fetch(`${this.apiBase}/analytics/filtered`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            date_range: {
              start: this.filters.dateRange.start.toISOString(),
              end: this.filters.dateRange.end.toISOString()
            },
            category: this.filters.category,
            priority: this.filters.priority,
            region: this.filters.region,
            status: this.filters.status
          })
        });

        const result = await response.json();
        if (result.success) {
          this.data.filtered = result.data;
          this.updateDashboard();
        }
      }, 300);
    } catch (error) {
      console.error('Error applying filters:', error);
    }
  }

  /**
   * ════════════════════════════════════════════
   * EXPORT & DATA MANAGEMENT
   * ════════════════════════════════════════════
   */

  async exportData() {
    try {
      const format = document.getElementById('exportFormat')?.value || 'json';
      const response = await fetch(`${this.apiBase}/analytics/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filters: this.filters,
          format: format
        })
      });

      const result = await response.json();
      
      if (format === 'csv' && result.content) {
        this.downloadCSV(result.content, 'analytics-report.csv');
      } else if (result.data) {
        this.downloadJSON(result.data, 'analytics-report.json');
      }
      
      showToast('✅ Report exported successfully', 'success');
    } catch (error) {
      console.error('Export error:', error);
      this.showError('Export failed');
    }
  }

  downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', filename);
    link.click();
  }

  downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', filename);
    link.click();
  }

  /**
   * ════════════════════════════════════════════
   * AUTO-REFRESH & UTILITIES
   * ════════════════════════════════════════════
   */

  startAutoRefresh() {
    if (this.autoRefreshEnabled) {
      this.refreshInterval = setInterval(() => {
        this.loadDashboard();
      }, this.refreshInterval);
    }
  }

  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.autoRefreshEnabled = false;
    }
  }

  setupEventListeners() {
    // Add auto-refresh toggle
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
      autoRefreshToggle.addEventListener('change', (e) => {
        this.autoRefreshEnabled = e.target.checked;
        if (e.target.checked) {
          this.startAutoRefresh();
        } else {
          this.stopAutoRefresh();
        }
      });
    }
  }

  // Cache management
  setCache(key, value, duration = 60000) {
    this.cache[key] = value;
    this.cacheExpiry[key] = Date.now() + duration;
  }

  getCache(key) {
    if (this.cache[key] && this.cacheExpiry[key] > Date.now()) {
      return this.cache[key];
    }
    delete this.cache[key];
    delete this.cacheExpiry[key];
    return null;
  }

  // Utility methods
  getDateBefore(days) {
    const date = new Date();
    date.setDate(date.getDate() - days);
    return date;
  }

  formatDate(date) {
    return date.toISOString().split('T')[0];
  }

  destroyChart(chartId) {
    if (this.charts[chartId]) {
      this.charts[chartId].destroy();
      delete this.charts[chartId];
    }
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
    console.error(message);
    if (typeof showToast === 'function') {
      showToast(message, 'error');
    }
  }
}

// Global instance
let advancedAnalytics = null;

function initAdvancedAnalytics(options) {
  advancedAnalytics = new AdvancedAnalytics(options);
  return advancedAnalytics.init();
}
