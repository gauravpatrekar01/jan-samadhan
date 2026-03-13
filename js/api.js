// JanSamadhan: Firebase-powered API Service
console.log("🚀 JanSamadhan: API Service Loading...");

const JanSamadhanAPI = {
    // ── AUTHENTICATION ──
    
    async register(userData) {
        try {
            const auth = window.auth;
            const db = window.db;
            if (!auth || !db) throw new Error("Firebase not initialized correctly.");

            // 1. Create user in Firebase Auth
            const userCredential = await auth.createUserWithEmailAndPassword(userData.email, userData.password);
            const user = userCredential.user;

            // 2. Store additional user info in Firestore
            const profile = {
                uid: user.uid,
                name: userData.name,
                email: userData.email,
                role: (userData.role || 'citizen').toLowerCase(),
                department: userData.department || null,
                createdAt: window.firebase.firestore.FieldValue.serverTimestamp()
            };
            await db.collection('users').doc(user.uid).set(profile);

            // 3. Set local session
            localStorage.setItem('js_user', JSON.stringify(profile));
            return profile;
        } catch (error) {
            console.error("Registration Error:", error);
            throw new Error(error.message);
        }
    },

    async login(credentials) {
        try {
            const auth = window.auth;
            const db = window.db;
            if (!auth || !db) throw new Error("Firebase not initialized correctly.");

            // 1. Sign in with Auth
            const userCredential = await auth.signInWithEmailAndPassword(credentials.email, credentials.password);
            const user = userCredential.user;

            // 2. Fetch profile from Firestore
            const doc = await db.collection('users').doc(user.uid).get();
            if (!doc.exists) throw new Error("User profile not found. Please register first.");
            
            const profile = doc.data();
            localStorage.setItem('js_user', JSON.stringify(profile));
            return profile;
        } catch (error) {
            console.error("Login Error:", error);
            throw new Error(error.message);
        }
    },

    async logout() {
        try {
            if (window.auth) {
                await window.auth.signOut();
                localStorage.removeItem('js_user');
            }
        } catch (error) {
            console.error("Logout Error:", error);
        }
    },

    // ── GRIEVANCES (Firestore) ──

    async createGrievance(grievanceData) {
        try {
            const db = window.db;
            const user = JSON.parse(localStorage.getItem('js_user'));
            const docRef = await db.collection('complaints').add({
                ...grievanceData,
                citizen_id: user ? user.uid : 'anonymous',
                status: 'submitted',
                createdAt: window.firebase.firestore.FieldValue.serverTimestamp(),
                updatedAt: window.firebase.firestore.FieldValue.serverTimestamp(),
                history: [
                    { status: 'submitted', remarks: 'Grievance filed by citizen', timestamp: new Date().toISOString() }
                ]
            });
            return { id: docRef.id, ...grievanceData };
        } catch (error) {
            console.error("Create Grievance Error:", error);
            throw new Error(error.message);
        }
    },

    async getMyGrievances() {
        try {
            const db = window.db;
            const user = JSON.parse(localStorage.getItem('js_user'));
            if (!user) throw new Error("Authentication required");

            const snapshot = await db.collection('complaints')
                .where('citizen_id', '==', user.uid)
                .orderBy('createdAt', 'desc')
                .get();
            
            return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        } catch (error) {
            console.error("Fetch User Grievances Error:", error);
            return [];
        }
    },

    async getAllGrievances() {
        try {
            const db = window.db;
            const snapshot = await db.collection('complaints')
                .orderBy('createdAt', 'desc')
                .limit(100)
                .get();
            return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        } catch (error) {
            console.error("Fetch All Grievances Error:", error);
            return [];
        }
    },

    async getAssignedGrievances() {
        try {
            const db = window.db;
            const snapshot = await db.collection('complaints')
                .where('status', 'in', ['submitted', 'under_review', 'in_progress'])
                .get();
            return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        } catch (error) {
            return this.getAllGrievances(); 
        }
    },

    async getGrievanceByID(id) {
        try {
            const db = window.db;
            const doc = await db.collection('complaints').doc(id).get();
            if (!doc.exists) throw new Error("Grievance not found");
            return { id: doc.id, ...doc.data() };
        } catch (error) {
            console.error("Fetch Grievance Detail Error:", error);
            throw new Error(error.message);
        }
    },

    async updateGrievanceStatus(id, status, remarks) {
        try {
            const db = window.db;
            const update = {
                status: status,
                updatedAt: window.firebase.firestore.FieldValue.serverTimestamp(),
                history: window.firebase.firestore.FieldValue.arrayUnion({
                    status: status,
                    remarks: remarks,
                    timestamp: new Date().toISOString()
                })
            };
            await db.collection('complaints').doc(id).update(update);
            return true;
        } catch (error) {
            console.error("Update Status Error:", error);
            throw new Error(error.message);
        }
    },

    async getAnalytics() {
        try {
            const db = window.db;
            if (!db) return null;
            const snapshot = await db.collection('complaints').get();
            const grievances = snapshot.docs.map(doc => doc.data());
            
            const total = grievances.length;
            const resolved = grievances.filter(g => g.status === 'resolved' || g.status === 'closed').length;
            const emergency = grievances.filter(g => g.priority === 'emergency').length;
            const high = grievances.filter(g => g.priority === 'high').length;
            const submitted = grievances.filter(g => g.status === 'submitted' || g.status === 'Submitted').length;

            return {
                total_complaints: total,
                resolved_complaints: resolved,
                resolution_rate: total > 0 ? Math.round((resolved / total) * 100) : 0,
                status_distribution: { submitted: submitted },
                priority_distribution: { emergency: emergency, high: high }
            };
        } catch (error) {
            console.error("Fetch Analytics Error:", error);
            return null;
        }
    }
};

window.JanSamadhanAPI = JanSamadhanAPI;
