"""
Envia os arquivos de data/landing/ para o stage interno do Snowflake (@VOOS.RAW.STG_VOOS).

- VRA:        data/landing/vra/ano=AAAA/mes=MM/*.csv -> @STG_VOOS/vra/ano=AAAA/mes=MM/
- Aeroportos: data/landing/airports.csv              -> @STG_VOOS/referencias/airports/
- Empresas:   data/landing/empresas_aereas_*.csv     -> @STG_VOOS/referencias/empresas/

O PUT compacta em .gz e, com OVERWRITE = FALSE, pula o que já está no stage (idempotente).

Uso:
  uv run python ingestion/enviar_stage.py
"""

import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
LANDING = RAIZ / "data" / "landing"
STAGE = "@VOOS.RAW.STG_VOOS"

load_dotenv(RAIZ / ".env")


def conectar():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        authenticator="SNOWFLAKE_JWT",
        private_key_file=str(RAIZ / os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]),
    )


def arquivos_para_enviar():
    """Lista (arquivo local, pasta de destino no stage)."""
    envios = []
    for arquivo in sorted((LANDING / "vra").rglob("*.csv")):
        pasta_relativa = arquivo.parent.relative_to(LANDING).as_posix()  # vra/ano=2024/mes=01
        envios.append((arquivo, f"{STAGE}/{pasta_relativa}/"))
    envios.append((LANDING / "airports.csv", f"{STAGE}/referencias/airports/"))
    for arquivo in LANDING.glob("empresas_aereas_*.csv"):
        envios.append((arquivo, f"{STAGE}/referencias/empresas/"))
    return envios


def main() -> None:
    conexao = conectar()
    cursor = conexao.cursor()
    try:
        for arquivo, destino in arquivos_para_enviar():
            caminho = arquivo.as_posix()  # o PUT pede barras "/" mesmo no Windows
            cursor.execute(f"PUT 'file://{caminho}' '{destino}' AUTO_COMPRESS = TRUE OVERWRITE = FALSE")
            origem, _, _, _, _, _, status, _ = cursor.fetchone()
            print(f"{origem:40} -> {destino:45} {status}")
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    main()