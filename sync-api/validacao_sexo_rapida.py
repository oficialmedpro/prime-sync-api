#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validação rápida - Quantos clientes SEM sexo no Supabase TÊM no Firebird
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
}

print("="*80)
print("VALIDACAO RAPIDA - CAMPO SEXO")
print("="*80)

# 1. Buscar amostra de 500 clientes SEM sexo no Supabase
print("\n[1/3] Buscando clientes SEM sexo no Supabase (amostra 500)...")
url = f"{SUPABASE_URL}/rest/v1/prime_clientes?sexo=is.null&ativo=eq.true&select=codigo_cliente_original&limit=500"
response = requests.get(url, headers=headers)
clientes_sem_sexo = [c['codigo_cliente_original'] for c in response.json()]

print(f"   Total na amostra: {len(clientes_sem_sexo)}")

# 2. Verificar no Firebird quantos TÊM sexo
print("\n[2/3] Verificando no Firebird quantos TEM sexo...")
conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

codigos_str = ','.join(map(str, clientes_sem_sexo))

cursor.execute(f"""
    SELECT CODIGO, NOMECLIENTE, SEXO
    FROM CLIENTE
    WHERE CODIGO IN ({codigos_str})
    AND SEXO IS NOT NULL
""")

com_sexo_fb = cursor.fetchall()
conn.close()

# 3. Análise
tem_no_fb = len(com_sexo_fb)
nao_tem_fb = len(clientes_sem_sexo) - tem_no_fb

print(f"\n[3/3] RESULTADO DA AMOSTRA:")
print(f"   Clientes analisados: {len(clientes_sem_sexo)}")
print(f"   TEM sexo no Firebird (erro): {tem_no_fb} ({tem_no_fb/len(clientes_sem_sexo)*100:.2f}%)")
print(f"   NAO TEM no Firebird (ok): {nao_tem_fb} ({nao_tem_fb/len(clientes_sem_sexo)*100:.2f}%)")

if tem_no_fb > 0:
    print(f"\n   Distribuicao dos que TEM sexo no Firebird:")
    sexo_dist = {}
    for row in com_sexo_fb[:10]:
        sexo = row[2]
        sexo_dist[sexo] = sexo_dist.get(sexo, 0) + 1
    
    for sexo, qtd in sexo_dist.items():
        print(f"      Sexo {sexo}: {qtd}")
    
    print(f"\n   Primeiros 10 clientes com erro:")
    for row in com_sexo_fb[:10]:
        print(f"      {row[0]}: {row[1][:40]} - Sexo: {row[2]}")

# 4. Estimativa total
print("\n" + "="*80)
print("ESTIMATIVA PARA TODOS OS 18.022 CLIENTES SEM SEXO:")
print("="*80)

percentual_erro = tem_no_fb / len(clientes_sem_sexo)
estimativa_total = int(18022 * percentual_erro)

print(f"Estimativa de clientes que PRECISAM correcao: ~{estimativa_total:,}")
print(f"Percentual de erro: {percentual_erro*100:.2f}%")
print("="*80)



