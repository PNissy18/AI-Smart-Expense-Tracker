# How to Run: AI Smart Expense Tracker

## Step-by-Step Guide

### Step 1: Install Python Dependencies
```bash
cd AI-Smart-Expense-Tracker
pip install -r backend/requirements.txt
```

### Step 2: Generate Synthetic Training Data
```bash
cd model
python generate_data.py
```
This creates `data/transactions.csv` with 36 months of synthetic transaction data.

### Step 3: Train the Multi-Task Model
```bash
cd model
python multitask_model.py
```
This will:
- Preprocess the data (clean, aggregate, engineer features, create sequences)
- Build the Multi-Task LSTM model
- Train for up to 100 epochs (with early stopping)
- Save the trained model to `data/final_multitask_model.keras`
- Save training plots to `data/training_history.png`
- Print evaluation metrics

### Step 4: Start the Backend API
```bash
cd backend
python app.py
```
The Flask server starts at http://localhost:5000

### Step 5: Create and Start the React Frontend
```bash
npx create-react-app frontend
cd frontend
npm install axios recharts react-router-dom
npm start
```
The React app starts at http://localhost:3000

### Step 6: Build frontend components
Replace the contents of `frontend/src/App.js` with your dashboard components
that call the backend API endpoints.

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/transactions` | GET | Get all transactions |
| `/api/transactions` | POST | Add transaction |
| `/api/upload-csv` | POST | Upload CSV file |
| `/api/dashboard` | GET | Dashboard summary |
| `/api/predict` | GET | AI predictions |

## Project Structure
```
AI-Smart-Expense-Tracker/
├── model/
│   ├── generate_data.py      # Synthetic data generation
│   ├── preprocess.py          # Data preprocessing pipeline
│   └── multitask_model.py     # Multi-Task LSTM model
├── backend/
│   ├── app.py                 # Flask REST API
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React app (created with create-react-app)
├── data/
│   ├── transactions.csv       # Generated after Step 2
│   ├── scaler.pkl            # Generated after Step 3
│   └── final_multitask_model.keras  # Generated after Step 3
├── FINAL_REPORT.md           # Complete project document
└── HOW_TO_RUN.md             # This file
```
