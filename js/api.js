// Enhanced API wrapper with robust token refresh mechanism
const API_BASE_URL = (() => {
    const { hostname, protocol, port } = window.location;
    // If we're on a local dev server (Live Server, Vite, etc.) or file system
    if (protocol === 'file:' || 
        hostname === 'localhost' || 
        hostname === '127.0.0.1' || 
        hostname.startsWith('192.168.') || 
        (port && port !== '8000')) {
        return 'http://localhost:8000';
    }
    return ''; // Relative path for production
})();
window.API_BASE_URL = API_BASE_URL; // For compatibility with other scripts

class JanSamadhanAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    // Enhanced token refresh with retry mechanism
    async _fetch(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultHeaders = {
            "Content-Type": "application/json",
        };

        // Get user from storage with safety checks
        let user = null;
        try {
            const userRaw = sessionStorage.getItem('js_user') || localStorage.getItem('js_user');
            if (userRaw) {
                user = JSON.parse(userRaw);
                
                // Safety check: ensure user object has required structure
                if (!user || typeof user !== 'object') {
                    console.warn('Invalid user object structure, clearing storage');
                    sessionStorage.removeItem('js_user');
                    localStorage.removeItem('js_user');
                    user = null;
                }
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
            // Clear corrupted data
            sessionStorage.removeItem('js_user');
            localStorage.removeItem('js_user');
            user = null;
        }

        // Add auth header if user exists and has valid token
        if (user && user.token && typeof user.token === 'string') {
            defaultHeaders.Authorization = `Bearer ${user.token}`;
        }

        const config = {
            ...options,
            headers: { ...defaultHeaders, ...options.headers },
        };

        // Add retry flag to prevent infinite loops
        if (!config._retry) {
            config._retry = 0;
        }

        // Safety check: prevent infinite retry loops
        if (config._retry > 1) {
            console.error('Maximum retry attempts exceeded');
            throw new Error('Maximum retry attempts exceeded');
        }

        try {
            const response = await fetch(url, config);
            let data;

            try {
                data = await response.json();
            } catch (e) {
                console.error("Failed to parse JSON response:", e);
                throw new Error(`Invalid response from server (${response.status})`);
            }

            console.log(`📨 ${options.method || 'GET'} ${endpoint} → ${response.status}`, data);

            // Handle token expiration with improved detection
            if (response.status === 401 && config._retry === 0) {
                const errorCode = data.error?.code || data.code;
                const errorMessage = data.error?.message || data.message;
                
                if (errorCode === 'TOKEN_EXPIRED' || errorMessage?.includes('expired')) {
                    console.log('🔄 Token expired, attempting refresh...');
                    
                    // Safety check: ensure user has refresh token
                    if (!user || !user.refresh_token) {
                        console.error('❌ No refresh token available');
                        this.redirectToLogin();
                        return;
                    }
                    
                    const refreshToken = user.refresh_token;
                    
                    // Validate refresh token format
                    if (!refreshToken || typeof refreshToken !== 'string' || refreshToken.split('.').length !== 3) {
                        console.error('❌ Invalid refresh token format');
                        this.redirectToLogin();
                        return;
                    }
                    
                    console.log('🔄 Using refresh token to get new access token...');
                    
                    try {
                        const newTokens = await this.refreshAccessToken(refreshToken);
                        
                        if (newTokens && newTokens.token && newTokens.refresh_token) {
                            console.log('✅ Token refresh successful');
                            
                            // Update user object with new tokens
                            user = { ...user, ...newTokens };
                            
                            // Update storage with error handling
                            try {
                                const userData = JSON.stringify(user);
                                sessionStorage.setItem('js_user', userData);
                                localStorage.setItem('js_user', userData);
                            } catch (storageError) {
                                console.error('Failed to store updated user data:', storageError);
                            }
                            
                            // Retry original request with new token
                            console.log('🔄 Retrying original request...');
                            config._retry = 1;
                            config.headers.Authorization = `Bearer ${newTokens.token}`;
                            
                            return this._fetch(endpoint, config);
                        } else {
                            console.error('❌ Token refresh failed: No tokens returned');
                            this.redirectToLogin();
                            return;
                        }
                    } catch (refreshError) {
                        console.error('❌ Token refresh failed:', refreshError);
                        this.redirectToLogin();
                        return;
                    }
                }
            }

            // Check for other errors
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
            
            // If this is a network error and we haven't retried yet, try once more
            if (err.message.includes('fetch') && config._retry === 0) {
                console.log('🔄 Network error, retrying once...');
                config._retry = 1;
                return this._fetch(endpoint, config);
            }
            
            throw err;
        }
    }

    // Helper method for login redirect
    redirectToLogin() {
        console.log('🔄 Redirecting to login due to authentication failure');
        sessionStorage.setItem('redirect_after_login', window.location.pathname);
        window.location.href = 'index.html';
    }

    // Enhanced refresh token method
    async refreshAccessToken(refreshToken) {
        try {
            const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                console.log('✅ Token refresh successful');
                return data.data;
            } else {
                console.error('❌ Token refresh failed:', data);
                return null;
            }
        } catch (err) {
            console.error('❌ Token refresh error:', err);
            return null;
        }
    }

    // API Methods
    async register(userData) {
        return this._fetch('/api/auth/register', { method: 'POST', body: JSON.stringify(userData) });
    }

    async registerNGO(ngoData) {
        return this._fetch('/api/auth/register-ngo', { method: 'POST', body: JSON.stringify(ngoData) });
    }

    async login(credentials) {
        const result = await this._fetch('/api/auth/login', { method: 'POST', body: JSON.stringify(credentials) });
        
        // Store tokens in both storages for reliability
        if (result && result.token) {
            const userData = JSON.stringify(result);
            localStorage.setItem('js_user', userData);
            sessionStorage.setItem('js_user', userData);
        }
        
        return result;
    }

    async adminLogin(credentials) {
        console.log("🔐 Attempting Admin Login via:", `${this.baseURL}/api/auth/admin-login`);
        // Admin login uses the dedicated admin-login endpoint
        const result = await this._fetch('/api/auth/admin-login', { method: 'POST', body: JSON.stringify(credentials) });
        
        // Store tokens in both storages for reliability
        if (result && result.token) {
            const userData = JSON.stringify(result);
            localStorage.setItem('js_user', userData);
            sessionStorage.setItem('js_user', userData);
        }
        
        return result;
    }

    async logout() {
        try {
            await this._fetch('/api/auth/logout', { method: 'POST' });
        } catch (err) {
            console.warn('Logout API call failed:', err);
        } finally {
            // Always clear local storage on logout
            localStorage.removeItem('js_user');
            sessionStorage.removeItem('js_user');
        }
    }

    async getUser() {
        return this._fetch('/api/auth/user');
    }

    async getComplaints(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this._fetch(`/api/complaints${queryString ? '?' + queryString : ''}`);
    }

    async getComplaint(id) {
        return this._fetch(`/api/complaints/${id}`);
    }

    async createComplaint(complaintData) {
        return this._fetch('/api/complaints/', { 
            method: 'POST', 
            body: JSON.stringify(complaintData) 
        });
    }

    async updateComplaint(id, updateData) {
        return this._fetch(`/api/complaints/${id}`, { 
            method: 'PUT', 
            body: JSON.stringify(updateData) 
        });
    }

    async deleteComplaint(id) {
        return this._fetch(`/api/complaints/${id}`, { method: 'DELETE' });
    }

    // Enhanced features
    async voteComplaint(id, voteType) {
        return this._fetch(`/api/complaints/${id}/vote?vote_type=${voteType}`, { method: 'POST' });
    }

    async commentComplaint(id, comment) {
        const formData = new FormData();
        formData.append('comment', comment);
        return this._fetch(`/api/complaints/${id}/comment`, { 
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }

    async getComplaintComments(id, skip = 0, limit = 50) {
        return this._fetch(`/api/complaints/${id}/comments?skip=${skip}&limit=${limit}`);
    }

    async uploadMedia(files) {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        
        return this._fetch('/api/complaints/with-media', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }

    async deleteMedia(publicId) {
        return this._fetch(`/api/complaints/media/${publicId}`, { method: 'DELETE' });
    }

    // Analytics endpoints
    async getPredictions(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this._fetch(`/api/analytics/predictions${queryString ? '?' + queryString : ''}`);
    }

    async getResolutionPredictions(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this._fetch(`/api/analytics/resolution-time-predictions${queryString ? '?' + queryString : ''}`);
    }

    // Public endpoints
    async getPublicStats() {
        return this._fetch('/api/public/stats');
    }

    async getPublicHeatmap(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this._fetch(`/api/public/heatmap${queryString ? '?' + queryString : ''}`);
    }

    async getPublicTrends(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this._fetch(`/api/public/trends${queryString ? '?' + queryString : ''}`);
    }


    // Aliases for frontend compatibility
    async getAnalytics() {
        return this.getPublicStats();
    }
    
    async getNotices(role = null) {
        // If no role provided, try to detect from session
        if (!role) {
            const user = JSON.parse(localStorage.getItem('js_user') || '{}');
            role = user.role || 'citizen';
        }
        return this._fetch(`/api/public/notices?role=${role}`);
    }
    
    async getGrievanceByID(id) {
        return this.getComplaint(id);
    }


    async getNGOUploadUrl(fileName, fileType) {
        return this._fetch(`/api/auth/ngo-upload-url?file_name=${encodeURIComponent(fileName)}&file_type=${encodeURIComponent(fileType)}`);
    }

    async uploadFileDirectly(file) {
        const data = await this.getNGOUploadUrl(file.name, file.type);
        
        // Handle Local Fallback
        if (data.use_local) {
            const formData = new FormData();
            formData.append('file', file);
            // Use the endpoint provided by the server, prefix with base URL
            const res = await this._fetch(data.endpoint, {
                method: 'POST',
                body: formData
            });
            // If backend returns absolute URL, use it, else prefix with server host
            return res.file_url.startsWith('http') ? res.file_url : `${API_BASE_URL}${res.file_url}`;
        }

        // Standard S3 Upload
        const { url, fields, file_url } = data;
        const formData = new FormData();
        Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
        formData.append('file', file);

        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error("Cloud storage upload failed.");
        return file_url;
    }

    async createGrievance(grievanceData) {
        return this._fetch('/api/complaints/', { method: 'POST', body: JSON.stringify(grievanceData) });
    }

    async getMyGrievances(status = null, priority = null, skip = 0, limit = 50) {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        params.append('skip', skip);
        params.append('limit', limit);
        return this._fetch(`/api/complaints/my?${params}`);
    }

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
    }

    async getGeoComplaintData(region = null, category = null, priority = null, limit = 1000) {
        const params = new URLSearchParams();
        if (region) params.append('region', region);
        if (category) params.append('category', category);
        if (priority) params.append('priority', priority);
        params.append('limit', String(limit));
        return this._fetch(`/api/complaints/geo-data?${params}`);
    }

    async getAssignedGrievances(status = null, priority = null, skip = 0, limit = 50) {
        const params = new URLSearchParams();
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        params.append('skip', skip);
        params.append('limit', limit);
        return this._fetch(`/api/complaints/assigned?${params}`);
    }

    async regenerateGrievanceSummary(id) {
        return this._fetch(`/api/complaints/${id}/generate-summary`, { method: 'POST' });
    }

    async assignComplaint(id, officerEmail) {
        return this._fetch(`/api/complaints/${id}/assign?officer_email=${officerEmail}`, { method: 'PATCH' });
    }

    async updateGrievanceStatus(id, status, remarks = '') {
        const params = new URLSearchParams({ status, remarks });
        return this._fetch(`/api/complaints/${id}/status?${params}`, { method: 'PATCH' });
    }

    async submitFeedback(id, rating, comment = '') {
        const params = new URLSearchParams({ rating, comment });
        return this._fetch(`/api/complaints/${id}/feedback?${params}`, { method: 'PATCH' });
    }

    async addNotice(noticeData) {
        // noticeData can be an object or FormData
        if (noticeData instanceof FormData) {
            return this._fetch('/api/admin/notices', { 
                method: 'POST', 
                body: noticeData,
                headers: {} // Browser will set correct multipart boundary
            });
        }
        return this._fetch('/api/admin/notices', { method: 'POST', body: JSON.stringify(noticeData) });
    }

    async deleteNotice(id) {
        return this._fetch(`/api/admin/notices/${id}`, { method: 'DELETE' });
    }

    async createUser(userData) {
        return this._fetch('/api/admin/users', { method: 'POST', body: JSON.stringify(userData) });
    }

    async getAdminAnalytics() {
        return this._fetch('/api/admin/analytics');
    }

    async toggleUserVerification(email) {
        return this._fetch(`/api/admin/users/${email}/verify`, { method: 'PATCH' });
    }

    async getAllUsers() {
        return this._fetch('/api/admin/users');
    }

    async governmentVerifyUser(email) {
        return this._fetch(`/api/admin/users/${email}/verify-government`, { method: 'POST' });
    }

    async getAuditLog(actorEmail = null, action = null, limit = 100) {
        const params = new URLSearchParams();
        if (actorEmail) params.append('actor_email', actorEmail);
        if (action) params.append('action', action);
        params.append('limit', limit);
        return this._fetch(`/api/admin/audit-log?${params}`);
    }

    async requestComplaint(id) {
        return this._fetch('/api/ngo/requests', {
            method: 'POST',
            body: JSON.stringify({ complaint_id: id })
        });
    }

    async getMyNGORequests() {
        return this._fetch('/api/ngo/my-requests');
    }

    async getNGOAssignedComplaints() {
        return this._fetch('/api/ngo/assigned-complaints');
    }

    async getNGOAvailableComplaints() {
        return this._fetch('/api/ngo/available-complaints');
    }

    async getNGOStats() {
        return this._fetch('/api/ngo/stats');
    }

    async getNGOProfile() {
        return this._fetch('/api/ngo/profile');
    }

    async updateNGOProfile(data) {
        return this._fetch('/api/ngo/profile', { method: 'PATCH', body: JSON.stringify(data) });
    }

    async getAdminNGORequests(status = 'pending') {
        return this._fetch(`/api/admin/ngo-requests?status=${status}`);
    }

    async approveNGORequest(requestId) {
        return this._fetch(`/api/admin/ngo-requests/${requestId}/approve`, { method: 'PATCH' });
    }

    async rejectNGORequest(requestId, remarks = '') {
        return this._fetch(`/api/admin/ngo-requests/${requestId}/reject?remarks=${remarks}`, { method: 'PATCH' });
    }

    async getPendingNGOs() {
        return this._fetch('/api/admin/ngo/pending');
    }

    async approveNGO(email) {
        return this._fetch(`/api/admin/ngo/${email}/approve`, { method: 'PATCH' });
    }

    async rejectNGO(email, reason) {
        return this._fetch(`/api/admin/ngo/${email}/reject?reason=${encodeURIComponent(reason)}`, { method: 'PATCH' });
    }

    async uploadEvidence(complaintId, file) {
        const formData = new FormData();
        formData.append('file', file);
        return this._fetch(`/api/complaints/${complaintId}/upload-media`, {
            method: 'POST',
            body: formData
        });
    }

    async getTranslations(lang = 'en') {
        return this._fetch(`/api/translations/${encodeURIComponent(lang)}`);
    }

    async chatbotQuery(query) {
        return this._fetch('/api/chatbot/query', {
            method: 'POST',
            body: JSON.stringify({ query })
        });
    }

    async getNextComplaints(limit = 10) {
        return this._fetch(`/api/complaints/next?limit=${limit}`);
    }

    async escalateComplaint(id, remarks = '') {
        const params = new URLSearchParams();
        if (remarks) params.append('remarks', remarks);
        return this._fetch(`/api/complaints/${id}/escalate?${params.toString()}`, { method: 'POST' });
    }

    async getAnalyticsOverview(days = 30) {
        return this._fetch(`/api/analytics/overview?days=${days}`);
    }

    async getAnalyticsTrends(days = 30) {
        return this._fetch(`/api/analytics/trends?days=${days}`);
    }

    async generateReport(payload = {}) {
        return this._fetch('/api/reports/generate', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }
}

// Create global API instance
window.JanSamadhanAPI = new JanSamadhanAPI();

// Storage event listener for cross-tab synchronization
window.addEventListener('storage', (event) => {
    if (event.key === 'js_user') {
        // Update local user data when it changes in another tab
        const userData = event.newValue;
        if (userData) {
            try {
                const user = JSON.parse(userData);
                console.log('🔄 User data updated from another tab');
                // You can trigger any UI updates here if needed
            } catch (e) {
                console.error('❌ Failed to parse user data from storage event:', e);
            }
        }
    }
});

// Auto-refresh token before expiry (optional enhancement)
function scheduleTokenRefresh() {
    const userRaw = localStorage.getItem('js_user') || sessionStorage.getItem('js_user');
    if (!userRaw) return;
    
    try {
        const user = JSON.parse(userRaw);
        if (!user.token) return;
        
        // Parse token to get expiry
        const tokenParts = user.token.split('.');
        if (tokenParts.length !== 3) return;
        
        const payload = JSON.parse(atob(tokenParts[1]));
        const expiryTime = payload.exp * 1000; // Convert to milliseconds
        const currentTime = Date.now();
        const timeUntilExpiry = expiryTime - currentTime;
        
        // Refresh 5 minutes before expiry
        const refreshTime = timeUntilExpiry - (5 * 60 * 1000);
        
        if (refreshTime > 0) {
            setTimeout(async () => {
                console.log('🔄 Auto-refreshing token before expiry');
                try {
                    const api = window.JanSamadhanAPI;
                    const newTokens = await api.refreshAccessToken(user.refresh_token);
                    if (newTokens) {
                        console.log('✅ Auto token refresh successful');
                    }
                } catch (e) {
                    console.error('❌ Auto token refresh failed:', e);
                }
            }, refreshTime);
        }
    } catch (e) {
        console.error('❌ Failed to schedule token refresh:', e);
    }
}

// Schedule refresh on page load
window.JanSamadhanAPI = new JanSamadhanAPI();
scheduleTokenRefresh();
