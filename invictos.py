from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import uvicorn

app = typer.Typer(help="CLI para ejecutar backend o cliente de Invictos")


@app.command()
def backend(
    host: str = typer.Option("127.0.0.1", help="Host a escuchar"),
    port: int = typer.Option(8000, help="Puerto del API"),
    reload: bool = typer.Option(False, help="Recargar automaticamente (desarrollo)"),
) -> None:
    """Inicia el backend FastAPI con SQLite."""

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command()
def client() -> None:
    """Lanza la aplicacion de escritorio (Flet)."""

    import flet as ft

    from client.app import main as app_main

    ft.app(target=app_main)


@app.command()
def seed(path: Optional[Path] = typer.Option(None, help="Ubicacion personalizada de la base de datos")) -> None:
    """Carga datos de ejemplo en la base."""

    if path:
        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        import os

        os.environ["INVICTOS_DB_URL"] = f"sqlite:///{path.as_posix()}"

    from backend.seed import seed_demo_data

    seed_demo_data()
    typer.echo("Datos de ejemplo cargados")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
