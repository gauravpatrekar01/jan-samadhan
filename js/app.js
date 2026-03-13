// Utility functions and state management
window.JanSamadhan = {
    STATUS_STAGES: ['Submitted', 'Under Review', 'In Progress', 'Resolved', 'Closed'],
    
    logout() {
        window.JanSamadhanAPI.logout();
    },

    async getStats() {
        try {
            return await window.JanSamadhanAPI.getAnalytics();
        } catch (e) {
            return { total: 0, resolved: 0, resolutionRate: 0 };
        }
    },

    async getGrievanceByID(id) {
        return await window.JanSamadhanAPI.getGrievanceByID(id);
    },

    async getPriorityQueue(filter) {
        // Now returns all grievances for the dashboard to filter
        return await window.JanSamadhanAPI.getAllGrievances();
    },

    getAnnouncements() {
        // Temporarily keeps dummy announcements until Firestore migration is fully verified
        return [
            { id: '1', text: "System maintenance scheduled for March 15th, 2 AM to 4 AM.", date: "2026-03-12", pinned: true },
            { id: '2', text: "New 'JanBot' AI assistant launched to help with grievance filing!", date: "2026-03-10", pinned: false },
            { id: '3', text: "Monsoon preparedness drive: Report drainage issues early.", date: "2026-03-08", pinned: false }
        ];
    },

    async submitFeedback(id, rating, comment) {
        console.log(`Feedback for ${id}: ${rating} stars, "${comment}"`);
        return await window.JanSamadhanAPI.updateGrievanceStatus(id, 'closed', `User Feedback (${rating} stars): ${comment}`);
    }
};

function getSessionUser() {
    const user = localStorage.getItem('js_user');
    return user ? JSON.parse(user) : null;
}

function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Global UI Helpers (referenced in HTML)
function categoryIcon(cat) {
    const icons = { 'Infrastructure': '🏗️', 'Water Supply': '💧', 'Electricity': '⚡', 'Sanitation': '🚯', 'Transport': '🚌', 'Law & Order': '⚖️', 'Healthcare': '🏥', 'Other': '📋' };
    return icons[cat] || '📋';
}

function categoryColor(cat) {
    const colors = { 'Infrastructure': '#3b82f6', 'Water Supply': '#0ea5e9', 'Electricity': '#eab308', 'Sanitation': '#8b5cf6', 'Transport': '#10b981', 'Law & Order': '#f43f5e', 'Healthcare': '#ef4444', 'Other': '#64748b' };
    return colors[cat] || '#64748b';
}

function priorityBadge(p) {
    const s = p?.toLowerCase() || 'medium';
    const badges = { 'emergency': '🚨 Emergency', 'high': '🔴 High', 'medium': '🟠 Medium', 'low': '🟢 Low' };
    return `<span class="badge badge-${s}">${badges[s] || p}</span>`;
}

function statusBadge(s) {
    const st = s?.toLowerCase() || 'submitted';
    return `<span class="badge badge-${st.replace('_', '-')}">${s}</span>`;
}

function timeAgo(date) {
    if (!date) return 'N/A';
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function renderProgressBar(percent) {
    return `<div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:${percent}%"></div></div>`;
}

// Modal Toggle
function openModal(id) { document.getElementById(id)?.classList.add('show'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('show'); }

// Basic Dark Mode
function toggleDark() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
}

// Counter animation
function initCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseInt(el.dataset.counter);
        const suffix = el.dataset.suffix || '';
        let count = 0;
        const inc = target / 50;
        const timer = setInterval(() => {
            count += inc;
            if (count >= target) {
                el.innerText = target + suffix;
                clearInterval(timer);
            } else {
                el.innerText = Math.floor(count) + suffix;
            }
        }, 30);
    });
}

function renderDummyMap(id, points = [], interactive = false) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '<div style="width:100%;height:100%;background:rgba(0,0,0,0.03);display:flex;align-items:center;justify-content:center;color:var(--text-light);font-family:var(--font-main);border:2px dashed var(--border);border-radius:var(--radius-md)">[ Interactive Map Component ]</div>';
}
