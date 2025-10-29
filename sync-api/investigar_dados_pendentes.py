#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Investigar se dados pendentes são NOVOS ou ANTIGOS
"""
import fdb
import requests
from datetime import datetime

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

SUPABASE_URL = 'https://agdffspstbxeqhqtltvb.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}

print("="*80)
print("INVESTIGAR DADOS PENDENTES")
print("="*80)

try:
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )

    # 1. Verificar FORMULAS_ITENS
    print("\n1. FORMULAS ITENS (352.964 pendentes)")
    print("-" * 80)

    # Último no Supabase
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
        headers=headers,
        params={'select': 'codigo_orcamento_original', 'order': 'codigo_orcamento_original.desc', 'limit': 1}
    )
    ultimo_supabase = resp.json()[0]['codigo_orcamento_original'] if resp.json() else 0

    print(f"   Último no Supabase: {ultimo_supabase}")

    cursor = conn.cursor()

    # Buscar os primeiros 10 pendentes
    cursor.execute(f"""
        SELECT FIRST 10
            A3.CODIGO_ATEND_A1,
            A1.CADASTRO_DT
        FROM ATENDIMENTO_A3 A3
        LEFT JOIN ATENDIMENTO_A1 A1 ON A3.CODIGO_ATEND_A1 = A1.CODIGO
        WHERE A3.CODIGO_ATEND_A1 > {ultimo_supabase}
        AND A3.CODIGO_ATEND_A1 IS NOT NULL
        ORDER BY A3.CODIGO_ATEND_A1
    """)

    print("\n   Primeiros 10 itens pendentes:")
    datas = []
    for row in cursor.fetchall():
        codigo, data = row
        datas.append(data)
        data_str = data.strftime('%Y-%m-%d') if data else 'SEM DATA'
        print(f"   - Código: {codigo} | Data: {data_str}")

    if datas:
        datas_validas = [d for d in datas if d]
        if datas_validas:
            mais_antiga = min(datas_validas)
            mais_recente = max(datas_validas)
            print(f"\n   Data mais antiga:  {mais_antiga.strftime('%Y-%m-%d')}")
            print(f"   Data mais recente: {mais_recente.strftime('%Y-%m-%d')}")

            # Calcular idade
            hoje = datetime.now()
            idade_dias = (hoje - mais_antiga).days
            print(f"   Idade dos dados:   {idade_dias} dias")

            if idade_dias > 30:
                print(f"\n   CONCLUSAO: Dados ANTIGOS (> 30 dias)")
                print(f"   A API incremental NAO vai sincronizar automaticamente")
                print(f"   Precisa de script de MIGRACAO INICIAL")
            else:
                print(f"\n   CONCLUSAO: Dados RECENTES (<= 30 dias)")
                print(f"   O cronjob vai sincronizar aos poucos (1000 por vez)")

    # 2. Verificar RASTREABILIDADE
    print("\n" + "="*80)
    print("2. RASTREABILIDADE (211.530 pendentes)")
    print("-" * 80)

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade",
        headers=headers,
        params={'select': 'codigo_rastreabilidade_original', 'order': 'codigo_rastreabilidade_original.desc', 'limit': 1}
    )
    ultimo_supabase = resp.json()[0]['codigo_rastreabilidade_original'] if resp.json() else 0

    print(f"   Último no Supabase: {ultimo_supabase}")

    cursor.execute(f"""
        SELECT FIRST 10
            PM.CODIGO,
            PM.DATA_PROCESSO
        FROM PROCESSO_MANIPULACAO PM
        WHERE PM.CODIGO > {ultimo_supabase}
        ORDER BY PM.CODIGO
    """)

    print("\n   Primeiros 10 registros pendentes:")
    datas = []
    for row in cursor.fetchall():
        codigo, data = row
        datas.append(data)
        data_str = data.strftime('%Y-%m-%d') if data else 'SEM DATA'
        print(f"   - Código: {codigo} | Data: {data_str}")

    if datas:
        datas_validas = [d for d in datas if d]
        if datas_validas:
            mais_antiga = min(datas_validas)
            mais_recente = max(datas_validas)
            print(f"\n   Data mais antiga:  {mais_antiga.strftime('%Y-%m-%d')}")
            print(f"   Data mais recente: {mais_recente.strftime('%Y-%m-%d')}")

            idade_dias = (datetime.now() - mais_antiga).days
            print(f"   Idade dos dados:   {idade_dias} dias")

            if idade_dias > 30:
                print(f"\n   CONCLUSAO: Dados ANTIGOS (> 30 dias)")
                print(f"   A API incremental NAO vai sincronizar automaticamente")
            else:
                print(f"\n   CONCLUSAO: Dados RECENTES (<= 30 dias)")
                print(f"   O cronjob vai sincronizar aos poucos")

    conn.close()

    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print("\nSe os dados sao ANTIGOS:")
    print("  - A API incremental NAO vai sincronizar")
    print("  - Precisa de migracao inicial/backfill")
    print("\nSe os dados sao RECENTES:")
    print("  - O cronjob vai sincronizar automaticamente")
    print("  - Tempo estimado: 3-6 dias (1000 por vez a cada 15min)")

except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()
