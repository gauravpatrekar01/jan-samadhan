// Utility functions and state management
window.JanSamadhan = {
    STATUS_STAGES: ['Submitted', 'Under Review', 'In Progress', 'Resolved', 'Closed'],
    
    logout() {
        window.JanSamadhanAPI.logout();
    },

    async getStats() {
        try {
            const data = await window.JanSamadhanAPI.getAnalytics();
            // Normalise both shapes (public /api/stats and admin /api/admin/analytics)
            return {
                total: data.total_complaints || 0,
                resolved: data.resolved_complaints || 0,
                resolutionRate: data.resolution_rate || 0,
                pending: data.pending || data.status_distribution?.submitted || 0,
                emergency: data.emergency || data.priority_distribution?.emergency || 0,
                high: data.high || data.priority_distribution?.high || 0,
                // Pass through the raw shape too so admin dashboard fallback works
                total_complaints: data.total_complaints || 0,
                resolved_complaints: data.resolved_complaints || 0,
                resolution_rate: data.resolution_rate || 0,
                status_distribution: data.status_distribution || {},
                priority_distribution: data.priority_distribution || {},
            };
        } catch (e) {
            return { total: 0, resolved: 0, resolutionRate: 0, pending: 0, emergency: 0, high: 0 };
        }
    },

    async getGrievanceByID(id) {
        return await window.JanSamadhanAPI.getGrievanceByID(id);
    },

    getPriorityQueue(filter) {
        // Returns an empty array synchronously — the admin dashboard
        // will populate urgentList/recentResolved from the API separately.
        return [];
    },

    async getAnnouncements() {
        try {
            const data = await window.JanSamadhanAPI.getNotices();
            // If API returns data and it's not empty, use it; otherwise use dummy
            if (data && data.length > 0) {
                return data;
            } else {
                return [
                    { id: '1', text: "System maintenance scheduled for March 15th, 2 AM to 4 AM.", date: "2026-03-12", pinned: true },
                    { id: '2', text: "New 'JanBot' AI assistant launched to help with grievance filing!", date: "2026-03-10", pinned: false },
                    { id: '3', text: "Monsoon preparedness drive: Report drainage issues early.", date: "2026-03-08", pinned: false }
                ];
            }
        } catch (e) {
            // Fallback to dummy data if API fails
            return [
                { id: '1', text: "System maintenance scheduled for March 15th, 2 AM to 4 AM.", date: "2026-03-12", pinned: true },
                { id: '2', text: "New 'JanBot' AI assistant launched to help with grievance filing!", date: "2026-03-10", pinned: false },
                { id: '3', text: "Monsoon preparedness drive: Report drainage issues early.", date: "2026-03-08", pinned: false }
            ];
        }
    },

    async submitFeedback(id, rating, comment) {
        console.log(`Feedback for ${id}: ${rating} stars, "${comment}"`);
        return await window.JanSamadhanAPI.submitFeedback(id, rating, comment);
    },

    async upvoteGrievance(id) {
        try {
            const result = await window.JanSamadhanAPI._fetch(`/api/complaints/${id}/vote?vote_type=up`, { method: 'POST' });
            return result;
        } catch (e) {
            console.error('Upvote failed:', e);
            throw e;
        }
    },

    async requestNGOHndling(complaintId) {
        try {
            return await window.JanSamadhanAPI._fetch('/api/ngo/requests', {
                method: 'POST',
                body: JSON.stringify({ complaint_id: complaintId })
            });
        } catch (e) {
            console.error('NGO Request failed:', e);
            throw e;
        }
    },

    // UI HELPER METHODS
    utils: {
        priorityBadge(p) {
            const s = (p || 'medium').toLowerCase();
            const colors = { emergency: '#991b1b', high: '#dc2626', medium: '#d97706', low: '#16a34a' };
            return `<span class="badge" style="background:${colors[s]}20;color:${colors[s]};border:1px solid ${colors[s]}40;font-weight:700;text-transform:uppercase;font-size:0.65rem;padding:2px 8px;border-radius:4px">${s}</span>`;
        },
        statusBadge(s) {
            const st = (s || 'submitted').toLowerCase();
            const colors = { submitted: '#64748b', under_review: '#3b82f6', in_progress: '#8b5cf6', resolved: '#16a34a', closed: '#1e293b' };
            const label = st.replace('_', ' ').toUpperCase();
            return `<span class="badge" style="background:${colors[st]}15;color:${colors[st]};border:1px solid ${colors[st]}30;font-weight:700;font-size:0.65rem;padding:2px 8px;border-radius:4px">${label}</span>`;
        },
        categoryIcon(c) {
            const icons = { Infrastructure: '🏗️', 'Water Supply': '💧', Electricity: '⚡', Sanitation: '🧹', Transport: '🚌', 'Law & Order': '🛡️', Healthcare: '🏥', Other: '📋' };
            return icons[c] || '📋';
        },
        categoryColor(c) {
            const colors = { Infrastructure: '#3b82f6', 'Water Supply': '#0ea5e9', Electricity: '#eab308', Sanitation: '#8b5cf6', Transport: '#f97316', 'Law & Order': '#dc2626', Healthcare: '#10b981', Other: '#64748b' };
            return colors[c] || '#64748b';
        },
        timeAgo(date) {
            if (!date) return 'N/A';
            const seconds = Math.floor((new Date() - new Date(date)) / 1000);
            if (seconds < 60) return 'Just now';
            const intervals = { yr: 31536000, mo: 2592000, wk: 604800, day: 86400, hr: 3600, min: 60 };
            for (let i in intervals) {
                const count = Math.floor(seconds / intervals[i]);
                if (count > 0) return `${count}${i} ago`;
            }
            return 'N/A';
        }
    }
};

function getSessionUser() {
    const user = localStorage.getItem('js_user');
    return user ? JSON.parse(user) : null;
}

function isOnline() {
    return window.navigator.onLine;
}

window.addEventListener('online', () => {
    showToast('You are back online! Syncing data...', 'success');
});

window.addEventListener('offline', () => {
    showToast('You are currently offline. Some features may be unavailable.', 'warning');
});

function showToast(message, type = 'info') {
    // Ensure container exists on body
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = { success: '✅', info: 'ℹ️', warning: '⚠️', error: '❌' };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || '🔔'}</span>
        <span class="toast-msg">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
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
    if (!date) return 'N/A';
    const d = new Date(date);
    return new Intl.DateTimeFormat(navigator.language, {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
        timeZoneName: 'short'
    }).format(d);
}

function renderProgressBar(percent) {
    return `<div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:${percent}%"></div></div>`;
}

function formatDeadline(deadline) {
    if (!deadline) return "No deadline set";
    const d = new Date(deadline);
    return d.toLocaleString(navigator.language, {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function getDeadlineBadge(deadline) {
    if (!deadline) return "";
    const now = new Date();
    const d = new Date(deadline);

    if (d < now) return `<span class="badge badge-error">🚨 Overdue</span>`;
    
    const diff = (d - now) / (1000 * 60 * 60);
    if (diff < 6) return `<span class="badge badge-warning">⏰ Urgent</span>`;
    
    return `<span class="badge badge-success">🕒 On Time</span>`;
}

// Global Modal Management
function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    
    // Switch directly if another modal is open, without flickering scroll
    document.querySelectorAll('.modal-overlay.show').forEach(m => {
        if(m.id !== id) m.classList.remove('show');
    });
    
    modal.classList.add('show');
    document.body.classList.add('modal-open');
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('show');
    } else {
        document.querySelectorAll('.modal-overlay.show').forEach(m => m.classList.remove('show'));
    }
    
    // Delay check slightly to handle rapid transitions
    setTimeout(() => {
        if (!document.querySelector('.modal-overlay.show')) {
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        }
    }, 50);
}

function handleLoginSuccess() {
    console.log("🔓 Login successful, cleaning up UI...");
    document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('show'));
    document.body.style.overflow = '';
    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
}

// Basic Dark Mode
function toggleDark() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
}

// Counter animation
function initCounters() {
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseFloat(el.dataset.counter) || 0;
        const suffix = el.dataset.suffix || '';
        const isFloat = el.id === 'heroSatisfaction' || el.id === 'heroResolved';
        
        if (target === 0) {
            el.innerText = (isFloat ? "0.0" : "0") + suffix;
            return;
        }

        let count = 0;
        const inc = target / 50;
        const timer = setInterval(() => {
            count += inc;
            if (count >= target) {
                el.innerText = (isFloat ? target.toFixed(1) : Math.floor(target)) + suffix;
                clearInterval(timer);
            } else {
                el.innerText = (isFloat ? count.toFixed(1) : Math.floor(count)) + suffix;
            }
        }, 30);
    });
}

function renderDummyMap(id, points = [], interactive = false) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '<div style="width:100%;height:100%;background:rgba(0,0,0,0.03);display:flex;align-items:center;justify-content:center;color:var(--text-light);font-family:var(--font-main);border:2px dashed var(--border);border-radius:var(--radius-md)">[ Interactive Map Component ]</div>';
}
