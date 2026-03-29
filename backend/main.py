from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from routers.track import router as track_router

app = FastAPI(title="RigRadar API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(track_router)

@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "RigRadar API"}

handler = Mangum(app)

