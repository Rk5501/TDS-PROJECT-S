# api/index.py
from mangum import Mangum
from app import app  # make sure your FastAPI app is named `app` in app.py

handler = Mangum(app)
