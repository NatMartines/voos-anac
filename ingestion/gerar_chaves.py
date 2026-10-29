"""
Gera o par de chaves (privada + pública) para o Snowflake.
A privada fica em keys/ (fora do Git). A pública é impressa na tela para ir ao Snowflake.

Uso:
  uv run python ingestion/gerar_chaves.py
"""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

PASTA = Path(__file__).resolve().parent.parent / "keys"
PASTA.mkdir(exist_ok=True)
arquivo_privada = PASTA / "snowflake_key.p8"

if arquivo_privada.exists():
    raise SystemExit("A chave já existe em keys/. Não vou sobrescrever.")

chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)

arquivo_privada.write_bytes(chave.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
))

publica = chave.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()

# O Snowflake quer só o miolo da chave pública, sem as linhas BEGIN/END e sem quebras
miolo = "".join(linha for linha in publica.splitlines() if "-----" not in linha)
print("Chave privada salva em:", arquivo_privada)
print("\nCole no Snowflake:\n")
print(f"ALTER USER NATMARTINES SET RSA_PUBLIC_KEY='{miolo}';")