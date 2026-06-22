from fastapi import Depends, HTTPException, Header
from config import settings


def require_admin_key(authorization: str | None = Header(default=None)):
    """Prüft, ob der Authorization-Bearer-Token korrekt ist.

    Admin-Endpunkte (/admin/*, /settings/*, force-keep, etc.) werden damit
    vor unbefugtem Zugriff geschützt. Der Schlüssel steht in .env unter
    SECRET_KEY und sollte nie im Klartext im Code stehen.
    """
    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(
            status_code=401,
            detail="Fehlender oder ungültiger Authorization-Header",
        )
    token = authorization[len(prefix):]
    if token != settings.secret_key:
        raise HTTPException(
            status_code=401,
            detail="Ungültiger API-Key",
        )
    return token


def optional_admin_key(authorization: str | None = Header(default=None)):
    """Liest den Admin-Key, erlaubt aber auch Aufrufe ohne Auth.

    Wird für Endpunkte verwendet, die admin-Informationen enthalten,
    aber auch öffentlich (z. B. zur Vorschau) sein sollen.
    """
    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        return None
    return authorization[len(prefix):]
