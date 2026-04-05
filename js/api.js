// JanSamadhan: REST API Service connecting to Python Backend
console.log("🚀 JanSamadhan: API Service Loading...");

const API_BASE_URL = `http://${window.location.hostname}:8000`;

const JanSamadhanAPI = {
    async _fetch(endpoint, options = {}) {
        // Token is stored under 'js_user' as part of the user object
        const userRaw = sessionStorage.getItem('js_user') || localStorage.getItem('js_user');
        const token = userRaw ? JSON.parse(userRaw).token : null;

        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: { ...headers, ...options.headers }
        });

        const data = await response.json();

        if (!response.ok || data.success === false) {
            throw new Error(
                data.detail ||
                data.message ||
                (data.error && data.error.message) ||
                `Request failed (${response.status})`
            );
        }

        return data.data !== undefined ? data.data : data;
    },

    async register(userData) {
        return this._fetch('/api/auth/register', { method: 'POST', body: JSON.stringify(userData) });
    },

    async login(credentials) {
        const response = await this._fetch('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
        if (response && response.token) {
            sessionStorage.setItem('js_user', JSON.stringify(response));
            // Keep localStorage in sync for pages that read from it
            localStorage.setItem('js_user', JSON.stringify(response));
        }
        return response;
    },

    logout() {
        sessionStorage.removeItem('js_user');
        localStorage.removeItem('js_user');
    },

    async createGrievance(grievanceData) {
        return this._fetch('/api/complaints/', { method: 'POST', body: JSON.stringify(grievanceData) });
    },

    async getMyGrievances() {
        return this._fetch('/api/complaints/my');
    },

    async getAllGrievances() {
        return this._fetch('/api/complaints/');
    },

    async getAssignedGrievances() {
        return this._fetch('/api/complaints/assigned');
    },

    async getGrievanceByID(id) {
        return this._fetch(`/api/complaints/${id}`);
    },

    async updateGrievanceStatus(id, status, remarks = '') {
        const params = new URLSearchParams({ status, remarks });
        return this._fetch(`/api/complaints/${id}/status?${params}`, { method: 'PATCH' });
    },

    async submitFeedback(id, rating, comment = '') {
        const params = new URLSearchParams({ rating, comment });
        return this._fetch(`/api/complaints/${id}/feedback?${params}`, { method: 'PATCH' });
    },

    async addNotice(notice) {
        return this._fetch('/api/admin/notices', { method: 'POST', body: JSON.stringify(notice) });
    },

    async getNotices() {
        return this._fetch('/api/admin/notices');
    },

    async deleteNotice(id) {
        return this._fetch(`/api/admin/notices/${id}`, { method: 'DELETE' });
    },

    /**
     * Public stats — used by the landing page KPI cards.
     * Hits /api/stats which requires NO authentication.
     * Falls back to zeros on error so the page still loads.
     */
    async getAnalytics() {
        try {
            return await this._fetch('/api/stats');
        } catch (err) {
            console.warn('Public stats endpoint failed:', err);
            return {
                total_complaints: 0,
                resolved_complaints: 0,
                resolution_rate: 0,
                pending: 0,
                emergency: 0,
                high: 0,
                status_distribution: { submitted: 0 },
                priority_distribution: { emergency: 0, high: 0 }
            };
        }
    },

    /**
     * Admin-only full analytics — requires admin JWT.
     * Used by the admin dashboard only.
     */
    async getAdminAnalytics() {
        return this._fetch('/api/admin/analytics');
    },

    async toggleUserVerification(email) {
        return this._fetch(`/api/admin/users/${email}/verify`, { method: 'PATCH' });
    },

    async getAllUsers() {
        return this._fetch('/api/admin/users');
    }
};

window.JanSamadhanAPI = JanSamadhanAPI;
