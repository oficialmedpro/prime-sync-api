#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZAR FORMULAS - SEGUNDO!
Sincroniza as fórmulas ANTES dos itens (dependência)
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
print("SINCRONIZAR: FORMULAS (dependência para itens)")
print("="*80)

try:
    # 1. Buscar último ID (não código)
    print("\n1. Buscando ultimo ID no Supabase...")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_formulas",
        headers=headers,
        params={'select': 'id', 'order': 'id.desc', 'limit': 1}
    )
    
    ultimo_id = 0
    if resp.status_code == 200:
        dados = resp.json()
        if dados and len(dados) > 0:
            ultimo_id = dados[0]['id']
    print(f"   Ultimo ID: {ultimo_id}")
    
    # 2. Buscar fórmulas do Firebird (TODAS, sem filtro de código)
    print("\n2. Buscando fórmulas do Firebird...")
    conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT
            A2.CODIGO_ATEND_A1,
            A2.NUMEROFORMULA,
            A2.TEXTOROTULO,
            A2.POSOLOGIA,
            A2.VALORFORMULA_VENDA
        FROM ATENDIMENTO_A2 A2
        ORDER BY A2.CODIGO_ATEND_A1
        ROWS 5000
    """)
    
    todas = cursor.fetchall()
    print(f"   Encontradas: {len(todas)}")
    
    # 3. Buscar cache de pedidos (SEM LIMITE!)
    print("\n3. Montando cache de pedidos...")
    resp_pedidos = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers=headers,
        params={'select': 'id,codigo_orcamento_original'}  # Sem limit!
    )
    print(f"   Pedidos HTTP: {resp_pedidos.status_code}")
    cache_pedidos = {}
    if resp_pedidos.status_code == 200:
        dados_pedidos = resp_pedidos.json()
        print(f"   Pedidos JSON: {len(dados_pedidos) if isinstance(dados_pedidos, list) else 'erro'}")
        if isinstance(dados_pedidos, list):
            cache_pedidos = {p['codigo_orcamento_original']: p['id'] for p in dados_pedidos}
    print(f"   Cache Pedidos: {len(cache_pedidos)}")
    
    # 4. Preparar dados
    print("\n4. Preparando fórmulas...")
    dados = []
    
    for row in todas:
        cod_atend, num_form, texto_rotulo, posologia, valor = row
        
        pedido_id = cache_pedidos.get(cod_atend)
        if not pedido_id:
            continue
        
        dado = {
            'pedido_id': pedido_id,
            'codigo_orcamento_original': cod_atend,
            'numero_formula': num_form,
            'descricao': str(texto_rotulo)[:500] if texto_rotulo else '',
            'posologia': str(posologia)[:500] if posologia else '',
            'valor_formula': float(valor) if valor else 0.0
        }
        dados.append(dado)
    
    print(f"   Preparadas: {len(dados)}")
    
    # 5. Inserir em batch
    print(f"\n5. Inserindo {len(dados)} fórmulas em batch...")
    
    batch_size = 100
    inseridos = 0
    erros = 0
    
    for batch_idx in range(0, len(dados), batch_size):
        batch = dados[batch_idx:batch_idx + batch_size]
        
        headers_batch = headers.copy()
        headers_batch['Prefer'] = 'resolution=ignore-duplicates'
        
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/prime_formulas",
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
    
    print(f"\n✓ COMPLETO: {inseridos} fórmulas processadas, {erros} erros")

except Exception as e:
    print(f"\n✗ ERRO FATAL: {e}")
    import traceback
    traceback.print_exc()
