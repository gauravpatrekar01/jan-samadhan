// Handle post-login redirect
document.addEventListener('DOMContentLoaded', function() {
    const redirectUrl = sessionStorage.getItem('redirect_after_login');
    
    if (redirectUrl) {
        console.log('🔄 Redirecting to:', redirectUrl);
        sessionStorage.removeItem('redirect_after_login');
        
        // Small delay to ensure login is complete
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 1000);
    }
});

// Enhanced login form submission
const originalLogin = window.login;
window.login = async function(e) {
    if (e) e.preventDefault();
    
    const form = document.getElementById('loginForm');
    const formData = new FormData(form);
    const loginBtn = document.getElementById('loginBtn');
    
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span> Signing in...';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            body: JSON.stringify({
                email: formData.get('email'),
                password: formData.get('password')
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const user = data.data;
            
            // Store user data
            sessionStorage.setItem('js_user', JSON.stringify(user));
            localStorage.setItem('js_user', JSON.stringify(user));
            
            // Show success message
            showToast('Login successful! Redirecting...', 'success');
            
            // Handle redirect
            const redirectUrl = sessionStorage.getItem('redirect_after_login');
            if (redirectUrl) {
                sessionStorage.removeItem('redirect_after_login');
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 1500);
            } else {
                // Default redirect based on role
                const role = user.role;
                let defaultRedirect = 'dashboard.html';
                
                if (role === 'admin') {
                    defaultRedirect = 'admin.html';
                } else if (role === 'officer') {
                    defaultRedirect = 'officer.html';
                } else if (role === 'ngo') {
                    defaultRedirect = 'ngo.html';
                }
                
                setTimeout(() => {
                    window.location.href = defaultRedirect;
                }, 1500);
            }
            
        } else {
            throw new Error(data.error?.message || 'Login failed');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showToast(error.message, 'error');
    } finally {
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '🚀 Sign In';
        }
    }
};

// Call original login if it exists
if (typeof originalLogin === 'function') {
    originalLogin.apply(this, arguments);
}
