#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE: Validar sincronizacao corrigida com ROWID
Testa se a logica de incremento funciona corretamente
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
print("TESTE: SINCRONIZACAO CORRIGIDA COM ROWID")
print("="*80)

# 1. Buscar último ID no Supabase
print("\n1. Buscando último item no Supabase...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
    headers=headers,
    params={
        'select': 'id,codigo_atendimento_original',
        'order': 'id.desc',
        'limit': 1
    }
)

if resp.json():
    ultimo_id_supabase = resp.json()[0]['id']
    ultimo_codigo = resp.json()[0]['codigo_atendimento_original']
    print(f"   Ultimo ID: {ultimo_id_supabase}")
    print(f"   Ultimo Codigo Atendimento: {ultimo_codigo}")
else:
    ultimo_id_supabase = 0
    ultimo_codigo = 0
    print(f"   Vazio (começar do 0)")

# 2. Conectar Firebird e testar ROWID
print("\n2. Testando query com ROWID no Firebird...")
conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
cursor = conn.cursor()

# Query CORRIGIDA: buscar por CODIGO_ATEND_A1 (incremento real)
cursor.execute(f"""
    SELECT
        A3.CODIGO_ATEND_A1,
        A3.NUMEROFORMULA,
        A3.NUMEROLINHA
    FROM ATENDIMENTO_A3 A3
    WHERE A3.CODIGO_ATEND_A1 > {ultimo_codigo}
    AND A3.CODIGO_ATEND_A1 IS NOT NULL
    ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
    ROWS 10
""")

novos = cursor.fetchall()
print(f"   Encontrados: {len(novos)} registros NOVOS com CODIGO > {ultimo_codigo}")

if novos:
    print(f"\n   Primeiros 10 novos:")
    for row in novos:
        rowid, cod_atend, num_formula, num_linha = row
        print(f"     ROWID: {rowid}, Codigo: {cod_atend}, Formula: {num_formula}, Linha: {num_linha}")

# 3. Comparar com query antiga (errada)
print(f"\n3. Comparando com query ANTIGA (errada)...")
cursor.execute(f"""
    SELECT COUNT(*)
    FROM ATENDIMENTO_A3 A3
    WHERE A3.CODIGO_ATEND_A1 > {ultimo_codigo}
    AND A3.CODIGO_ATEND_A1 IS NOT NULL
""")
antigos = cursor.fetchone()[0]
print(f"   Query ANTIGA retorna: {antigos} registros")
print(f"   Query CORRIGIDA retorna: {len(novos)} registros")
print(f"   Diferenca: {abs(antigos - len(novos))} registros")

conn.close()

print("\n" + "="*80)
print("CONCLUSAO:")
print("="*80)

if len(novos) > antigos:
    print(f"✓ SUCESSO! Query com ROWID encontrou {len(novos)} (vs {antigos} da antiga)")
    print("  A correcao vai sincronizar os {len(novos)} registros pendentes!")
else:
    print(f"⚠ PROBLEMA: ROWID retornou {len(novos)}, query antiga {antigos}")
    if len(novos) == 0:
        print("  Pode ser que ja esteja sincronizado")

print("\nProxima acao: fazer deploy com a correcao\n")
