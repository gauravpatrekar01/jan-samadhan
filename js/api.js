// JanSamadhan: REST API Service connecting to Python Backend
console.log("🚀 JanSamadhan: API Service Loading...");

const API_BASE_URL = 'http://localhost:8000/api';

const JanSamadhanAPI = {
    async _fetch(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers: {
                    ...headers,
                    ...options.headers
                }
            });
            const data = await response.json();
            if (!response.ok || data.success === false) {
                throw new Error(data.message || (data.error && data.error.message) || "API Request failed");
            }
            return data.data || data;
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            throw error;
        }
    },

    async register(userData) {
        return await this._fetch('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },

    async login(credentials) {
        const response = await this._fetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
        if (response && response.token) {
            localStorage.setItem('token', response.token);
            // Store user profile info explicitly too if sent by the backend
            localStorage.setItem('js_user', JSON.stringify(response));
        }
        return response;
    },

    async logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('js_user');
    },

    async createGrievance(grievanceData) {
        return await this._fetch('/complaints/', {
            method: 'POST',
            body: JSON.stringify(grievanceData)
        });
    },

    async getMyGrievances() {
        return await this._fetch('/complaints/my');
    },

    async getAllGrievances() {
        return await this._fetch('/complaints/');
    },

    async getAssignedGrievances() {
        return await this._fetch('/complaints/assigned');
    },

    async getGrievanceByID(id) {
        return await this._fetch(`/complaints/${id}`);
    },

    async updateGrievanceStatus(id, status, remarks) {
        return await this._fetch(`/complaints/${id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status, remarks })
        });
    },

    async getAnalytics() {
        try {
            return await this._fetch('/admin/analytics');
        } catch(err) {
            return {
                total_complaints: 0,
                resolved_complaints: 0,
                resolution_rate: 0,
                status_distribution: { submitted: 0 },
                priority_distribution: { emergency: 0, high: 0 }
            };
        }
    }
};

window.JanSamadhanAPI = JanSamadhanAPI;
