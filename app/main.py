from fastapi import FastAPI
from dotenv import load_dotenv
from .db import engine
from .models import Base
from .routers import auth, restaurants, orders

def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(title="GELSİN API", version="1.0.0")

    Base.metadata.create_all(bind=engine)

    app.include_router(auth.router)
    app.include_router(restaurants.router)
    app.include_router(orders.router)

    @app.get("/health")
    def health():
        return {"ok": True}

    return app

app = create_app()
