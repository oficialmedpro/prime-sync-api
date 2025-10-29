#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparação lado a lado: Firebird vs Supabase
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

def contar_supabase(tabela, max_limit=50000):
    """Conta registros com paginação"""
    total = 0
    offset = 0
    while offset < max_limit:
        resp = requests.get(
            f'{SUPABASE_URL}/rest/v1/{tabela}',
            headers=headers,
            params={'select': 'id', 'limit': 1000, 'offset': offset},
            timeout=10
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        total += len(data)
        offset += 1000
    return total

print('='*100)
print('COMPARACAO FIREBIRD vs SUPABASE - LADO A LADO')
print('='*100)

conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
cursor = conn.cursor()

# Header
print(f'\nTABELA                    | FIREBIRD        | SUPABASE        | PENDENTES       | STATUS')
print('-'*100)

# 1. Clientes
cursor.execute('SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1')
fb_clientes = cursor.fetchone()[0]
sb_clientes = contar_supabase('prime_clientes', 50000)
diff_clientes = fb_clientes - sb_clientes
status = 'OK' if diff_clientes <= 0 else 'PENDENTE'
print(f'Clientes                  | {fb_clientes:>15,} | {sb_clientes:>15,} | {diff_clientes:>15,} | {status}')

# 2. Pedidos
cursor.execute('SELECT COUNT(*) FROM ATENDIMENTO_A1 WHERE CODIGO_CLIENTE IS NOT NULL')
fb_pedidos = cursor.fetchone()[0]
sb_pedidos = contar_supabase('prime_pedidos', 20000)
diff_pedidos = fb_pedidos - sb_pedidos
status = 'OK' if diff_pedidos <= 0 else 'PENDENTE'
print(f'Pedidos                   | {fb_pedidos:>15,} | {sb_pedidos:>15,} | {diff_pedidos:>15,} | {status}')

# 3. Formulas
cursor.execute('SELECT COUNT(*) FROM ATENDIMENTO_A2')
fb_formulas = cursor.fetchone()[0]
sb_formulas = contar_supabase('prime_formulas', 40000)
diff_formulas = fb_formulas - sb_formulas
status = 'OK' if diff_formulas <= 0 else 'PENDENTE'
print(f'Formulas                  | {fb_formulas:>15,} | {sb_formulas:>15,} | {diff_formulas:>15,} | {status}')

# 4. Itens
cursor.execute('SELECT COUNT(*) FROM ATENDIMENTO_A3 WHERE CODIGO_ATEND_A1 IS NOT NULL')
fb_itens = cursor.fetchone()[0]
print(f'Formulas Itens            | {fb_itens:>15,} | Aguarde...      | Aguarde...      | ...')

# 5. Rastreabilidade
cursor.execute('SELECT COUNT(*) FROM PROCESSO_MANIPULACAO')
fb_rast = cursor.fetchone()[0]
sb_rast = contar_supabase('prime_rastreabilidade', 250000)
diff_rast = fb_rast - sb_rast
status = 'OK' if diff_rast <= 10 else 'PENDENTE'
print(f'Rastreabilidade           | {fb_rast:>15,} | {sb_rast:>15,} | {diff_rast:>15,} | {status}')

# 6. Tipos
cursor.execute('SELECT COUNT(*) FROM FORMAFARMACEUTICA_PROCESSO_TIPO')
fb_tipos = cursor.fetchone()[0]
resp = requests.get(f'{SUPABASE_URL}/rest/v1/prime_tipos_processo', headers=headers, params={'select': 'id'})
sb_tipos = len(resp.json())
diff_tipos = fb_tipos - sb_tipos
status = 'OK' if diff_tipos <= 0 else 'PENDENTE'
print(f'Tipos Processo            | {fb_tipos:>15,} | {sb_tipos:>15,} | {diff_tipos:>15,} | {status}')

conn.close()

# Agora contar itens (mais lento)
print(f'\nContando Formulas Itens no Supabase (pode demorar 1-2 minutos)...')
sb_itens = contar_supabase('prime_formulas_itens', 400000)
diff_itens = fb_itens - sb_itens
status = 'OK' if diff_itens <= 0 else 'PENDENTE'
print(f'Formulas Itens            | {fb_itens:>15,} | {sb_itens:>15,} | {diff_itens:>15,} | {status}')

print('-'*100)
total_pendentes = diff_clientes + diff_pedidos + diff_formulas + diff_itens + diff_rast + diff_tipos
print(f'\nTOTAL PENDENTES: {total_pendentes:,}')
print('='*100)



