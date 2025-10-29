#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE FINAL: Simular exatamente o que a API vai fazer com ROWS 5000
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

print("="*80)
print("TESTE COMPLETO: Simular API com ROWS 5000")
print("="*80)

try:
    # Buscar último código real
    print("\n1. Buscando ultimo codigo no Supabase...")
    url = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
    resp = requests.get(url, headers=headers, params={
        'select': 'codigo_atendimento_original',
        'order': 'codigo_atendimento_original.desc',
        'limit': 1
    })
    ultimo = resp.json()[0]['codigo_atendimento_original'] if resp.json() else 0
    print(f"   Ultimo: {ultimo}")
    
    # Conectar Firebird
    print("\n2. Conectando no Firebird...")
    conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
    cursor = conn.cursor()
    
    # Buscar com ROWS 5000
    print("\n3. Buscando com ROWS 5000...")
    inicio = time.time()
    
    cursor.execute(f"""
        SELECT
            A3.CODIGO_ATEND_A1,
            A3.NUMEROFORMULA,
            A3.NUMEROLINHA,
            A3.CODIGO_PRODUTO,
            EG.NOMEPRODUTO,
            A3.QUANTIDADE,
            A3.UNIDADE,
            A3.VALORCUSTO,
            A3.VALORVENDA,
            A3.OBSERVACAO
        FROM ATENDIMENTO_A3 A3
        LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
        WHERE A3.CODIGO_ATEND_A1 > {ultimo}
        AND A3.CODIGO_ATEND_A1 IS NOT NULL
        ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
        ROWS 5000
    """)
    
    resultado = cursor.fetchall()
    tempo_firebird = time.time() - inicio
    
    print(f"   Registros: {len(resultado)}")
    print(f"   Tempo: {tempo_firebird:.2f}s")
    
    if len(resultado) > 0:
        print(f"   Primeiro: {resultado[0][0]}")
        print(f"   Ultimo: {resultado[-1][0]}")
        
        # Simular preparacao de dados
        print("\n4. Preparando dados para Supabase...")
        inicio = time.time()
        
        dados = []
        for row in resultado:
            item = {
                'codigo_atendimento_original': row[0],
                'numero_formula': row[1],
                'numero_linha': row[2],
                'codigo_produto': row[3],
                'nome_produto': row[4] or 'N/A',
                'quantidade': float(row[5]) if row[5] else None,
                'unidade': row[6],
                'quantidade_calculo': float(row[5]) if row[5] else None,
                'valor_custo': float(row[7]) if row[7] else 0.0,
                'valor_venda': float(row[8]) if row[8] else 0.0,
                'observacao': row[9]
            }
            dados.append(item)
        
        tempo_preparacao = time.time() - inicio
        import json
        tamanho = len(json.dumps(dados))
        print(f"   Itens preparados: {len(dados)}")
        print(f"   Tempo: {tempo_preparacao:.2f}s")
        print(f"   Tamanho JSON: {tamanho/1024:.1f} KB")
        
        if tamanho > 500 * 1024:
            print("\n   ATENCAO: JSON muito grande! Pode dar timeout!")
            print("   Recomendacao: MANTER ROWS 1000")
            RESULTADO = "FALHOU"
        elif tempo_firebird > 20:
            print("\n   ATENCAO: Firebird lento! Mais de 20s")
            print("   Recomendacao: MANTER ROWS 1000")
            RESULTADO = "FALHOU"
        else:
            print("\n   TESTE APROVADO!")
            print("   ROWS 5000 funciona sem problemas")
            RESULTADO = "PASSOU"
        
    else:
        print("\n   Nenhum registro novo (tudo sincronizado)")
        RESULTADO = "PASSOU (sem dados)"
    
    conn.close()
    
    print("\n" + "="*80)
    print(f"RESULTADO FINAL: {RESULTADO}")
    print("="*80)
    
    if RESULTADO == "PASSOU":
        print("\nPODE FAZER COMMIT E DEPLOY!")
    else:
        print("\nNAO FAZER COMMIT! Reverter para ROWS 1000")

except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()

print()



