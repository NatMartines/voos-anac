"""
Baixa os arquivos mensais do VRA (Voo Regular Ativo) da ANAC.

- Um arquivo CSV por mês, salvo em data/landing/vra/ano=AAAA/mes=MM/
- Idempotente: se o arquivo do mês já existe, ele é pulado (use --force para baixar de novo)

Uso:
  uv run python ingestion/baixar_vra.py
  uv run python ingestion/baixar_vra.py --ano 2024 --meses 1 2 3
"""

import argparse
import time
from pathlib import Path
from urllib.parse import quote

import requests

BASE_URL = "https://sistemas.anac.gov.br/dadosabertos/Voos e operações aéreas/Voo Regular Ativo (VRA)"
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
PASTA_DESTINO = Path(__file__).resolve().parent.parent / "data" / "landing" / "vra"


def montar_url(ano: int, mes: int) -> str:
    """Ex.: .../2024/01 - Janeiro/VRA_20241.csv (o arquivo não tem zero à esquerda no mês)."""
    pasta_mes = f"{mes:02d} - {MESES[mes - 1]}"
    arquivo = f"VRA_{ano}{mes}.csv"
    caminho = f"{BASE_URL}/{ano}/{pasta_mes}/{arquivo}"
    # quote troca espaço, acento e parênteses pelos códigos que a URL aceita (%20, %C3%A7...)
    return quote(caminho, safe=":/")


def baixar_mes(ano: int, mes: int, force: bool) -> str:
    destino = PASTA_DESTINO / f"ano={ano}" / f"mes={mes:02d}" / f"VRA_{ano}{mes:02d}.csv"
    if destino.exists() and not force:
        return f"{ano}-{mes:02d}: já existe, pulando"

    url = montar_url(ano, mes)
    for tentativa in range(1, 4):  # até 3 tentativas, porque o site às vezes falha
        try:
            resposta = requests.get(url, timeout=120)
            resposta.raise_for_status()
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(resposta.content)
            tamanho_mb = len(resposta.content) / 1024 / 1024
            return f"{ano}-{mes:02d}: baixado ({tamanho_mb:.1f} MB)"
        except requests.RequestException as erro:
            print(f"{ano}-{mes:02d}: tentativa {tentativa} falhou ({erro})")
            time.sleep(5 * tentativa)
    return f"{ano}-{mes:02d}: ERRO, não foi possível baixar"


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa os arquivos VRA da ANAC")
    parser.add_argument("--ano", type=int, default=2024)
    parser.add_argument("--meses", type=int, nargs="+", default=list(range(1, 13)))
    parser.add_argument("--force", action="store_true", help="baixa de novo mesmo se já existir")
    args = parser.parse_args()

    for mes in args.meses:
        print(baixar_mes(args.ano, mes, args.force))


if __name__ == "__main__":
    main()