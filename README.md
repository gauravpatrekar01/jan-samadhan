# 🏛️ JanSamadhan - Smart Public Grievance Resolution System

<div align="center">
  <h3>Transparent Governance. Faster Resolutions.</h3>
  <p>A digital initiative to bring transparency and efficiency to public grievance redressal via a modern web platform securely backed by Python and MongoDB.</p>
</div>

---

## 🚀 Key Features

* **Role-Based Access**: Specialized portals tailored for **Citizens**, **Field Officers**, and **Administrators**.
* **Smart Priority Queue**: Emergency cases are automatically escalated and flagged for immediate attention.
* **Geospatial Location Mapping**: Track complaints easily with region heatmaps and pinned addresses.
* **Real-time Processing**: Seamless REST APIs ensure live updates out-of-the-box.
* **Modern Stack**:
  * **Frontend**: Pure HTML, CSS, and Vanilla JS configured for maximum performance and broad compatibility.
  * **Backend**: High-performance Python backend powered by **FastAPI**.
  * **Database**: Decentralized tracking via **MongoDB Atlas**.

---

## 🛠️ Technology Stack

| Component     | Technology |
|---------------|------------|
| Frontend      | HTML5, CSS3, Vanilla JavaScript |
| Backend       | Python 3.11+, FastAPI, Uvicorn |
| Database      | MongoDB (Atlas / Local Docker) |
| Security      | JWT Auth, passlib Bcrypt Password Hashing |

---

## 🧑‍💻 Getting Started (Local Development)

Follow these steps to quickly get the entire project running on your local machine.

### 1️⃣ Database Config
The backend is already wired to a MongoDB cluster via standard URI integration.
1. Open `backend/.env`.
2. Ensure your `MONGO_URI` is accurately providing your MongoDB credentials (e.g., swapping out the `<password>` tag).

### 2️⃣ Start the Python Backend API
The backend utilizes Python virtual environments to prevent dependency clutter.

**Open a terminal at the project root and run:**
```powershell
# 1. Navigate into the backend folder
cd backend

# 2. Activate the Virtual Environment
# (For Windows)
.\venv\Scripts\activate
# (For Mac/Linux, run: source venv/bin/activate)

# 3. Install required packages
pip install -r requirements.txt
pip install email-validator

# 4. Boot the server
uvicorn app:app --reload
```
Once you see `Application startup complete` in your console, the backend is active on **http://localhost:8000**.
*(Tip: Visit `http://localhost:8000/docs` in your browser to view and test all APIs interactively!)*

### 3️⃣ Start the Frontend UI
Because the UI is built strictly with beautiful lightweight HTML, CSS, and JS, there is no bulky Next/React compilation process required!

**To view the app:**
1. You can simply double-click `index.html` located in the root directory to run it in your browser natively.
2. Alternatively, for a better networking experience, launch the project folder using an IDE extension like **VS Code Live Server**.

---

## 📁 Project Structure

```text
gitjansamadhan/
│
├── index.html            # Main Website & Login Gateway
├── register.html         # Grievance Registration Form
├── citizen.html          # Citizen Tracking Dashboard
├── officer.html          # Field Officer Action Dashboard
├── admin.html            # Administrator Analytics Console
├── js/                   # Frontend Logic
│   ├── api.js            # Pure REST API Wrapper connecting to FastAPI
│   └── app.js            # UI interaction logic & animations
│
└── backend/              # Python FastAPI Application
    ├── .env              # Environment Variables & Atlas Connection
    ├── app.py            # Main Application & Router Config
    ├── db.py             # MongoDB Driver Singleton
    ├── routes/           # REST Handlers (auth.py, complaints.py, admin.py)
    ├── schemas/          # Pydantic data validation models
    └── tests/            # Test suite 
```
