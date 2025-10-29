#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZAR PEDIDOS - PRIMEIRO!
Sincroniza os 231 pedidos faltando ANTES dos itens de formulas
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
print("SINCRONIZAR: PEDIDOS (231 pendentes)")
print("="*80)

try:
    # 1. Buscar último ID
    print("\n1. Buscando ultimo ID no Supabase...")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers=headers,
        params={'select': 'id', 'order': 'id.desc', 'limit': 1}
    )
    
    ultimo_id = 0
    if resp.status_code == 200:
        dados = resp.json()
        if dados and len(dados) > 0:
            ultimo_id = dados[0]['id']
    print(f"   Ultimo ID: {ultimo_id}")
    
    # 2. Buscar pedidos do Firebird
    print("\n2. Buscando pedidos do Firebird...")
    conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            A.CODIGO,
            A.CODIGO_CLIENTE,
            A.CADASTRO_DT,
            A.AVIADA_DT,
            A.ENTREGUE_DT,
            A.VALORVENDA,
            A.OBSERVACAO
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IS NOT NULL
        ORDER BY A.CODIGO
        ROWS 5000
    """)
    
    todos = cursor.fetchall()
    print(f"   Encontrados: {len(todos)}")
    
    # 3. Buscar cache de clientes
    print("\n3. Montando cache de clientes...")
    
    resp_clientes = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_clientes",
        headers=headers,
        params={'select': 'id,codigo_cliente_original', 'limit': 50000}
    )
    print(f"   Clientes HTTP: {resp_clientes.status_code}")
    cache_clientes = {}
    if resp_clientes.status_code == 200:
        dados_clientes = resp_clientes.json()
        print(f"   Clientes JSON: {len(dados_clientes) if isinstance(dados_clientes, list) else 'erro'}")
        if isinstance(dados_clientes, list):
            cache_clientes = {c['codigo_cliente_original']: c['id'] for c in dados_clientes}
    print(f"   Cache Clientes: {len(cache_clientes)}")
    
    # 4. Preparar dados
    print("\n4. Preparando pedidos...")
    dados = []
    
    for row in todos:
        cod, cod_cliente, cad_dt, avi_dt, ent_dt, valor, obs = row
        
        cliente_id = cache_clientes.get(cod_cliente)
        if not cliente_id:
            continue
        
        status_aprovacao = 'APROVADO' if avi_dt else 'NAO_APROVADO'
        status_entrega = 'ENTREGUE' if ent_dt else 'NAO_ENTREGUE'
        
        if ent_dt:
            status_geral = 'ENTREGUE'
        elif avi_dt:
            status_geral = 'APROVADO'
        else:
            status_geral = 'PENDENTE'
        
        dado = {
            'codigo_orcamento_original': cod,
            'codigo_cliente_original': cod_cliente,
            'cliente_id': cliente_id,
            'data_criacao': cad_dt.isoformat() if cad_dt else None,
            'data_aprovacao': avi_dt.isoformat() if avi_dt else None,
            'data_entrega': ent_dt.isoformat() if ent_dt else None,
            'valor_total': float(valor) if valor else 0.0,
            'observacoes': str(obs)[:500] if obs else '',
            'status_aprovacao': status_aprovacao,
            'status_entrega': status_entrega,
            'status_geral': status_geral
        }
        dados.append(dado)
    
    print(f"   Preparados: {len(dados)}")
    
    # 5. Inserir em batch (muito mais rápido)
    print(f"\n5. Inserindo {len(dados)} pedidos em batch...")
    
    # Dividir em batches de 100
    batch_size = 100
    inseridos = 0
    erros = 0
    
    for batch_idx in range(0, len(dados), batch_size):
        batch = dados[batch_idx:batch_idx + batch_size]
        
        # Usar header especial para ignorar duplicatas
        headers_batch = headers.copy()
        headers_batch['Prefer'] = 'resolution=ignore-duplicates'
        
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/prime_pedidos",
            headers=headers_batch,
            json=batch,
            timeout=60
        )
        
        if resp.status_code in [200, 201]:
            inseridos += len(batch)
            print(f"   Batch {batch_idx//batch_size + 1}: OK ({len(batch)} registros)")
        else:
            erros += len(batch)
            print(f"   Batch {batch_idx//batch_size + 1}: ERRO {resp.status_code}")
            print(f"     {resp.text[:200]}")
        
        time.sleep(0.5)
    
    conn.close()
    
    print(f"\n✓ COMPLETO: {inseridos} pedidos processados, {erros} erros")

except Exception as e:
    print(f"\n✗ ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()
