// Enhanced API wrapper with robust token refresh mechanism
const API_BASE_URL = (() => {
    if (window.JS_API_BASE_URL) return window.JS_API_BASE_URL;
    const { hostname, protocol, port } = window.location;
    // Local development fallbacks
    if (protocol === 'file:') return 'http://127.0.0.1:8000';
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        if (port && port !== '8000') return `http://${hostname}:8000`;
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
        const defaultHeaders = {};
        if (!(options.body instanceof FormData)) {
            defaultHeaders["Content-Type"] = "application/json";
        }

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
                const errorMsg = data.detail?.error?.message || data.detail?.message || data.error?.message || data.message || `Request failed: ${response.status}`;
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
        if (grievanceData instanceof FormData) {
            return this._fetch('/api/complaints/with-media', { method: 'POST', body: grievanceData });
        }
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

    async voteGrievance(id, type = 'up') {
        return this._fetch(`/api/complaints/${id}/vote?vote_type=${type}`, { method: 'POST' });
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

    async generateTransientSummary(id, lang = null) {
        const url = `/api/complaints/${id}/generate-view-summary${lang ? `?target_language=${lang}` : ''}`;
        return this._fetch(url, { method: 'POST' });
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
        return this._fetch(`/api/admin/audit-logs?${params}`);
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

    async getNGOAllGrievances(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/api/ngo/all-grievances${qs ? '?' + qs : ''}`);
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
        return this._fetch('/api/chatbot/generate', {
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

    async getAdminAnalyticsOverview(days = 30) {
        return this._fetch(`/api/analytics/admin/overview?days=${days}`);
    }

    async getAnalyticsTrends(days = 30) {
        return this._fetch(`/api/analytics/trends?days=${days}`);
    }

    async getOfficerPerformance(officerId) {
        return this._fetch(`/api/analytics/officer/${officerId}/performance`);
    }

    async getAdminOfficerPerformance(limit = 20) {
        return this._fetch(`/api/analytics/admin/officer-performance?limit=${limit}`);
    }

    async getOfficerQueue(officerId) {
        return this._fetch(`/api/analytics/officer/${officerId}/queue`);
    }

    async getAdminPeakTimes() {
        return this._fetch('/api/analytics/admin/peak-times');
    }

    async getAdminNGOContribution() {
        return this._fetch('/api/analytics/admin/ngo-contribution');
    }

    async getAdminEscalationAdvanced() {
        return this._fetch('/api/analytics/admin/escalation-advanced');
    }

    async getFilteredAnalytics(filters) {
        return this._fetch('/api/analytics/filtered', {
            method: 'POST',
            body: JSON.stringify(filters)
        });
    }

    async exportAnalytics(filters, format = 'csv') {
        return this._fetch('/api/analytics/export', {
            method: 'POST',
            body: JSON.stringify({ filters, format })
        });
    }

    async generateReport(payload = {}) {
        return this._fetch('/api/reports/generate', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    // ── Project Module Endpoints ──
    async requestProjectConversion(complaintId, data) {
        const params = new URLSearchParams({ complaint_id: complaintId, ...data });
        return this._fetch(`/api/projects/project-conversion/request?${params}`, { method: 'POST' });
    }

    async getPendingProjectConversions() {
        return this._fetch('/api/projects/project-conversion/pending');
    }

    async approveProjectConversion(complaintId, remarks = '') {
        return this._fetch(`/api/projects/project-conversion/approve?complaint_id=${complaintId}&admin_remarks=${remarks}`, { method: 'POST' });
    }

    async rejectProjectConversion(complaintId, reason) {
        return this._fetch(`/api/projects/project-conversion/reject?complaint_id=${complaintId}&reason=${reason}`, { method: 'POST' });
    }

    async getProjects() {
        return this._fetch('/api/projects/');
    }

    async getProject(projectId) {
        return this._fetch(`/api/projects/${projectId}`);
    }

    async updateProject(projectId, data) {
        return this._fetch(`/api/projects/${projectId}/update`, { method: 'PUT', body: JSON.stringify(data) });
    }

    async addProjectMilestone(projectId, milestone) {
        return this._fetch(`/api/projects/milestone?project_id=${projectId}`, { method: 'POST', body: JSON.stringify(milestone) });
    }

    async addProjectProgressUpdate(update) {
        return this._fetch('/api/projects/progress-update', { method: 'POST', body: JSON.stringify(update) });
    }

    async requestDeadlineExtension(extensionRequest) {
        return this._fetch('/api/projects/request-extension', { method: 'POST', body: JSON.stringify(extensionRequest) });
    }

    async getPendingExtensions() {
        return this._fetch('/api/projects/pending-extensions');
    }

    async approveExtension(requestId) {
        return this._fetch(`/api/projects/approve-extension?request_id=${requestId}`, { method: 'POST' });
    }

    async rejectExtension(requestId, reason) {
        return this._fetch(`/api/projects/reject-extension?request_id=${requestId}&reason=${reason}`, { method: 'POST' });
    }

    async getExtensionHistory(projectId) {
        return this._fetch(`/api/projects/extension-history/${projectId}`);
    }

    async getAIReport(id, refresh = false) {
        return this._fetch(`/api/complaints/${id}/ai-report?refresh=${refresh}`);
    }

    async generateAIReport(id, refresh = false) {
        return this._fetch(`/api/complaints/${id}/ai-report/generate?refresh=${refresh}`, { method: 'POST' });
    }

    async reopenComplaint(id, reason) {
        return this._fetch(`/api/complaints/${id}/reopen`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    async extendDeadline(id, newDueDate, reason) {
        return this._fetch(`/api/complaints/${id}/extend-deadline`, {
            method: 'POST',
            body: JSON.stringify({ new_due_date: newDueDate, reason })
        });
    }

    async deleteComplaint(id) {
        return this._fetch(`/api/complaints/${id}`, {
            method: 'DELETE'
        });
    }
}

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

// ── AI INTELLIGENCE PANEL UI RENDERER & ACTIONS ──
window.renderAIIntelligencePanel = function(g, userRole) {
    if (!g) return '';
    const id = g.id || g.grievanceID || g._id;
    const aiReport = g.ai_report;
    const hasReport = !!aiReport;
    
    // Check role permissions for refresh
    const canRefresh = (userRole === 'officer' || userRole === 'admin');
    
    let html = `
    <div class="ai-intelligence-panel" style="margin-top:20px;margin-bottom:20px;border:1px solid rgba(37,99,235,0.15);border-radius:12px;background:rgba(37,99,235,0.02);padding:18px;font-family:inherit;box-shadow:0 4px 12px rgba(37,99,235,0.03)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;border-bottom:1px dashed rgba(37,99,235,0.15);padding-bottom:10px">
            <h4 style="margin:0;color:var(--primary-light);font-size:1rem;display:flex;align-items:center;gap:8px">
                <span style="font-size:1.2rem">🤖</span> AI Intelligence Insights
            </h4>
            <div style="display:flex;gap:8px;align-items:center">
    `;
    
    if (!hasReport) {
        html += `
                <button id="btn-generate-ai-report" class="btn btn-primary btn-sm" onclick="handleGenerateAIReport('${id}')" style="display:flex;align-items:center;gap:6px">
                    <span class="spinner-border spinner-border-sm" style="width:12px;height:12px;display:none" id="generate-ai-spinner"></span>
                    <span>Generate AI Report</span>
                </button>
        `;
    } else {
        html += `
                <button id="btn-toggle-ai-report" class="btn btn-outline btn-sm" onclick="toggleAIReportSection()" style="display:flex;align-items:center;gap:6px">
                    <span>👁️ View AI Report</span>
                </button>
        `;
        if (canRefresh) {
            html += `
                <button id="btn-refresh-ai-report" class="btn btn-ghost btn-sm" onclick="handleRefreshAIReport('${id}')" title="Regenerate/Overwrite Cached AI Report" style="background:rgba(0,0,0,0.03);border-radius:6px;display:flex;align-items:center;gap:6px">
                    <span class="spinner-border spinner-border-sm" style="width:12px;height:12px;display:none" id="refresh-ai-spinner"></span>
                    <span>🔄 Refresh</span>
                </button>
            `;
        }
    }
    
    html += `
            </div>
        </div>
    `;
    
    if (hasReport) {
        const severityColor = aiReport.severity_score >= 75 ? '#dc2626' : (aiReport.severity_score >= 40 ? '#d97706' : '#16a34a');
        const urgencyBg = aiReport.urgency_level === 'critical' ? '#7f1d1d' : (aiReport.urgency_level === 'high' ? '#991b1b' : (aiReport.urgency_level === 'medium' ? '#b45309' : '#14532d'));
        const urgencyColor = '#ffffff';
        const sentimentEmoji = aiReport.sentiment === 'highly_negative' ? 'Highly Negative' : (aiReport.sentiment === 'negative' ? 'Negative' : 'Neutral');
        
        // Render risk flags badges
        const getRiskColor = (risk) => risk === 'high' ? '#dc2626' : (risk === 'medium' ? '#d97706' : '#16a34a');
        const riskFlagsHtml = Object.entries(aiReport.risk_flags || {}).map(([key, val]) => `
            <div style="background:rgba(15,23,42,0.03);border:1px solid rgba(0,0,0,0.05);padding:8px 12px;border-radius:8px;text-align:center">
                <div style="font-size:0.68rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;letter-spacing:0.3px">${key.replace('_', ' ')}</div>
                <div style="font-size:0.85rem;font-weight:800;color:${getRiskColor(val)};margin-top:2px;text-transform:capitalize">${val}</div>
            </div>
        `).join('');
        
        // Render category validation
        const catMatch = (aiReport.category_validation?.user_category || '').toLowerCase() === (aiReport.category_validation?.ai_predicted_category || '').toLowerCase();
        const categoryValHtml = `
            <div style="display:flex;align-items:center;gap:10px;background:${catMatch ? 'rgba(22,163,74,0.05)' : 'rgba(220,38,38,0.05)'};border:1px solid ${catMatch ? 'rgba(22,163,74,0.1)' : 'rgba(220,38,38,0.1)'};padding:10px 14px;border-radius:8px;font-size:0.85rem;margin-bottom:12px">
                <span style="font-size:1.2rem">${catMatch ? '✅' : '⚠️'}</span>
                <div style="flex:1">
                    <div><strong>Category Match:</strong> ${catMatch ? 'Validated successfully' : 'Mismatch detected'}</div>
                    <div style="font-size:0.78rem;color:var(--text-muted);margin-top:2px">
                        Filed: <span style="text-decoration:underline">${aiReport.category_validation?.user_category || 'N/A'}</span> · 
                        AI Predicts: <strong style="color:${catMatch ? 'inherit' : 'var(--danger)'}">${aiReport.category_validation?.ai_predicted_category || 'N/A'}</strong> 
                        (Confidence: ${Math.round((aiReport.category_validation?.confidence || 0) * 100)}%)
                    </div>
                </div>
            </div>
        `;
        
        html += `
        <div id="ai-report-details-section" style="display:none;margin-top:10px">
            <div style="background:rgba(37,99,235,0.04);border-left:3px solid var(--primary-light);padding:12px 16px;border-radius:6px;margin-bottom:14px;font-size:0.88rem;line-height:1.5;color:var(--text)">
                <strong>Summary Insight:</strong> ${aiReport.summary_insight}
            </div>
            
            <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));gap:12px;margin-bottom:14px">
                <div style="background:#fff;border:1px solid rgba(0,0,0,0.05);padding:10px 12px;border-radius:10px;display:flex;flex-direction:column;justify-content:center;box-shadow:var(--shadow-sm)">
                    <span style="font-size:0.7rem;color:var(--text-muted);font-weight:700;text-transform:uppercase">Severity Score</span>
                    <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
                        <span style="font-size:1.4rem;font-weight:800;color:${severityColor}">${aiReport.severity_score}/100</span>
                        <div style="flex:1;background:rgba(0,0,0,0.05);height:6px;border-radius:3px;overflow:hidden">
                            <div style="background:${severityColor};width:${aiReport.severity_score}%;height:100%"></div>
                        </div>
                    </div>
                </div>
                
                <div style="background:#fff;border:1px solid rgba(0,0,0,0.05);padding:10px 12px;border-radius:10px;display:flex;flex-direction:column;justify-content:center;box-shadow:var(--shadow-sm)">
                    <span style="font-size:0.7rem;color:var(--text-muted);font-weight:700;text-transform:uppercase">Urgency Level</span>
                    <span style="background:${urgencyBg};color:${urgencyColor};padding:3px 8px;border-radius:6px;font-size:0.78rem;font-weight:800;text-transform:uppercase;align-self:flex-start;margin-top:6px;letter-spacing:0.5px">${aiReport.urgency_level}</span>
                </div>
                
                <div style="background:#fff;border:1px solid rgba(0,0,0,0.05);padding:10px 12px;border-radius:10px;display:flex;flex-direction:column;justify-content:center;box-shadow:var(--shadow-sm)">
                    <span style="font-size:0.7rem;color:var(--text-muted);font-weight:700;text-transform:uppercase">Sentiment</span>
                    <span style="font-size:0.85rem;font-weight:700;margin-top:6px;color:#1e293b">${sentimentEmoji}</span>
                </div>
            </div>
            
            <div style="display:grid;grid-template-columns:1fr 1.2fr;gap:14px;margin-bottom:14px">
                <div>
                    <h5 style="margin:0 0 8px 0;font-size:0.8rem;text-transform:uppercase;color:var(--text-muted);letter-spacing:0.3px">Risk Profiling</h5>
                    <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:8px">
                        ${riskFlagsHtml}
                    </div>
                </div>
                <div>
                    <h5 style="margin:0 0 8px 0;font-size:0.8rem;text-transform:uppercase;color:var(--text-muted);letter-spacing:0.3px">Routing & Recommended Dept</h5>
                    <div style="background:#fff;border:1px solid rgba(0,0,0,0.05);padding:12px;border-radius:10px;box-shadow:var(--shadow-sm)">
                        <div style="font-size:0.9rem;font-weight:800;color:var(--primary-light)">🏫 ${aiReport.recommended_department || 'General Administration'}</div>
                        <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px">Assigned Region: 📍 ${aiReport.entity_extraction?.location || 'Unknown'}</div>
                    </div>
                </div>
            </div>
            
            ${categoryValHtml}
            
            <div style="display:grid;grid-template-columns:1.2fr 1fr;gap:14px">
                <div>
                    <h5 style="margin:0 0 8px 0;font-size:0.8rem;text-transform:uppercase;color:var(--text-muted);letter-spacing:0.3px">Suggested Actions</h5>
                    <ul style="margin:0;padding-left:18px;font-size:0.82rem;line-height:1.6;color:var(--text)">
                        ${(aiReport.suggested_actions || []).map(action => `<li style="margin-bottom:4px">${action}</li>`).join('')}
                    </ul>
                </div>
                <div>
                    <h5 style="margin:0 0 8px 0;font-size:0.8rem;text-transform:uppercase;color:var(--text-muted);letter-spacing:0.3px">Extracted Keywords</h5>
                    <div style="display:flex;flex-wrap:wrap;gap:6px">
                        ${(aiReport.entity_extraction?.keywords || []).map(kw => `<span style="background:rgba(0,0,0,0.04);border:1px solid rgba(0,0,0,0.05);color:var(--text);padding:3px 8px;border-radius:6px;font-size:0.75rem;font-weight:600">🏷️ ${kw}</span>`).join('') || '<span style="font-size:0.8rem;color:var(--text-muted)">None</span>'}
                    </div>
                    ${aiReport.entity_extraction?.organizations?.length ? `
                    <h5 style="margin:8px 0 8px 0;font-size:0.8rem;text-transform:uppercase;color:var(--text-muted);letter-spacing:0.3px">Organizations</h5>
                    <div style="display:flex;flex-wrap:wrap;gap:6px">
                        ${aiReport.entity_extraction.organizations.map(org => `<span style="background:rgba(37,99,235,0.05);border:1px solid rgba(37,99,235,0.1);color:var(--primary-light);padding:3px 8px;border-radius:6px;font-size:0.75rem;font-weight:600">🏢 ${org}</span>`).join('')}
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <div style="text-align:right;font-size:0.7rem;color:var(--text-muted);margin-top:14px;border-top:1px solid rgba(0,0,0,0.05);padding-top:8px">
                Report generated: 📅 ${new Date(aiReport.generated_at).toLocaleString('en-IN')} · Version ${aiReport.version}
            </div>
        </div>
        `;
    }
    
    html += `
    </div>
    `;
    
    return html;
};

// Global click/toggle handlers
window.toggleAIReportSection = function() {
    const section = document.getElementById('ai-report-details-section');
    const btn = document.getElementById('btn-toggle-ai-report');
    if (!section || !btn) return;
    
    if (section.style.display === 'none') {
        section.style.display = 'block';
        btn.innerHTML = '<span>👁️ Hide AI Report</span>';
        btn.classList.add('active');
    } else {
        section.style.display = 'none';
        btn.innerHTML = '<span>👁️ View AI Report</span>';
        btn.classList.remove('active');
    }
};

window.handleGenerateAIReport = async function(id) {
    const btn = document.getElementById('btn-generate-ai-report');
    const spinner = document.getElementById('generate-ai-spinner');
    if (!btn) return;
    
    btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    
    try {
        const res = await window.JanSamadhanAPI.generateAIReport(id);
        if (res) {
            showToast('🤖 AI Report generated successfully!', 'success');
            // Re-render the current detail modal
            if (window.viewDetail) {
                await window.viewDetail(id);
            } else if (window.showComplaintDetails) {
                await window.showComplaintDetails(id);
            }
        } else {
            throw new Error('Failed to generate');
        }
    } catch (e) {
        showToast(e.message || 'Error generating AI report', 'error');
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
};

window.handleRefreshAIReport = async function(id) {
    const btn = document.getElementById('btn-refresh-ai-report');
    const spinner = document.getElementById('refresh-ai-spinner');
    if (!btn) return;
    
    btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    
    try {
        const res = await window.JanSamadhanAPI.generateAIReport(id, true);
        if (res) {
            showToast('🔄 AI Report refreshed successfully!', 'success');
            // Re-render the current detail modal
            if (window.viewDetail) {
                await window.viewDetail(id);
            } else if (window.showComplaintDetails) {
                await window.showComplaintDetails(id);
            }
        } else {
            throw new Error('Failed to refresh');
        }
    } catch (e) {
        showToast(e.message || 'Error refreshing AI report', 'error');
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
};

// ── DYNAMIC LIFECYCLE ACTION MODALS (DELETE, REOPEN, EXTEND SLA) ──
window.openDeleteModal = function(id) {
    const existing = document.getElementById('dynamic-action-modal');
    if (existing) existing.remove();
    
    const modalHtml = `
    <div id="dynamic-action-modal" class="modal-overlay show" style="display:flex;align-items:center;justify-content:center;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.6);z-index:9999;backdrop-filter:blur(4px)">
        <div class="modal-card" style="background:#fff;border-radius:16px;width:100%;max-width:480px;padding:24px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.1),0 10px 10px -5px rgba(0,0,0,0.04);animation:modalEnter 0.25s cubic-bezier(0.16, 1, 0.3, 1)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                <h3 style="margin:0;font-size:1.15rem;font-weight:800;color:#ef4444;display:flex;align-items:center;gap:8px">
                    <span>⚠️</span> Delete Complaint
                </h3>
                <button onclick="closeDynamicModal()" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:var(--text-muted)">&times;</button>
            </div>
            <p style="margin:0 0 16px 0;font-size:0.9rem;color:var(--text);line-height:1.5">
                This action is irreversible. It will soft-delete the complaint, hiding it from public feeds while preserving audit records.
            </p>
            <div style="background:rgba(239,68,68,0.04);border:1px solid rgba(239,68,68,0.1);border-radius:8px;padding:12px;margin-bottom:16px;font-size:0.85rem">
                To confirm deletion, please type <strong style="color:#ef4444;user-select:none">DELETE</strong> in the box below.
            </div>
            <input type="text" id="delete-confirm-input" placeholder="Type DELETE here..." oninput="validateDeleteInput()" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.9rem;margin-bottom:20px;outline:none" autocomplete="off">
            
            <div style="display:flex;justify-content:flex-end;gap:12px">
                <button class="btn btn-outline" onclick="closeDynamicModal()" style="padding:8px 16px;border-radius:8px;font-size:0.88rem;cursor:pointer">Cancel</button>
                <button id="btn-confirm-delete-action" class="btn btn-danger" onclick="submitDeleteGrievance('${id}')" disabled style="padding:8px 16px;border-radius:8px;font-size:0.88rem;cursor:pointer;background:#ef4444;color:#fff;border:none;opacity:0.5;display:flex;align-items:center;gap:6px">
                    <span class="spinner-border spinner-border-sm" style="width:12px;height:12px;display:none" id="delete-spinner"></span>
                    <span>Confirm Delete</span>
                </button>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.body.style.overflow = 'hidden';
};

window.validateDeleteInput = function() {
    const input = document.getElementById('delete-confirm-input');
    const btn = document.getElementById('btn-confirm-delete-action');
    if (!input || !btn) return;
    
    if (input.value === 'DELETE') {
        btn.disabled = false;
        btn.style.opacity = '1';
    } else {
        btn.disabled = true;
        btn.style.opacity = '0.5';
    }
};

window.submitDeleteGrievance = async function(id) {
    const btn = document.getElementById('btn-confirm-delete-action');
    const spinner = document.getElementById('delete-spinner');
    if (!btn) return;
    
    btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    
    try {
        const res = await window.JanSamadhanAPI.deleteComplaint(id);
        if (res.success) {
            showToast('🗑️ Complaint deleted successfully!', 'success');
            closeDynamicModal();
            closeModal('grievanceDetailModal');
            closeModal('complaintDetailsModal');
            // Refresh feed
            if (window.fetchGrievances) {
                await window.fetchGrievances();
            } else if (window.loadMyGrievances) {
                await window.loadMyGrievances();
            } else if (window.loadComplaints) {
                await window.loadComplaints();
            } else {
                setTimeout(() => window.location.reload(), 1000);
            }
        } else {
            throw new Error(res.error || 'Failed to delete');
        }
    } catch (e) {
        showToast(e.message || 'Error deleting complaint', 'error');
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
};

window.openReopenModal = function(id) {
    const existing = document.getElementById('dynamic-action-modal');
    if (existing) existing.remove();
    
    const modalHtml = `
    <div id="dynamic-action-modal" class="modal-overlay show" style="display:flex;align-items:center;justify-content:center;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.6);z-index:9999;backdrop-filter:blur(4px)">
        <div class="modal-card" style="background:#fff;border-radius:16px;width:100%;max-width:480px;padding:24px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.1),0 10px 10px -5px rgba(0,0,0,0.04);animation:modalEnter 0.25s cubic-bezier(0.16, 1, 0.3, 1)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                <h3 style="margin:0;font-size:1.15rem;font-weight:800;color:var(--primary-light);display:flex;align-items:center;gap:8px">
                    <span>🔄</span> Reopen Complaint
                </h3>
                <button onclick="closeDynamicModal()" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:var(--text-muted)">&times;</button>
            </div>
            <p style="margin:0 0 12px 0;font-size:0.88rem;color:var(--text-muted)">
                Please describe the reason why this grievance requires reopening. (Limit: 3 reopening cycles total).
            </p>
            <div style="margin-bottom:16px">
                <label style="display:block;font-size:0.75rem;font-weight:700;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase">Reopen Reason <span style="color:#ef4444">*</span></label>
                <textarea id="reopen-reason-textarea" placeholder="E.g., The resolution provided is incomplete because..." style="width:100%;height:100px;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.9rem;outline:none;resize:none;font-family:inherit"></textarea>
            </div>
            
            <div style="display:flex;justify-content:flex-end;gap:12px">
                <button class="btn btn-outline" onclick="closeDynamicModal()" style="padding:8px 16px;border-radius:8px;font-size:0.88rem;cursor:pointer">Cancel</button>
                <button id="btn-confirm-reopen-action" class="btn btn-primary" onclick="submitReopenGrievance('${id}')" style="padding:8px 16px;border-radius:8px;font-size:0.88rem;cursor:pointer;display:flex;align-items:center;gap:6px">
                    <span class="spinner-border spinner-border-sm" style="width:12px;height:12px;display:none" id="reopen-spinner"></span>
                    <span>Reopen Complaint</span>
                </button>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.body.style.overflow = 'hidden';
};

window.submitReopenGrievance = async function(id) {
    const reasonText = document.getElementById('reopen-reason-textarea')?.value?.trim();
    if (!reasonText) {
        showToast('Please provide a reopening reason', 'error');
        return;
    }
    
    const btn = document.getElementById('btn-confirm-reopen-action');
    const spinner = document.getElementById('reopen-spinner');
    if (!btn) return;
    
    btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    
    try {
        const res = await window.JanSamadhanAPI.reopenComplaint(id, reasonText);
        if (res.success) {
            showToast('🔄 Complaint reopened successfully!', 'success');
            closeDynamicModal();
            closeModal('grievanceDetailModal');
            closeModal('complaintDetailsModal');
            // Refresh
            if (window.fetchGrievances) {
                await window.fetchGrievances();
            } else if (window.loadMyGrievances) {
                await window.loadMyGrievances();
            } else if (window.loadComplaints) {
                await window.loadComplaints();
            } else {
                setTimeout(() => window.location.reload(), 1000);
            }
        } else {
            throw new Error(res.error || 'Failed to reopen');
        }
    } catch (e) {
        showToast(e.message || 'Error reopening complaint', 'error');
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
};

window.openExtendDeadlineModal = function(id, currentSlaDateStr) {
    const existing = document.getElementById('dynamic-action-modal');
    if (existing) existing.remove();
    
    let minDateStr = '';
    try {
        if (currentSlaDateStr) {
            const currentSla = new Date(currentSlaDateStr);
            const minDate = new Date(currentSla.getTime() + 60 * 1000);
            const pad = (num) => String(num).padStart(2, '0');
            minDateStr = `${minDate.getFullYear()}-${pad(minDate.getMonth()+1)}-${pad(minDate.getDate())}T${pad(minDate.getHours())}:${pad(minDate.getMinutes())}`;
        }
    } catch (e) {
        console.error('Error parsing SLA date:', e);
    }
    
    const modalHtml = `
    <div id="dynamic-action-modal" class="modal-overlay show" style="display:flex;align-items:center;justify-content:center;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.6);z-index:9999;backdrop-filter:blur(4px)">
        <div class="modal-card" style="background:#fff;border-radius:16px;width:100%;max-width:480px;padding:24px;box-shadow:0 20px 25px -5px rgba(0,0,0,0.1),0 10px 10px -5px rgba(0,0,0,0.04);animation:modalEnter 0.25s cubic-bezier(0.16, 1, 0.3, 1)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                <h3 style="margin:0;font-size:1.15rem;font-weight:800;color:var(--primary-light);display:flex;align-items:center;gap:8px">
                    <span>📅</span> Extend SLA Deadline
                </h3>
                <button onclick="closeDynamicModal()" style="background:none;border:none;font-size:1.2rem;cursor:pointer;color:var(--text-muted)">&times;</button>
            </div>
            
            <div style="margin-bottom:14px">
                <label style="display:block;font-size:0.75rem;font-weight:700;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase">New Due Date & Time <span style="color:#ef4444">*</span></label>
                <input type="datetime-local" id="extend-due-date-input" min="${minDateStr}" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.9rem;outline:none;font-family:inherit">
                <div style="font-size:0.7rem;color:var(--text-muted);margin-top:4px">Must be later than current deadline: ${currentSlaDateStr ? new Date(currentSlaDateStr).toLocaleString() : 'N/A'}</div>
            </div>
            
            <div style="margin-bottom:20px">
                <label style="display:block;font-size:0.75rem;font-weight:700;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase">Reason <span style="color:#ef4444">*</span></label>
                <textarea id="extend-reason-textarea" placeholder="Provide justification for deadline extension..." style="width:100%;height:80px;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:0.9rem;outline:none;resize:none;font-family:inherit"></textarea>
            </div>
            
            <div style="display:flex;justify-content:flex-end;gap:12px">
                <button class="btn btn-outline" onclick="closeDynamicModal()" style="padding:8px 16px;border-radius:8px;font-size:0.88rem;cursor:pointer">Cancel</button>
                <button id="btn-confirm-extend-action" class="btn btn-primary" onclick="submitExtendDeadline('${id}')" style="padding:8px 16px;border-radius:8px;font-size:0.88rem;cursor:pointer;display:flex;align-items:center;gap:6px">
                    <span class="spinner-border spinner-border-sm" style="width:12px;height:12px;display:none" id="extend-spinner"></span>
                    <span>Extend Deadline</span>
                </button>
            </div>
        </div>
    </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    document.body.style.overflow = 'hidden';
};

window.submitExtendDeadline = async function(id) {
    const newDueDate = document.getElementById('extend-due-date-input')?.value;
    const reason = document.getElementById('extend-reason-textarea')?.value?.trim();
    
    if (!newDueDate) {
        showToast('Please select a new due date & time', 'error');
        return;
    }
    if (!reason) {
        showToast('Please provide a reason for extension', 'error');
        return;
    }
    
    const btn = document.getElementById('btn-confirm-extend-action');
    const spinner = document.getElementById('extend-spinner');
    if (!btn) return;
    
    btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    
    try {
        const isoDate = new Date(newDueDate).toISOString();
        const res = await window.JanSamadhanAPI.extendDeadline(id, isoDate, reason);
        if (res.success) {
            showToast('📅 Deadline extended successfully!', 'success');
            closeDynamicModal();
            closeModal('grievanceDetailModal');
            closeModal('complaintDetailsModal');
            // Refresh
            if (window.fetchGrievances) {
                await window.fetchGrievances();
            } else if (window.loadMyGrievances) {
                await window.loadMyGrievances();
            } else if (window.loadComplaints) {
                await window.loadComplaints();
            } else {
                setTimeout(() => window.location.reload(), 1000);
            }
        } else {
            throw new Error(res.error || 'Failed to extend deadline');
        }
    } catch (e) {
        showToast(e.message || 'Error extending deadline', 'error');
        btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
    }
};

window.closeDynamicModal = function() {
    const modal = document.getElementById('dynamic-action-modal');
    if (modal) {
        modal.remove();
    }
    document.body.style.overflow = '';
};
