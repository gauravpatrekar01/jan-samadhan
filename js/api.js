// JanSamadhan: REST API Service connecting to Python Backend
console.log("🚀 JanSamadhan: API Service Loading...");

// Determine API base URL - handle both local file:// and http:// serving
const API_BASE_URL = (() => {
    if (!window.location.hostname || window.location.hostname === '') {
        // Local file (file://) - default to localhost:8000
        return 'http://localhost:8000';
    }
    // Normal web serving - use current hostname
    return `http://${window.location.hostname}:8000`;
})();

console.log("📡 API Base URL:", API_BASE_URL);

const JanSamadhanAPI = {
    async _fetch(endpoint, options = {}) {
        // Token is stored under 'js_user' as part of the user object
        const userRaw = sessionStorage.getItem('js_user') || localStorage.getItem('js_user');
        const token = userRaw ? JSON.parse(userRaw).token : null;

        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers: { ...headers, ...options.headers }
            });

            let data;
            try {
                data = await response.json();
            } catch (e) {
                console.error("Failed to parse JSON response:", e);
                throw new Error(`Invalid response from server (${response.status})`);
            }

            console.log(`📨 ${options.method || 'GET'} ${endpoint} → ${response.status}`, data);

            // Handle token expiration (401 with TOKEN_EXPIRED code)
            if (response.status === 401 && data.error?.code === 'TOKEN_EXPIRED') {
                const refreshToken = userRaw ? JSON.parse(userRaw).refresh_token : null;
                if (refreshToken) {
                    const newTokens = await this.refreshAccessToken(refreshToken);
                    if (newTokens) {
                        // Retry original request with new token
                        const user = JSON.parse(sessionStorage.getItem('js_user') || localStorage.getItem('js_user'));
                        user.token = newTokens.token;
                        user.refresh_token = newTokens.refresh_token;
                        sessionStorage.setItem('js_user', JSON.stringify(user));
                        localStorage.setItem('js_user', JSON.stringify(user));
                        return this._fetch(endpoint, options);
                    }
                }
                // Refresh failed, redirect to login
                window.location.href = 'index.html';
                return;
            }

            // Check for errors
            if (!response.ok) {
                const errorMsg = data.detail ||
                    data.error?.message ||
                    data.message ||
                    `Request failed: ${response.status}`;
                console.error("❌ API Error:", errorMsg, data);
                throw new Error(errorMsg);
            }

            // If response has success: false, treat as error
            if (data.success === false) {
                const errorMsg = data.error?.message || data.message || "Request failed";
                console.error("❌ API Error (success=false):", errorMsg, data);
                throw new Error(errorMsg);
            }

            // Return the data payload
            const result = data.data !== undefined ? data.data : data;
            return result;
        } catch (err) {
            console.error("🔥 Fetch error:", err);
            throw err;
        }
    },

    async refreshAccessToken(refreshToken) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            const data = await response.json();
            if (data.success) {
                return data.data;
            }
            return null;
        } catch (err) {
            console.error('Token refresh failed:', err);
            return null;
        }
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
            localStorage.setItem('js_user', JSON.stringify(response));
        }
        return response;
    },

    async adminLogin(credentials) {
        const response = await this._fetch('/api/auth/admin-login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
        if (response && response.token) {
            sessionStorage.setItem('js_user', JSON.stringify(response));
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

    async getMyGrievances(status = null, priority = null, skip = 0, limit = 50) {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        params.append('skip', skip);
        params.append('limit', limit);
        return this._fetch(`/api/complaints/my?${params}`);
    },

    async getAllGrievances(status = null, priority = null, category = null, region = null, search = null, skip = 0, limit = 50) {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        if (category) params.append('category', category);
        if (region) params.append('region', region);
        if (search) params.append('search', search);
        params.append('skip', skip);
        params.append('limit', limit);
        return this._fetch(`/api/complaints/?${params}`);
    },

    async getAssignedGrievances(status = null, priority = null, skip = 0, limit = 50) {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        params.append('skip', skip);
        params.append('limit', limit);
        return this._fetch(`/api/complaints/assigned?${params}`);
    },

    async getGrievanceByID(id) {
        return this._fetch(`/api/complaints/${id}`);
    },

    async assignComplaint(id, officerEmail) {
        return this._fetch(`/api/complaints/${id}/assign?officer_email=${officerEmail}`, { method: 'PATCH' });
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

    async createUser(userData) {
        return this._fetch('/api/admin/users', { method: 'POST', body: JSON.stringify(userData) });
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
    },

    async governmentVerifyUser(email) {
        return this._fetch(`/api/admin/users/${email}/verify-government`, { method: 'POST' });
    },

    async getAuditLog(actorEmail = null, action = null, limit = 100) {
        const params = new URLSearchParams();
        if (actorEmail) params.append('actor_email', actorEmail);
        if (action) params.append('action', action);
        params.append('limit', limit);
        return this._fetch(`/api/admin/audit-log?${params}`);
    }
};

window.JanSamadhanAPI = JanSamadhanAPI;
