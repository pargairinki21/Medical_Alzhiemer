# Deployment Guide

## Architecture
- **Frontend**: Vercel (HTML, CSS, JS)
- **Backend**: Render (FastAPI, MongoDB, Gemini Vision)

## Step 1: Deploy Backend to Render

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/yourrepo.git
   git push -u origin main
   ```

2. **Go to render.com** and sign up

3. **Create new Web Service**
   - Connect your GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
   - Environment Variables (add these in Render):
     ```
     GOOGLE_API_KEY=your_google_api_key
     MONGO_DB_URL=your_mongodb_url
     EMAIL_ADDRESS=your_gmail@gmail.com
     EMAIL_PASSWORD=your_app_password
     ```

4. **Deploy** - Render will build and deploy your backend

5. **Copy the backend URL** (e.g., `https://your-app.onrender.com`)

## Step 2: Deploy Frontend to Vercel

1. **Go to vercel.com** and sign up

2. **Import your GitHub repository**

3. **Configure Vercel**
   - Root Directory: `frontend`
   - Build Command: (leave empty - static files)
   - Output Directory: (leave empty)

4. **Add Environment Variable**
   - Name: `VITE_API_URL`
   - Value: Your Render backend URL (e.g., `https://your-app.onrender.com`)

5. **Deploy** - Vercel will deploy your frontend

## Step 3: Test

1. Open your Vercel frontend URL
2. Test authentication (email OTP)
3. Test chat queries
4. Test MRI analysis

## Notes

- Backend on Render may take 30-60 seconds to cold start (free tier)
- MongoDB Atlas must have IP whitelist set to allow Render's IP
- Email sending requires Gmail App Password (not regular password)
- Gemini Vision requires valid Google API key
