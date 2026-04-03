# JanSamadhan Backend API

## Setup Locally
1. `cd backend`
2. `python -m venv venv`
3. `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. `pip install -r requirements.txt`
5. `uvicorn app:app --reload`

## Next steps for Frontend Integration
1. Point your frontend fetch calls to `http://localhost:8000/api`.
2. Login should save the token in `localStorage`.
3. Pass `Bearer <token>` in the Authorization header for protected routes.
