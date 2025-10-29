#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATUALIZACAO RETROATIVA: Preencher data_criacao e outros campos faltantes
Atualiza TODOS os pedidos que estão com campos vazios
Data: 27/10/2025
"""

import fdb
import requests
import os
from datetime import datetime

# Configuração
FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or 'Lt-@=waIh))Ql3~'

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('VITE_SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Configure SUPABASE_URL e SUPABASE_KEY")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api',
    'Prefer': 'return=representation'
}

print("="*80)
print("ATUALIZACAO RETROATIVA: Preencher data_criacao em pedidos")
print("="*80)

try:
    # ========================================================================
    # 1. BUSCAR TODOS OS PEDIDOS NO SUPABASE COM data_criacao NULL
    # ========================================================================
    print("\n1. Buscando pedidos com data_criacao vazia no Supabase...")
    
    url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
    response = requests.get(
        url,
        headers={**headers, 'Prefer': 'count=exact'},
        params={
            'select': 'id,codigo_orcamento_original,data_criacao',
            'data_criacao': 'is.null',
            'limit': 10000  # Ajuste se tiver mais pedidos
        }
    )
    
    if response.status_code != 200:
        print(f"   ERRO ao buscar pedidos: {response.status_code}")
        exit(1)
    
    pedidos_supabase = response.json()
    total_count = int(response.headers.get('Content-Range', '0').split('/')[-1])
    
    print(f"   Encontrados: {total_count} pedidos sem data_criacao")
    
    if not pedidos_supabase:
        print("\n   Nenhum pedido para atualizar!")
        exit(0)
    
    # Extrair códigos dos pedidos
    codigos_pedidos = [p['codigo_orcamento_original'] for p in pedidos_supabase]
    print(f"   Códigos: {min(codigos_pedidos)} até {max(codigos_pedidos)}")
    
    # ========================================================================
    # 2. BUSCAR DADOS COMPLETOS NO FIREBIRD (EM LOTE COM CACHE)
    # ========================================================================
    print("\n2. Buscando dados completos no Firebird...")
    
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    
    cursor = conn.cursor()
    
    # Buscar em lote (muito mais rápido)
    codigos_str = ','.join(map(str, codigos_pedidos))
    
    cursor.execute(f"""
        SELECT
            A.CODIGO,
            A.DATA,
            A.AVIADA_DT,
            A.ENTREGUE_DT,
            A.VALORVENDA,
            A.OBSERVACAO
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO IN ({codigos_str})
    """)
    
    pedidos_firebird = cursor.fetchall()
    conn.close()
    
    print(f"   Encontrados: {len(pedidos_firebird)} pedidos no Firebird")
    
    # Criar cache (dict) para acesso rápido
    cache_firebird = {}
    for row in pedidos_firebird:
        codigo, data, aviada_dt, entregue_dt, valor_venda, observacao = row
        cache_firebird[codigo] = {
            'data_criacao': data.isoformat() if data else None,
            'data_aprovacao': aviada_dt.isoformat() if aviada_dt else None,
            'data_entrega': entregue_dt.isoformat() if entregue_dt else None,
            'valor_total': float(valor_venda) if valor_venda else 0.0,
            'observacoes': (observacao or '').strip() or None
        }
    
    # ========================================================================
    # 3. ATUALIZAR EM LOTE NO SUPABASE
    # ========================================================================
    print("\n3. Atualizando pedidos no Supabase...")
    
    atualizados = 0
    erros = 0
    sem_dados = 0
    
    # Processar em lotes de 100 (mais rápido)
    batch_size = 100
    for i in range(0, len(pedidos_supabase), batch_size):
        batch = pedidos_supabase[i:i+batch_size]
        
        for pedido in batch:
            codigo = pedido['codigo_orcamento_original']
            pedido_id = pedido['id']
            
            # Buscar dados no cache
            dados_firebird = cache_firebird.get(codigo)
            
            if not dados_firebird:
                sem_dados += 1
                continue
            
            # Atualizar no Supabase
            url_update = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
            response = requests.patch(
                url_update,
                headers=headers,
                params={'id': f'eq.{pedido_id}'},
                json=dados_firebird
            )
            
            if response.status_code in [200, 204]:
                atualizados += 1
            else:
                erros += 1
                print(f"   ERRO ao atualizar pedido {codigo}: {response.status_code}")
        
        # Progresso
        print(f"   Progresso: {min(i+batch_size, len(pedidos_supabase))}/{len(pedidos_supabase)} pedidos processados")
    
    # ========================================================================
    # 4. RESUMO
    # ========================================================================
    print("\n" + "="*80)
    print("RESUMO DA ATUALIZACAO")
    print("="*80)
    print(f"\nPedidos atualizados:        {atualizados}")
    print(f"Pedidos sem dados Firebird: {sem_dados}")
    print(f"Erros:                      {erros}")
    print(f"Total processado:           {len(pedidos_supabase)}")
    
    # ========================================================================
    # 5. VERIFICAR RESULTADO
    # ========================================================================
    print("\n" + "="*80)
    print("VERIFICANDO RESULTADO")
    print("="*80)
    
    response_check = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers={**headers, 'Prefer': 'count=exact'},
        params={
            'select': 'id',
            'data_criacao': 'is.null',
            'limit': 0
        }
    )
    
    restantes = int(response_check.headers.get('Content-Range', '0').split('/')[-1])
    
    print(f"\nPedidos ainda sem data_criacao: {restantes}")
    
    if restantes == 0:
        print("\nSUCESSO! Todos os pedidos foram atualizados!")
    else:
        print(f"\nAinda restam {restantes} pedidos para atualizar")
        print("Execute o script novamente se necessario")
    
except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n")




