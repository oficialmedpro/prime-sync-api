#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZAR FORMULAS ITENS - SIMPLES
Apenas 1 tabela, logs detalhados, mostra cada erro
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
print("SINCRONIZAR: FORMULAS ITENS (4.605 pendentes)")
print("="*80)

try:
    # 1. Buscar último ID
    print("\n1. Buscando ultimo ID no Supabase...")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
        headers=headers,
        params={'select': 'id', 'order': 'id.desc', 'limit': 1}
    )
    
    ultimo_id = 0
    if resp.status_code == 200:
        dados = resp.json()
        if dados and len(dados) > 0:
            ultimo_id = dados[0]['id']
    print(f"   Ultimo ID: {ultimo_id}")
    
    # 2. Buscar do Firebird
    print("\n2. Buscando itens do Firebird...")
    conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT
            A3.CODIGO_ATEND_A1,
            A3.NUMEROFORMULA,
            A3.NUMEROLINHA,
            A3.CODIGO_PRODUTO,
            COALESCE(EG.NOMEPRODUTO, 'SEM NOME'),
            COALESCE(A3.QUANTIDADE, 0),
            COALESCE(A3.UNIDADE, 'u'),
            COALESCE(A3.VALORCUSTO, 0),
            COALESCE(A3.VALORVENDA, 0),
            COALESCE(A3.OBSERVACAO, ''),
            A1.CODIGO_CLIENTE
        FROM ATENDIMENTO_A3 A3
        LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
        LEFT JOIN ATENDIMENTO_A1 A1 ON A3.CODIGO_ATEND_A1 = A1.CODIGO
        ORDER BY A3.CODIGO_ATEND_A1
        ROWS 5000
    """)
    
    todos = cursor.fetchall()
    print(f"   Encontrados: {len(todos)}")
    
    # 3. Buscar cache de pedidos e clientes (COM PAGINAÇÃO)
    print("\n3. Montando cache...")
    
    # Buscar TODOS os pedidos com paginação
    cache_pedidos = {}
    offset = 0
    while True:
        resp_pedidos = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_pedidos",
            headers=headers,
            params={'select': 'id,codigo_orcamento_original', 'offset': offset, 'limit': 1000}
        )
        if resp_pedidos.status_code == 200:
            dados_pedidos = resp_pedidos.json()
            if not dados_pedidos:
                break
            for p in dados_pedidos:
                cache_pedidos[p['codigo_orcamento_original']] = p['id']
            offset += 1000
        else:
            print(f"   ERRO Pedidos: {resp_pedidos.status_code}")
            break
    print(f"   Cache Pedidos: {len(cache_pedidos)}")
    
    # Buscar TODOS os clientes com paginação
    cache_clientes = {}
    offset = 0
    while True:
        resp_clientes = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_clientes",
            headers=headers,
            params={'select': 'id,codigo_cliente_original', 'offset': offset, 'limit': 1000}
        )
        if resp_clientes.status_code == 200:
            dados_clientes = resp_clientes.json()
            if not dados_clientes:
                break
            for c in dados_clientes:
                cache_clientes[c['codigo_cliente_original']] = c['id']
            offset += 1000
        else:
            print(f"   ERRO Clientes: {resp_clientes.status_code}")
            break
    print(f"   Cache Clientes: {len(cache_clientes)}")
    
    # Buscar TODAS as fórmulas com paginação
    cache_formulas = {}
    offset = 0
    while True:
        resp_formulas = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_formulas",
            headers=headers,
            params={'select': 'id,codigo_orcamento_original,numero_formula', 'offset': offset, 'limit': 1000}
        )
        if resp_formulas.status_code == 200:
            dados_formulas = resp_formulas.json()
            if not dados_formulas:
                break
            for f in dados_formulas:
                cache_formulas[(f['codigo_orcamento_original'], f['numero_formula'])] = f['id']
            offset += 1000
        else:
            print(f"   ERRO Formulas: {resp_formulas.status_code}")
            break
    print(f"   Cache Formulas: {len(cache_formulas)}")
    
    # 4. Preparar dados
    print("\n4. Preparando dados...")
    dados = []
    
    for row in todos:
        cod_atend, num_form, num_linha, cod_prod, nome_prod, qtd, unidade, val_custo, val_venda, obs, cod_cliente = row
        
        pedido_id = cache_pedidos.get(cod_atend)
        cliente_id = cache_clientes.get(cod_cliente)
        formula_id = cache_formulas.get((cod_atend, num_form))
        
        if not pedido_id:
            continue
        
        # Não adicionar item se não tiver fórmula
        if not formula_id:
            continue
        
        dado = {
            'formula_id': formula_id,
            'pedido_id': pedido_id,
            'codigo_atendimento_original': cod_atend,
            'numero_formula': num_form,
            'numero_linha': num_linha,
            'codigo_produto': cod_prod,
            'nome_produto': str(nome_prod)[:255],
            'quantidade': float(qtd),
            'unidade': str(unidade)[:50],
            'quantidade_calculo': float(qtd),
            'valor_custo': float(val_custo),
            'valor_venda': float(val_venda),
            'observacao': str(obs)[:255]
        }
        dados.append(dado)
    
    print(f"   Preparados: {len(dados)}")
    
    # 5. Inserir
    print(f"\n5. Inserindo {len(dados)} itens...")
    inseridos = 0
    erros = 0
    
    for i, dado in enumerate(dados):
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
            headers=headers,
            json=dado,
            timeout=30
        )
        
        if resp.status_code in [200, 201]:
            inseridos += 1
        else:
            erros += 1
            print(f"   ERRO {resp.status_code}: {resp.text[:100]}")
        
        if (i+1) % 100 == 0:
            print(f"   {i+1}/{len(dados)}: {inseridos} OK, {erros} ERRO")
        
        time.sleep(0.1)
    
    conn.close()
    
    print(f"\n✓ COMPLETO: {inseridos} inseridos, {erros} erros")

except Exception as e:
    print(f"\n✗ ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()
