import os
import logging
import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
import json

# ------------------- Load Environment -------------------
load_dotenv()
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")  

# Ensure token is loaded
assert AIPIPE_TOKEN, "Missing AIPIPE_TOKEN in .env"

app = FastAPI()
handler = Mangum(app)
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataAnalystAPI")

# ------------------- AI Pipe Proxy Function -------------------
async def call_aipipe_chat(prompt: str, token: str) -> str:
    url = "https://aipipe.org/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",  # or whichever model is available
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                err = await resp.text()
                raise Exception(f"AI Pipe Error {resp.status}: {err}")
            data = await resp.json()
            # according to AI Pipe docs format
            return data["choices"][0]["message"]["content"]

# ------------------- Routes -------------------
@app.get("/api", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("api_front.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_data(
    request: Request,
    file: UploadFile = File(...)
):
    try:
        file_content = (await file.read()).decode("utf-8")
        logger.info("File uploaded successfully")

        prompt = f"Analyze this data:\n\n{file_content}"
        answer = await call_aipipe_chat(prompt, AIPIPE_TOKEN)

        result = {"status": "success", "answer": answer}
    except Exception as e:
        logger.error("Error calling AI Pipe: %s", e)
        result = {"status": "error", "message": str(e)}

    # 💡 Pretty-print the result as JSON for display
    pretty_json = json.dumps(result, indent=4)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "result": result,
        "pretty_json": pretty_json
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
