from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


def crear_token(data: dict):
    datos = data.copy()

    expiracion = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    datos.update({"exp": expiracion})

    return jwt.encode(
        datos,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verificar_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None