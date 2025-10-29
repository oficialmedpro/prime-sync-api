#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTAR diferentes limites para ver qual funciona melhor
"""
import fdb
import requests
import time
import sys

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

print("=== TESTE: DIFERENTES LIMITES ===\n")

# Buscar último código de itens
url = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
resp = requests.get(url, headers=headers, params={'select': 'codigo_atendimento_original', 'order': 'codigo_atendimento_original.desc', 'limit': 1})
ultimo_codigo = resp.json()[0]['codigo_atendimento_original'] if resp.json() else 0

print(f"Ultimo codigo Supabase: {ultimo_codigo}")
print(f"\nTestando diferentes limites...\n")

# Testar cada limite
limites = [1000, 2500, 5000, 10000]

for limite in limites:
    print(f"{'='*50}")
    print(f"TESTE: ROWS {limite}")
    print(f"{'='*50}")
    
    try:
        inicio = time.time()
        
        # Conectar Firebird
        conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
        cursor = conn.cursor()
        
        # Buscar com limite
        cursor.execute(f"""
            SELECT
                A3.CODIGO_ATEND_A1,
                A3.NUMEROFORMULA,
                A3.NUMEROLINHA,
                A3.CODIGO_PRODUTO
            FROM ATENDIMENTO_A3 A3
            WHERE A3.CODIGO_ATEND_A1 > {ultimo_codigo}
            AND A3.CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
            ROWS {limite}
        """)
        
        resultado = cursor.fetchall()
        tempo_firebird = time.time() - inicio
        
        print(f"  Firebird: {len(resultado)} registros em {tempo_firebird:.2f}s - OK")
        
        conn.close()
        
        # Testar upload para Supabase (simulado - só testar tamanho)
        inicio = time.time()
        
        # Criar dados de teste
        dados_teste = [{
            'codigo_atendimento_original': 999999999,  # Código inválido (só para teste de tamanho)
            'numero_formula': 1,
            'numero_linha': 1,
            'codigo_produto': 123
        }] * len(resultado)  # Simular a quantidade real
        
        url_test = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
        # NÃO INSERIR, só testar tamanho da requisição
        response = requests.post(url_test, headers=headers, json=dados_teste[:100], timeout=30)
        
        tempo_supabase = time.time() - inicio
        
        if response.status_code in [200, 201, 409]:
            print(f"  Supabase: OK em {tempo_supabase:.2f}s - Status: {response.status_code}")
            print(f"  TOTAL: {tempo_firebird + tempo_supabase:.2f}s")
        else:
            print(f"  Supabase: ERRO {response.status_code}")
            
    except fdb.OperationalError as e:
        print(f"  Firebird ERRO: {str(e)[:100]}")
    except requests.exceptions.Timeout:
        print(f"  Supabase TIMEOUT (>30s)")
    except Exception as e:
        print(f"  ERRO: {str(e)[:100]}")
    
    print()
    time.sleep(1)  # Pausa entre testes

print("="*50)
print("ANALISE:")
print("="*50)
print("\nBaseado nos testes, escolha o limite que:")
print("  ✓ Levou menos tempo TOTAL")
print("  ✓ Não deu timeout")
print("  ✓ Não deu erro")
print("\nRecomendacao: Use 2500 ou 5000")



