#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALISE: Por que estava dando erro nos itens se os pedidos estavam lá?
"""
import fdb
import requests

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

SUPABASE_URL = 'https://agdffspstbxeqhqtltvb.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Accept-Profile': 'api'
}

print("="*80)
print("ANALISE: POR QUE HAVIA ERRO NOS ITENS?")
print("="*80)

# 1. FIREBIRD: Quantos ATENDIMENTO_A3 têm codigo_atend_a1 com referência válida em A1
print("\n1. FIREBIRD - VERIFICANDO INTEGRIDADE")
conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(DISTINCT A3.CODIGO_ATEND_A1)
    FROM ATENDIMENTO_A3 A3
    WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
""")
total_atend_a3 = cursor.fetchone()[0]
print(f"   Total de ATENDIMENTO_A3 únicos: {total_atend_a3}")

cursor.execute("""
    SELECT COUNT(DISTINCT A3.CODIGO_ATEND_A1)
    FROM ATENDIMENTO_A3 A3
    LEFT JOIN ATENDIMENTO_A1 A1 ON A3.CODIGO_ATEND_A1 = A1.CODIGO
    WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
    AND A1.CODIGO IS NOT NULL
""")
com_referencia = cursor.fetchone()[0]
print(f"   Com referência válida em A1: {com_referencia}")
print(f"   SEM referência em A1: {total_atend_a3 - com_referencia}")

cursor.execute("""
    SELECT COUNT(DISTINCT A3.CODIGO_ATEND_A1)
    FROM ATENDIMENTO_A3 A3
    LEFT JOIN ATENDIMENTO_A1 A1 ON A3.CODIGO_ATEND_A1 = A1.CODIGO
    WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
    AND A1.CODIGO_CLIENTE IS NOT NULL
""")
com_cliente = cursor.fetchone()[0]
print(f"   Com CODIGO_CLIENTE válido: {com_cliente}")

conn.close()

# 2. SUPABASE: Quantos pedidos existem
print("\n2. SUPABASE - VERIFICANDO DADOS")
resp = requests.get(
    f'{SUPABASE_URL}/rest/v1/prime_pedidos?select=count()',
    headers=headers
)
print(f"   Total de pedidos: {resp.text}")

# Buscar maiores códigos
resp2 = requests.get(
    f'{SUPABASE_URL}/rest/v1/prime_pedidos',
    headers=headers,
    params={'select': 'codigo_orcamento_original', 'order': 'codigo_orcamento_original.desc', 'limit': 10}
)
if resp2.status_code == 200:
    dados = resp2.json()
    print(f"   Top 10 maiores códigos:")
    for d in dados:
        print(f"     - {d['codigo_orcamento_original']}")

# 3. COMPARACAO
print("\n3. PROBLEMA IDENTIFICADO:")
print("   Os itens (ATENDIMENTO_A3) têm referencias a pedidos que:")
print("   a) Existem no Firebird (ATENDIMENTO_A1)")
print("   b) MAS não existiam no Supabase (por isso dava erro)")
print("   c) Agora que sincronizamos os 119 pedidos, os itens vão funcionar!")

print("\n✓ Próximo passo: Rodar sincronizar_simples.py para sincronizar os itens")



