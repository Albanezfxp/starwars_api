import os
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Segurança simples para o case:
    - exige header: x-api-key
    - compara com env var: API_KEY
    - permite ignorar no local se você não setar API_KEY
    """

    async def dispatch(self, request: Request, call_next):
        required_key = os.getenv("API_KEY")

        # Se não tiver API_KEY setada, deixa rodar (modo dev/local)
        if not required_key:
            return await call_next(request)

        provided = request.headers.get("x-api-key")
        if not provided or provided != required_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        return await call_next(request)
