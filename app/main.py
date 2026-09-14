from fastapi import FastAPI
from sqlalchemy import text
from app.core.database import engine

app = FastAPI(
    title="SGPSU",
    description="Sistema de Gestão de Processos e Suporte ao Usuário",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "message": "SGPSU API funcionando",
        "version":"0.1.0",
    }
    
@app.get("/teste-banco")
def teste_banco():
    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT 1"))
        
        return{
            "database": "conectado com sucesso",
            "resultado": resultado.scalar(),
        }