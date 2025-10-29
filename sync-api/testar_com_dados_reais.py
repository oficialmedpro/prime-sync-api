#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTAR com dados REAIS pendentes
"""
import fdb
import requests
import time

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

SUPABASE_URL = 'https://agdffspstbxeqhqtltvb.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api'
}

print("=== TESTE COM DADOS REAIS PENDENTES ===\n")

# Buscar último código do SUPABASE
url = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
resp = requests.get(url, headers=headers, params={'select': 'codigo_atendimento_original', 'order': 'codigo_atendimento_original.desc', 'limit': 1})
ultimo_supabase = resp.json()[0]['codigo_atendimento_original'] if resp.json() else 0

print(f"Ultimo codigo Supabase: {ultimo_supabase}")

# Conectar no Firebird para ver quanto tem PARA CIMA
conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
cursor = conn.cursor()

# Contar total pendente (sem limite)
cursor.execute(f"""
    SELECT COUNT(*)
    FROM ATENDIMENTO_A3 A3
    WHERE A3.CODIGO_ATEND_A1 > {ultimo_supabase}
    AND A3.CODIGO_ATEND_A1 IS NOT NULL
""")
total_pendente = cursor.fetchone()[0]

print(f"Total PENDENTE no Firebird: {total_pendente:,} registros\n")

# Buscar o PRIMEIRO código pendente (menor que está pendente)
cursor.execute(f"""
    SELECT FIRST 1 A3.CODIGO_ATEND_A1
    FROM ATENDIMENTO_A3 A3
    WHERE A3.CODIGO_ATEND_A1 > {ultimo_supabase}
    AND A3.CODIGO_ATEND_A1 IS NOT NULL
    ORDER BY A3.CODIGO_ATEND_A1 ASC
""")
primeiro_pendente = cursor.fetchone()[0] if cursor.fetchone() else 0

print(f"Primeiro pendente: {primeiro_pendente}")
print(f"Ultimo do Supabase: {ultimo_supabase}")
print(f"Diferenca: {primeiro_pendente - ultimo_supabase:,} codigos\n")

# Testar diferentes limites
limites = [1000, 2000, 5000, 10000]

for limite in limites:
    print(f"{'='*50}")
    print(f"TESTE: ROWS {limite}")
    print(f"{'='*50}")
    
    try:
        inicio = time.time()
        
        cursor.execute(f"""
            SELECT
                A3.CODIGO_ATEND_A1,
                A3.NUMEROFORMULA,
                A3.NUMEROLINHA,
                A3.CODIGO_PRODUTO,
                EG.NOMEPRODUTO,
                A3.QUANTIDADE,
                A3.UNIDADE
            FROM ATENDIMENTO_A3 A3
            LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
            WHERE A3.CODIGO_ATEND_A1 > {ultimo_supabase}
            AND A3.CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
            ROWS {limite}
        """)
        
        resultado = cursor.fetchall()
        tempo_firebird = time.time() - inicio
        
        print(f"  Firebird: {len(resultado)} registros em {tempo_firebird:.2f}s")
        
        if len(resultado) > 0:
            print(f"  Primeiro: {resultado[0][0]}")
            print(f"  Ultimo: {resultado[-1][0]}")
        
    except Exception as e:
        print(f"  ERRO: {str(e)[:100]}")
        import traceback
        traceback.print_exc()
    
    print()

conn.close()

print("="*50)
print("RECOMENDACAO:")
print("="*50)
print(f"\nCom {total_pendente:,} registros pendentes:")
print(f"  - ROWS 1000 = {total_pendente // 1000} execucoes do cronjob")
print(f"  - ROWS 2000 = {total_pendente // 2000} execucoes do cronjob")
print(f"  - ROWS 5000 = {total_pendente // 5000} execucoes do cronjob")
print(f"  - ROWS 10000 = {total_pendente // 10000} execucoes do cronjob")




