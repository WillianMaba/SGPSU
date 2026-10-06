from fastapi import FastAPI
from sqlalchemy import text
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.sectors import router as sectors_router
from app.api.routes.profiles import router as profiles_router
from app.core.database import engine
from app.api.routes.permissions import router as permissions_router
from app.api.routes.profile_permissions import (
    router as profile_permissions_router,
)


app = FastAPI(
    title="SGPSU",
    description="Sistema de Gestão de Processos e Suporte ao Usuário",
    version="0.1.0",
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(sectors_router)
app.include_router(profiles_router)
app.include_router(permissions_router)
app.include_router(profile_permissions_router)


@app.get("/")
def root():
    return {
        "message": "SGPSU API funcionando",
        "version": "0.1.0",
    }


@app.get("/teste-banco")
def teste_banco():
    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT 1"))

        return {
            "database": "conectado com sucesso",
            "resultado": resultado.scalar(),
        }