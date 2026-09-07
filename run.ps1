# PowerShell script to start the VoltGuard backend

echo "Starting VoltGuard Backend..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
