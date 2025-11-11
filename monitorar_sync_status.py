#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitora o status da sincronização em background."""
import argparse
import codecs
import sys
import time
from datetime import datetime

import requests

# Forçar saída em UTF-8 no Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

API_URL = "http://72.60.61.40:5000"
STATUS_ENDPOINT = f"{API_URL}/sync/status"
SUMMARY_ENDPOINT = f"{API_URL}/sync/summary"


def obter_json(url, timeout=15):
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def imprimir_status(status_payload):
    status = status_payload.get('status', {})
    print("=" * 80)
    print("STATUS ATUAL DO /sync")
    print("=" * 80)
    print(f"Rodando agora........: {status.get('running')}")
    print(f"Disparo..............: {status.get('trigger')}")
    print(f"Iniciado às..........: {status.get('started_at')}")
    print(f"Finalizado às........: {status.get('finished_at')}")
    print(f"Última duração (s)...: {status.get('last_duration_seconds')}")
    print(f"Último erro..........: {status.get('last_error')}")
    print(f"Fase atual...........: {status.get('current_phase')}")
    print(f"Último heartbeat.....: {status.get('last_heartbeat')}")
    progresso = status.get('last_progress') or {}
    if progresso:
        print("Último progresso.....:")
        print(f"  - Fase............: {progresso.get('fase')}")
        print(f"  - Detalhe.........: {progresso.get('detalhe')}")
        print(f"  - Progresso.......: {progresso.get('progresso')}")
        print(f"  - Timestamp.......: {progresso.get('timestamp')}")
    if status.get('last_result'):
        resultado = status['last_result']
        print("\nResumo da última execução:")
        print(f"  - Timestamp........: {resultado.get('timestamp')}")
        print(f"  - Total inseridos..: {resultado.get('total_inseridos')}")
        print(f"  - Versão...........: {resultado.get('version')}")
        faltantes = []
        for chave in ['clientes', 'pedidos', 'formulas', 'formulas_itens', 'rastreabilidade']:
            tabela = resultado.get(chave) or {}
            restantes = tabela.get('faltantes_restantes', 0)
            if restantes:
                faltantes.append(f"{chave}={restantes}")
        if faltantes:
            print(f"  - Faltantes atuais.: {', '.join(faltantes)}")
        avisos = resultado.get('avisos')
        if avisos:
            print(f"  - Avisos...........: {avisos}")
    print("=" * 80)


def imprimir_summary():
    try:
        resumo = obter_json(SUMMARY_ENDPOINT, timeout=20)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"⚠️  Não foi possível obter resumo: {exc}")
        return

    if not resumo.get('sucesso'):
        print(f"⚠️  Resumo retornou erro: {resumo.get('erro')}")
        return

    print("\nResumo Firebird × Supabase:")
    print(f"Atualizado em........: {resumo.get('atualizado_em')}")
    print(f"Total Firebird.......: {resumo.get('total_firebird'):,}")
    print(f"Total Supabase.......: {resumo.get('total_supabase'):,}")
    print(f"Faltantes Totais.....: {resumo.get('faltantes_totais'):,}")
    print(f"Percentual Geral.....: {resumo.get('percentual_geral')}%")

    print("\nPor tabela:")
    for linha in resumo.get('tabelas', []):
                firebird_val = linha.get('firebird')
                supabase_val = linha.get('supabase')
                faltantes_val = linha.get('faltantes')
                percentual_val = linha.get('percentual')

                firebird_txt = f"{firebird_val:,}" if isinstance(firebird_val, (int, float)) else str(firebird_val)
                supabase_txt = f"{supabase_val:,}" if isinstance(supabase_val, (int, float)) else str(supabase_val)
                faltantes_txt = f"{faltantes_val:,}" if isinstance(faltantes_val, (int, float)) else str(faltantes_val)
                percentual_txt = f"{percentual_val}%" if percentual_val is not None else "N/A"

                print(
                    f" - {linha['tabela']}: Firebird={firebird_txt} | "
                    f"Supabase={supabase_txt} | Faltantes={faltantes_txt} "
                    f"({percentual_txt})"
                )


def main():
    parser = argparse.ArgumentParser(description="Monitora a execução da sincronização.")
    parser.add_argument("--intervalo", type=int, default=15, help="Intervalo em segundos entre verificações (default: 15s)")
    parser.add_argument("--max-espera", type=int, default=3600, help="Tempo máximo de espera antes de abortar (default: 3600s)")
    args = parser.parse_args()

    inicio = datetime.now()

    while True:
        try:
            payload = obter_json(STATUS_ENDPOINT)
        except requests.exceptions.RequestException as exc:
            print(f"❌ Erro ao consultar /sync/status: {exc}")
            time.sleep(args.intervalo)
            continue

        imprimir_status(payload)

        rodando = payload.get('status', {}).get('running')
        if not rodando:
            imprimir_summary()
            break

        if (datetime.now() - inicio).total_seconds() > args.max_espera:
            print("⚠️  Tempo máximo de espera excedido; abortando monitoramento.")
            break

        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
