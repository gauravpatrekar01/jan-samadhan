# 🏛️ JanSamadhan - Smart Public Grievance Resolution System

<div align="center">
  <h3>Transparent Governance. Faster Resolutions.</h3>
  <p>A digital initiative to bring transparency and efficiency to public grievance redressal via a modern web platform securely backed by Python and MongoDB. Empowering citizens, officers, and administrators with real-time grievance tracking and resolution.</p>
</div>

---

## 🚀 Core Features

### 👥 **Role-Based Access Control**
* **Citizens Portal**: Submit, track, and manage grievances with full transparency
* **Field Officers Dashboard**: Prioritized complaint queue, real-time updates, and performance analytics
* **Admin Console**: System-wide oversight, user management, NGO verification, and reporting
* **NGO Portal**: Handle assigned cases, coordinate with officers, and track resolutions
* Secure JWT-based authentication with refresh token mechanism
* Role-specific features and permissions enforced at both frontend and backend

### 📋 **Grievance Management System**
* **Complaint Submission**: Citizens can submit detailed grievances with:
  - Multiple categories (Infrastructure, Water Supply, Sanitation, Health, Education, etc.)
  - Priority levels (Emergency, High, Normal, Low)
  - Location tracking with geospatial data (latitude/longitude)
  - Optional photo/document attachments
  - Description and detailed problem statements
* **Smart Status Tracking**: Real-time status transitions
  - Submitted → Under Review → In Progress → Resolved → Closed
  - Automatic escalation for overdue complaints
  - Audit trail for all status changes
  - Timestamp tracking at each stage
* **Advanced Filtering & Search**:
  - Filter by status, priority, category, and region
  - Full-text search across complaint titles and descriptions
  - Pagination for efficient data loading
  - Geospatial search (complaints within radius)

### 🗺️ **Geospatial Mapping & Visualization**
* Interactive map view with all complaints displayed as pins
* Heatmap visualization showing complaint density by region
* Region-based statistics and insights
* Quick access to complaint details from map markers
* Filter complaints by location radius
* Visual identification of high-priority areas

### 📊 **Analytics & Dashboard**
* **System-Wide Statistics**:
  - Total complaints count and trends
  - Resolution rate percentage
  - Status distribution (Pie charts)
  - Priority distribution (Bar charts)
  - Category breakdown
  - Complaint volume over time
* **Officer Performance Metrics**:
  - Cases handled per officer
  - Average resolution time
  - Complaint resolution rate
  - Performance rankings
* **Citizen Dashboard**:
  - Personal complaint statistics
  - Grievance history and trends
  - Quick status overview
  - Latest announcements and notices

### 🎯 **Smart Priority Queue System**
* Automatic complaint prioritization based on:
  - Severity level (Emergency, High, Normal, Low)
  - Duration pending (older complaints escalated)
  - Category importance
* Emergency cases flagged for immediate attention
* Auto-assignment of least-loaded officers
* Officer workload balancing
* Queue management and redistribution

### 💬 **Feedback & Rating System**
* Citizens can rate resolved grievances (1-5 stars)
* Add detailed feedback comments
* Track satisfaction metrics
* Feedback history and analytics
* Officer performance evaluated through citizen feedback

### 🔔 **Notification System**
* Status change notifications
* Officer assignment alerts
* Complaint escalation warnings
* System maintenance announcements
* Email notifications (optional)
* In-app toast notifications

### 📰 **Announcements & Notices**
* Admin can publish system-wide announcements
* Important notices and alerts
* Pinned announcements for visibility
* Categorized news and updates
* Date-based filtering and sorting
* Citizen-facing communication channel

### 🤝 **NGO Portal & Management**
* Dedicated NGO registration and verification system
* NGO document upload and verification
* Category-based service offerings
* Assigned complaint handling
* Available complaint browsing
* Progress tracking and status updates
* NGO performance statistics
* Profile management and updates
* Admin verification workflow

### 🔐 **Security & Authentication**
* **JWT-Based Authentication**:
  - Access tokens (60-minute expiration)
  - Refresh tokens (30-day expiration)
  - Token validation on every request
  - Automatic token refresh mechanism
* **Password Security**:
  - Bcrypt hashing with salt
  - Complex password requirements (uppercase, lowercase, numbers, special chars)
  - 12-digit Aadhaar validation for citizens
* **Access Control**:
  - Role-based endpoint protection
  - Data isolation (citizens see only own complaints)
  - Officer-specific complaint assignment
  - Admin-only administrative functions
* **Rate Limiting**:
  - 5 requests/minute for login endpoints
  - 3 requests/minute for registration endpoints
  - Protection against brute-force attacks
  - Configurable rate limits per endpoint
* **Data Protection**:
  - HTTPS/TLS encryption (production)
  - Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
  - No sensitive data in logs or error messages
  - Aadhaar number masking in UI (last 4 digits only)

### 📱 **Responsive Design**
* Mobile-first responsive layout
* Works on all screen sizes (320px - 1920px)
* Touch-friendly interface for mobile devices
* Adaptive navigation for mobile/tablet/desktop
* Dark mode support (theme toggle)
* Optimized performance for slow networks

### ⚡ **Performance & Scalability**
* Vanilla JavaScript (no heavy frameworks)
* Lightweight HTML/CSS for fast loading
* Database connection pooling
* Optimized MongoDB queries with indexes
* Pagination for large datasets
* Lazy loading of images and content
* API response times < 1 second for most operations
* Concurrent user support with load balancing

### 📁 **File Management**
* Document upload for NGO registration
* S3 cloud storage integration (with local fallback)
* File type validation (PDF, Images)
* File size limits (5MB per document)
* Unique filename generation
* Presigned URL support for secure uploads

### 🔍 **Government Registry Integration**
* Aadhaar verification for citizen validation
* Verification status tracking
* Validated citizen badge/indicator
* Government record matching

### 📊 **Advanced Reporting**
* Export complaint data (CSV, JSON)
* Custom report generation
* Date range filtering
* Multi-criteria reporting
* Performance reports by officer
* System health reports

### 🗄️ **Audit Trail & Compliance**
* Complete action logging:
  - User login/logout events
  - Complaint creation, updates, assignments
  - Status changes with timestamps
  - Admin actions tracked with actor details
* Audit log access for administrators
* Compliance tracking
* Historical data retention

---

## 🛠️ Technology Stack

| Component     | Technology |
|---------------|------------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **Database** | MongoDB (Atlas or Local) |
| **Security** | JWT (python-jose), Bcrypt (passlib) |
| **Task Scheduling** | APScheduler |
| **Rate Limiting** | SlowAPI |
| **File Storage** | AWS S3 with local fallback |
| **Logging** | Python JSON Logger |
| **Testing** | pytest, httpx |
| **API Documentation** | FastAPI Swagger/OpenAPI |

---

## 🧑‍💻 Getting Started (Local Development)

### Prerequisites
- Python 3.11 or higher
- MongoDB (Atlas or Local instance)
- Node.js/npm (optional, for serving static files)
- Git

### Step 1️⃣: Clone & Configure

```bash
# Clone the repository
git clone https://github.com/yourusername/jansamadhan.git
cd jansamadhan

# Create environment file
cp backend/.env.example backend/.env
```

### Step 2️⃣: Configure Environment

Edit `backend/.env`:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=JanSamadhan
DATABASE_NAME=jansamadhan
JWT_SECRET=your_super_secret_key_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
AWS_ACCESS_KEY=optional_s3_key
AWS_SECRET_KEY=optional_s3_secret
S3_BUCKET_NAME=optional_bucket_name
```

### Step 3️⃣: Start Backend API

```bash
# Navigate to backend
cd backend

# (Optional) Create virtual environment
python -m venv venv
# Activate:
# Windows: .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create test users (optional)
python create_test_users.py

# Start the server
uvicorn app:app --reload
```

✅ Backend runs on **http://localhost:8000**  
📖 Interactive API docs available at **http://localhost:8000/docs**

### Step 4️⃣: Start Frontend

No build process needed! Simply:

**Option A: Direct File**
```bash
# Open index.html directly in browser
open index.html
# Or right-click → Open with → Browser
```

**Option B: Local Server (Recommended)**
```bash
# Using VS Code Live Server Extension
# Right-click index.html → Open with Live Server

# Or using Python
python -m http.server 8001

# Or using Node/npx
npx serve .
```

✅ Frontend runs on **http://localhost:8001** (or http://localhost:8000 if serving from backend)

### Step 5️⃣: Test the Application

**Test Credentials:**
```
Citizen:
  Email: citizen@example.com
  Password: CitizenSecure123!

Officer:
  Email: officer@example.com
  Password: OfficerSecure123!

Admin:
  Email: admin@example.com
  Password: AdminSecure123!
```

---

## 📁 Project Structure

```text
jansamadhan/
├── 📄 index.html               # Landing page & authentication portal
├── 📄 citizen.html             # Citizen dashboard (grievance tracking)
├── 📄 officer.html             # Officer dashboard (priority queue & analytics)
├── 📄 admin.html               # Admin console (system management)
├── 📄 ngo.html                 # NGO portal (case handling)
├── 📄 ngo-portal.html          # NGO registration & management
├── 📄 admin-login.html         # Admin login page
├── 📄 register.html            # Grievance registration form
│
├── 📁 css/
│   ├── main.css                # Global styles & components
│   └── dashboard.css           # Dashboard-specific styles
│
├── 📁 js/
│   ├── api.js                  # REST API client wrapper
│   ├── app.js                  # Core app logic & utilities
│   ├── charts.js               # Chart.js visualizations
│   ├── chatbot.js              # AI chatbot widget
│   └── ledger.js               # Data ledger & utilities
│
├── 📁 backend/
│   ├── 📄 app.py               # FastAPI main application
│   ├── 📄 db.py                # MongoDB connection & singleton
│   ├── 📄 config.py            # Configuration & settings
│   ├── 📄 security.py          # JWT & password utilities
│   ├── 📄 dependencies.py      # FastAPI dependency injection
│   ├── 📄 errors.py            # Custom exception classes
│   ├── 📄 audit.py             # Audit logging
│   ├── 📄 search.py            # Full-text search utilities
│   ├── 📄 notifications.py     # Notification system
│   ├── 📄 limiter.py           # Rate limiting configuration
│   ├── 📄 government_registry.py # Aadhaar verification
│   ├── 📄 requirements.txt      # Python dependencies
│   ├── 📄 .env                 # Environment variables
│   │
│   ├── 📁 routes/              # API endpoint handlers
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── complaints.py       # Grievance management
│   │   ├── admin.py            # Admin operations
│   │   └── ngo.py              # NGO-specific endpoints
│   │
│   ├── 📁 schemas/             # Pydantic data models
│   │   ├── user.py             # User & NGO models
│   │   └── complaint.py        # Complaint/grievance models
│   │
│   ├── 📁 services/            # Business logic services
│   │   └── s3_service.py       # AWS S3 integration
│   │
│   ├── 📁 tests/               # Test suite
│   │   ├── test_main.py        # Main test suite
│   │   └── test_integration.py # Integration tests
│   │
│   ├── 📁 static/
│   │   └── uploads/            # Local file storage fallback
│   │
│   └── 📄 Dockerfile           # Container configuration
│
├── 📁 test_files/              # Test data & utilities
├── 📄 TESTING_CHECKLIST.md     # Comprehensive testing guide
├── 📄 TESTING_QUICK_START.md   # Quick testing setup
├── 📄 LOGIN_FIX_GUIDE.md       # Authentication troubleshooting
└── 📄 README.md                # This file
```

---

## 🎯 Features by Role

### 👤 **Citizen Features**
| Feature | Description |
|---------|-------------|
| 📝 Register Account | Sign up with name, email, Aadhaar, password |
| 📋 Submit Grievance | Create new complaint with category, priority, location, attachments |
| 👁️ View All Grievances | See all submitted grievances with status |
| 📍 Track Status | Real-time tracking of complaint progress |
| 🗺️ Map View | Visualize all grievances on interactive map |
| ⭐ Submit Feedback | Rate and comment on resolved grievances |
| 📰 View Announcements | See system announcements and notices |
| 📊 Dashboard | Personal statistics and grievance summary |
| 🔔 Notifications | Real-time status update alerts |

### 👨‍💼 **Officer Features**
| Feature | Description |
|---------|-------------|
| 🎯 Priority Queue | View complaints sorted by priority and age |
| 📊 Analytics | Performance metrics and case statistics |
| 🗺️ Map View | Geographic visualization of assigned complaints |
| ✅ Update Status | Change complaint status and add notes |
| 📝 Add Notes | Document actions and progress |
| 👤 View Complainant | Access citizen details and history |
| ⚡ Quick Assign | Assign cases to self from queue |
| 📈 Performance | Track personal resolution metrics |
| 🔔 Escalation Alerts | Receive alerts for overdue complaints |

### 🔑 **Admin Features**
| Feature | Description |
|---------|-------------|
| 👥 User Management | Create officers, manage accounts, view users |
| 📊 System Dashboard | System-wide statistics and metrics |
| 🤝 NGO Verification | Review and approve NGO registrations |
| 🔍 Audit Log | View complete action history |
| 📝 Manage Categories | Define complaint categories |
| 🔊 Post Announcements | Create and publish system notices |
| 📈 Reports | Generate detailed system reports |
| ⚙️ System Config | Manage settings and escalation rules |
| 📌 Escalation Management | Handle pending and overdue complaints |

### 🤝 **NGO Features**
| Feature | Description |
|---------|-------------|
| 📝 Register Organization | Submit NGO details and documents |
| 📋 View Assigned Cases | See complaints assigned to NGO |
| 👀 Browse Available | Find new cases to handle |
| ✅ Update Progress | Track and update case status |
| 📞 Coordination | Communicate with officers |
| 📊 Performance Stats | View NGO's resolution metrics |
| 👤 Profile Management | Update organization information |
| 📄 Document Upload | Submit verification documents |

---

## 🔌 API Endpoints

### Authentication Endpoints
```
POST   /api/auth/register          # Citizen registration
POST   /api/auth/register-ngo      # NGO registration  
POST   /api/auth/login             # Standard login (Citizen/Officer/NGO)
POST   /api/auth/admin-login       # Admin login
POST   /api/auth/refresh           # Refresh access token
GET    /api/auth/ngo-upload-url    # Get S3 presigned URL
```

### Complaint Endpoints
```
GET    /api/complaints/            # Get all complaints (filtered)
GET    /api/complaints/my          # Get user's complaints
GET    /api/complaints/{id}        # Get complaint details
POST   /api/complaints/            # Create new complaint
PUT    /api/complaints/{id}        # Update complaint status
```

### Admin Endpoints
```
GET    /api/admin/users            # List all users
POST   /api/admin/users            # Create new user (officer/admin)
GET    /api/admin/notices          # Get announcements
POST   /api/admin/notices          # Create announcement
```

### NGO Endpoints
```
POST   /api/ngo/requests           # Submit NGO request
GET    /api/ngo/my-requests        # View NGO's requests
GET    /api/ngo/assigned-complaints # Get assigned cases
GET    /api/ngo/available-complaints # Browse available cases
GET    /api/ngo/stats              # Get NGO statistics
GET    /api/ngo/profile            # Get NGO profile
PATCH  /api/ngo/profile            # Update NGO profile
```

### Public Endpoints
```
GET    /api/stats                  # System statistics
GET    /api/notices                # Public announcements
```

### Full API Documentation
Visit **http://localhost:8000/docs** for interactive Swagger documentation with try-it-out functionality.

---

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t jansamadhan:latest .

# Run container
docker run -p 8000:8000 \
  -e MONGO_URI="mongodb+srv://..." \
  -e JWT_SECRET="your-secret" \
  jansamadhan:latest
```

### Environment Variables for Production
```env
# Security
JWT_SECRET=your_very_long_secret_key_here
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=JanSamadhan
DATABASE_NAME=jansamadhan

# AWS S3 (Optional)
AWS_ACCESS_KEY=your_aws_key
AWS_SECRET_KEY=your_aws_secret
S3_BUCKET_NAME=your_bucket_name
AWS_REGION=ap-south-1

# API
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Deployment Checklist
- [ ] Update `JWT_SECRET` with strong random value
- [ ] Configure `MONGO_URI` for production database
- [ ] Set up HTTPS/TLS certificates
- [ ] Configure CORS for your domain
- [ ] Enable rate limiting for production
- [ ] Set up logging and monitoring
- [ ] Configure database backups
- [ ] Test all features in staging
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Configure email notifications

---

## 🧪 Testing

### Run Unit Tests
```bash
cd backend
pytest tests/ -v --cov
```

### Run Integration Tests
```bash
pytest tests/test_integration.py -v
```

### Manual Testing
See [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) for comprehensive testing guide.

### Quick Test
See [TESTING_QUICK_START.md](TESTING_QUICK_START.md) for quick testing setup.

---

## 🔒 Security Best Practices

✅ **Implemented Security Features:**
- JWT-based authentication with refresh tokens
- Bcrypt password hashing with salt
- Rate limiting on sensitive endpoints
- CORS protection and security headers
- Aadhaar masking in UI (last 4 digits)
- Secure HTTPS-only cookies (production)
- Input validation and sanitization
- SQL injection prevention (Pymongo parameterized)
- CSRF token validation
- Complete audit logging
- Regular dependency vulnerability scanning

⚠️ **Always in Production:**
- Use HTTPS/TLS encryption
- Set secure JWT_SECRET (minimum 32 characters)
- Enable database encryption at rest
- Configure IP whitelisting
- Set up Web Application Firewall (WAF)
- Enable database backups
- Monitor access logs
- Keep dependencies updated
- Use environment variables for secrets
- Never commit .env files to git

---

## 📊 Performance Metrics

Target Performance Goals:
- **Login Response**: < 1 second
- **Page Load**: < 2 seconds
- **List Load (1000+ items)**: < 500ms
- **Database Query**: < 100ms
- **Concurrent Users**: Support 1000+
- **Uptime**: 99.9%

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Make changes and test thoroughly
3. Commit with clear messages: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Write unit tests for new features
- Ensure all tests pass before PR

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with ❤️ for transparent governance
- Powered by FastAPI, MongoDB, and vanilla JavaScript
- Inspired by citizen-centric digital governance initiatives
- Special thanks to all contributors and testers

---

## 📞 Support & Contact

- 📧 Email: support@jansamadhan.gov.in
- 🐛 Report Issues: [GitHub Issues](https://github.com/yourname/jansamadhan/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourname/jansamadhan/discussions)
- 📚 Documentation: [Complete Docs](./DOCUMENTATION.md)

---

## 🎯 Roadmap

### Version 2.0 (Planned)
- [ ] Mobile native app (React Native)
- [ ] AI-powered grievance categorization
- [ ] Video complaint submission
- [ ] Multi-language support
- [ ] SMS notifications
- [ ] Integration with existing government systems
- [ ] Advanced predictive analytics
- [ ] Blockchain-based audit trail

### Version 1.5 (In Development)
- [ ] Enhanced offline support
- [ ] Progressive Web App (PWA)
- [ ] Advanced search filters
- [ ] Complaint templates
- [ ] Bulk import/export

---

**Last Updated**: April 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
