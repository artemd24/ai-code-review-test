import uvicorn
from fastapi import FastAPI

from app.modules.routes import router
from app.settings.settings import Settings

settings = Settings()

app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        app, host=settings.APP_HOST, port=settings.APP_PORT, debug=settings.DEBUG
    )
