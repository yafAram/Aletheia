"""Small, permission-gated host agent. It never runs arbitrary shell commands."""
from __future__ import annotations

import base64
import hmac
import io
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from desktop_agent.config import AgentSettings, get_agent_settings


class OpenAppRequest(BaseModel):
    app: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_]+$")


class OpenUrlRequest(BaseModel):
    url: HttpUrl


def create_app(settings: AgentSettings | None = None) -> FastAPI:
    config = settings or get_agent_settings()
    app = FastAPI(
        title="Aletheia Desktop Agent",
        version="0.1.0",
        description=(
            "Agente local para abrir aplicaciones preautorizadas y capturar pantalla "
            "solo cuando el usuario lo solicita explícitamente."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def current_token() -> str:
        if config.token_file:
            try:
                return Path(config.token_file).expanduser().read_text(encoding="utf-8").strip()
            except OSError:
                return ""
        return config.token.strip()

    async def require_token(
        authorization: Annotated[str | None, Header()] = None,
    ) -> None:
        expected_token = current_token()
        if not expected_token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agente bloqueado: configura ALETHEIA_DESKTOP_TOKEN antes de usarlo.",
            )
        scheme, _, supplied = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token del agente ausente o inválido.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    Authenticated = Annotated[None, Depends(require_token)]

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "aletheia-desktop-agent", "platform": platform.system()}

    @app.get("/v1/apps", dependencies=[Depends(require_token)])
    async def list_apps() -> dict:
        apps = []
        for alias, command in sorted(config.allowed_apps.items()):
            executable = command[0]
            available = shutil.which(executable) is not None
            # On Windows, .exe aliases may be resolved by CreateProcess without which().
            if platform.system() == "Windows" and executable.lower().endswith((".exe", ".com")):
                available = True
            apps.append({"id": alias, "available": available})
        return {"platform": platform.system(), "items": apps, "total": len(apps)}

    @app.post("/v1/apps/open", dependencies=[Depends(require_token)])
    async def open_app(request: OpenAppRequest) -> dict:
        command = config.allowed_apps.get(request.app)
        if command is None:
            raise HTTPException(status_code=403, detail="Aplicación no incluida en la lista permitida.")
        executable = command[0]
        if platform.system() != "Windows" and shutil.which(executable) is None:
            raise HTTPException(status_code=404, detail=f"No se encontró el ejecutable autorizado: {executable}")
        try:
            subprocess.Popen(
                command,
                shell=False,
                close_fds=(platform.system() != "Windows"),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"No se pudo abrir la aplicación: {exc.strerror or type(exc).__name__}") from exc
        return {"status": "launched", "app": request.app, "platform": platform.system()}

    @app.post("/v1/browser/open", dependencies=[Depends(require_token)])
    async def open_browser(request: OpenUrlRequest) -> dict[str, str]:
        url = str(request.url)
        if not url.startswith(("https://", "http://")):
            raise HTTPException(status_code=400, detail="Solo se permiten URL http/https.")
        try:
            opened = webbrowser.open(url, new=2, autoraise=True)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="No se pudo abrir el navegador predeterminado.") from exc
        if not opened:
            raise HTTPException(status_code=500, detail="El sistema no confirmó la apertura del navegador.")
        return {"status": "opened", "url": url}

    @app.post("/v1/screen/capture", dependencies=[Depends(require_token)])
    async def capture_screen() -> dict:
        """Manual one-shot capture. No background recording and no disk persistence."""
        try:
            import mss
            from PIL import Image
        except ImportError as exc:
            raise HTTPException(
                status_code=503,
                detail="Captura no disponible. Instala los extras de desktop_agent/requirements.txt.",
            ) from exc

        try:
            with mss.mss() as screen:
                monitor = screen.monitors[1]  # primary monitor, not the virtual desktop
                shot = screen.grab(monitor)
                image = Image.frombytes("RGB", shot.size, shot.rgb)
                if image.width > config.max_capture_width:
                    new_height = round(image.height * config.max_capture_width / image.width)
                    image = image.resize((config.max_capture_width, new_height))
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=82, optimize=True)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception("Falló la captura de pantalla del agente")
            raise HTTPException(status_code=500, detail="No se pudo capturar la pantalla. Comprueba la sesión gráfica y los logs del agente.") from exc

        return {
            "status": "captured",
            "mime_type": "image/jpeg",
            "width": image.width,
            "height": image.height,
            "image_base64": base64.b64encode(buffer.getvalue()).decode("ascii"),
            "persisted": False,
            "capture_mode": "manual_one_shot",
        }

    return app


app = create_app()
