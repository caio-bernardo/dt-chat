"""
Script to create a Banco Bot API
"""

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from .database import create_db_and_tables
from .routes import router

load_dotenv()

app = FastAPI(title="BancoBotAPI")


app.include_router(router)


@app.on_event("startup")
async def startup():
    create_db_and_tables()


def main():
    uvicorn.run(app, port=8080)


if __name__ == "__main__":
    main()
