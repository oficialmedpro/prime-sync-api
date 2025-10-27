#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparar total de registros: Firebird vs Supabase
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

print("="*100)
print("COMPARACAO: FIREBIRD vs SUPABASE")
print("="*100)

# Conectar Firebird
conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
cursor = conn.cursor()

tabelas = [
    {
        'nome': 'CLIENTES',
        'firebird': 'SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1 AND CODIGO < 500000',
        'supabase': 'prime_clientes'
    },
    {
        'nome': 'PEDIDOS',
        'firebird': 'SELECT COUNT(*) FROM ATENDIMENTO_A1 WHERE CODIGO_CLIENTE IS NOT NULL',
        'supabase': 'prime_pedidos'
    },
    {
        'nome': 'FORMULAS',
        'firebird': 'SELECT COUNT(*) FROM ATENDIMENTO_A2',
        'supabase': 'prime_formulas'
    },
    {
        'nome': 'FORMULAS ITENS',
        'firebird': 'SELECT COUNT(*) FROM ATENDIMENTO_A3 WHERE CODIGO_ATEND_A1 IS NOT NULL',
        'supabase': 'prime_formulas_itens'
    },
    {
        'nome': 'RASTREABILIDADE',
        'firebird': 'SELECT COUNT(*) FROM PROCESSO_MANIPULACAO',
        'supabase': 'prime_rastreabilidade'
    },
    {
        'nome': 'TIPOS PROCESSO',
        'firebird': 'SELECT COUNT(*) FROM FORMAFARMACEUTICA_PROCESSO_TIPO',
        'supabase': 'prime_tipos_processo'
    }
]

total_firebird_geral = 0
total_supabase_geral = 0
resultados = []

for tab in tabelas:
    # Firebird
    cursor.execute(tab['firebird'])
    total_firebird = cursor.fetchone()[0]
    
    # Supabase
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{tab['supabase']}",
        headers={**headers, 'Prefer': 'count=exact'},
        params={'select': 'id', 'limit': 0}
    )
    total_supabase = int(resp.headers.get('Content-Range', '0').split('/')[-1])
    
    # Calcular percentual
    if total_firebird > 0:
        percentual = (total_supabase / total_firebird) * 100
    else:
        percentual = 0
    
    diferenca = total_firebird - total_supabase
    
    resultados.append({
        'nome': tab['nome'],
        'firebird': total_firebird,
        'supabase': total_supabase,
        'diferenca': diferenca,
        'percentual': percentual
    })
    
    total_firebird_geral += total_firebird
    total_supabase_geral += total_supabase

conn.close()

# Exibir resultados
print(f"\n{'TABELA':<20} {'FIREBIRD':>12} {'SUPABASE':>12} {'DIFERENCA':>12} {'SINCRONIZADO':>12}")
print("-" * 100)

for r in resultados:
    status = "OK" if r['diferenca'] == 0 else "FALTA"
    print(f"{r['nome']:<20} {r['firebird']:>12,} {r['supabase']:>12,} {r['diferenca']:>12,} {r['percentual']:>11.1f}% {status}")

print("-" * 100)

# Resumo geral
percentual_geral = (total_supabase_geral / total_firebird_geral * 100) if total_firebird_geral > 0 else 0

print(f"\n{'TOTAL GERAL':<20} {total_firebird_geral:>12,} {total_supabase_geral:>12,} {(total_firebird_geral - total_supabase_geral):>12,} {percentual_geral:>11.1f}%")

print("\n" + "="*100)

if total_firebird_geral == total_supabase_geral:
    print("OK! Todas as tabelas 100% sincronizadas!")
else:
    faltam = total_firebird_geral - total_supabase_geral
    print(f"FALTAM {faltam:,} registros para sincronizar ({100-percentual_geral:.1f}%)")

print("="*100 + "\n")
