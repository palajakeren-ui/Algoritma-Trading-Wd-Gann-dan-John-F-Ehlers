# Gann Quant AI

Gann Quant AI is a comprehensive algorithmic trading system based on the principles of W.D. Gann, combined with modern quantitative analysis, machine learning, and advanced signal processing techniques from John F. Ehlers.

## Features

- **Gann Analysis Engine**: Implements Square of 9, Square of 52, Gann Angles, and more.
- **Astro Engine**: Incorporates planetary aspects and retrograde cycles for timing analysis.
- **Ehlers Indicators**: A full suite of Digital Signal Processing (DSP) indicators.
- **Machine Learning Core**: Utilizes MLP, LSTM, and Transformer models for advanced forecasting.
- **Multi-Broker Integration**: Connects with MetaTrader 5, Binance, and other brokers.
- **Advanced Risk Management**: Features sophisticated risk controls and position sizing.
- **Backtesting and Optimization**: Robust backtesting engine with hyperparameter optimization.
- **Dashboard GUI**: A user-friendly interface for monitoring and control.

## Architecture

(Detailed architecture diagram and explanation to be added here.)

## Getting Started

### Prerequisites

- Python 3.9+
- Pip
- Virtualenv (recommended)

### Installation

**1. Backend (Python)**
```bash
# Clone the repository
git clone https://github.com/your-username/gann_quant_ai.git
cd gann_quant_ai

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials if needed
```

**2. Frontend (Node.js)**
```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to the root directory
cd ..
```

### Usage

To run the full application, you need to start both the backend API server and the frontend development server in separate terminals.

**Terminal 1: Start the Backend**
```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Run the Flask API server
python api.py
```
The API will be running at `http://localhost:5000`.

**Terminal 2: Start the Frontend**
```bash
# Navigate to the frontend directory
cd frontend

# Run the Vite development server
npm run dev
```
The user interface will be accessible at `http://localhost:5173`. Open this URL in your browser to use the application.

## Disclaimer

Trading involves substantial risk and is not suitable for all investors. This software is for educational and research purposes only and should not be considered financial advice.
