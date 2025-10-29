#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar percentual de pedidos COM data_criacao preenchida
"""
import requests

SUPABASE_URL = 'https://agdffspstbxeqhqtltvb.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Accept-Profile': 'api'
}

print("="*80)
print("VERIFICANDO data_criacao")
print("="*80)

url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"

# Total
resp_total = requests.get(url, headers={**headers, 'Prefer': 'count=exact'}, params={'select': 'id', 'limit': 0})
total = int(resp_total.headers.get('Content-Range', '0').split('/')[-1])

# Com data_criacao
resp_com_data = requests.get(url, headers={**headers, 'Prefer': 'count=exact'}, params={'select': 'id', 'data_criacao': 'not.is.null', 'limit': 0})
com_data = int(resp_com_data.headers.get('Content-Range', '0').split('/')[-1])

# Sem data_criacao
resp_sem_data = requests.get(url, headers={**headers, 'Prefer': 'count=exact'}, params={'select': 'id', 'data_criacao': 'is.null', 'limit': 0})
sem_data = int(resp_sem_data.headers.get('Content-Range', '0').split('/')[-1])

print(f"\nTotal de pedidos: {total:,}")
print(f"Com data_criacao: {com_data:,}")
print(f"Sem data_criacao: {sem_data:,}")
print(f"\nPercentual: {(com_data/total)*100:.1f}% completos")

if sem_data > 0:
    print(f"\nFALTAM {sem_data:,} pedidos para preencher data_criacao")
    print(f"Estimativa: {sem_data // 100} execucoes do cronjob")

print()



