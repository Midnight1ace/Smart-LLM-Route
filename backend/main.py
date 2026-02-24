from fastapi import FastAPI
from app.api.endpoints import router as api_router

app = FastAPI(title="Smart LLM Router")

app.include_router(api_router, prefix="/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
