from fastapi import FastAPI
from api.db import close_pool

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
def shutdown_event():
    # Cleanly close DB pool connections when Render stops the service
    close_pool()