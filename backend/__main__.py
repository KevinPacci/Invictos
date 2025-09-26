﻿import uvicorn

from .main import app


def run() -> None:
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
