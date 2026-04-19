# JanSamadhan Production Deployment Guide 🚀

This document outlines the steps to deploy the JanSamadhan system to production.

## 1. Environment Variables (.env)
Create a `.env` file in the `backend` directory with the following variables:
```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/jansamadhan
DATABASE_NAME=jansamadhan
JWT_SECRET=your_super_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AWS S3 Settings
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
AWS_REGION=ap-south-1
S3_BUCKET_NAME=jansamadhan-media
```

## 2. Database Setup (MongoDB Atlas)
1.  Create a Project on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2.  Deploy a Free/Serverless Cluster.
3.  Add a Database User and allow network access (0.0.0.0/0 for pilot).
4.  Run the index initialization script (happens automatically on first startup via `db.py`).

## 3. Backend Deployment (Docker)
We use Docker for containerization.
1. Build the image:
   ```bash
   docker build -t jansamadhan-api ./backend
   ```
2. Run the container:
   ```bash
   docker run -d -p 8000:8000 --env-file ./backend/.env jansamadhan-api
   ```

## 4. Frontend Deployment
The frontend is a static site with Vanilla JS.
*   **Vercel/Netlify**: Connect the GitHub repository and set the root directory to the project folder. Ensure `backend/config.js` points to the production API URL.

## 5. Background Jobs (Escalation)
The system uses `APScheduler` which runs inside the FastAPI process.
*   **Safeguard**: We've implemented a distributed lock using MongoDB to prevent duplicate executions if multiple API instances are running.

## 6. Backup & Recovery Strategy 🛡️
*   **Automated Backups**: Enable "Cloud Backup" on MongoDB Atlas (Free tier has limited snapshotting, shared tier starts at $0.10/GB).
*   **Retention**: Set for 7 days.
*   **Test Restore**: Perform a test restore to a temporary cluster once every quarter.

## 7. Security Hardening
*   **SSL**: Always run the API behind a reverse proxy (Nginx/Traefik) or use provider-managed SSL (Vercel/Railway).
*   **Headers**: Security headers are enforced via middleware in `app.py`.
*   **Rate Limiting**: Auth and Complaint routes are rate-limited per IP.
