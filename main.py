from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import documents, rules, policy_spaces
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="FastAPI Boilerplate", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(
    policy_spaces.router, prefix="/api/v1/policy-spaces", tags=["policy-spaces"]
)
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}


@app.get("/")
async def root():
    return {"message": "FastAPI Boilerplate Application"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
