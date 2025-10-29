#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATUALIZACAO RAPIDA com feedback
"""
import fdb
import requests
import os
import sys
from datetime import datetime

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

print("INICIANDO ATUALIZACAO...")
sys.stdout.flush()

try:
    # 1. Buscar pedidos Supabase
    print("1. Buscando pedidos Supabase...")
    sys.stdout.flush()
    
    url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
    pedidos = []
    offset = 0
    limit = 1000
    
    while True:
        resp = requests.get(url, headers=headers, params={'select': 'id,codigo_orcamento_original', 'limit': limit, 'offset': offset})
        batch = resp.json()
        if not batch:
            break
        pedidos.extend(batch)
        offset += limit
        print(f"   Baixados: {len(pedidos)}")
        sys.stdout.flush()
        if len(batch) < limit:
            break
    
    codigos = [p['codigo_orcamento_original'] for p in pedidos]
    print(f"Total: {len(pedidos)} pedidos")
    sys.stdout.flush()
    
    # 2. Buscar Firebird em cache
    print("2. Buscando Firebird...")
    sys.stdout.flush()
    
    conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
    cursor = conn.cursor()
    
    cache = {}
    batch_size = 500
    
    for i in range(0, len(codigos), batch_size):
        batch_codes = codigos[i:i+batch_size]
        codes_str = ','.join(map(str, batch_codes))
        
        cursor.execute(f"SELECT A.CODIGO, A.CADASTRO_DT, A.AVIADA_DT, A.ENTREGUE_DT FROM ATENDIMENTO_A1 A WHERE A.CODIGO IN ({codes_str})")
        
        for row in cursor.fetchall():
            codigo, cad, avi, ent = row
            cache[codigo] = {
                'data_criacao': cad.isoformat() if cad else None,
                'data_aprovacao': avi.isoformat() if avi else None,
                'data_entrega': ent.isoformat() if ent else None
            }
        
        print(f"   Firebird: {len(cache)}/{len(pedidos)}")
        sys.stdout.flush()
    
    conn.close()
    
    # 3. Atualizar Supabase
    print("3. Atualizando Supabase...")
    sys.stdout.flush()
    
    atualizados = 0
    
    for pedido in pedidos:
        codigo = pedido['codigo_orcamento_original']
        dados = cache.get(codigo)
        
        if not dados:
            continue
        
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/prime_pedidos",
            headers=headers,
            params={'id': f"eq.{pedido['id']}"},
            json=dados
        )
        
        if resp.status_code in [200, 204]:
            atualizados += 1
            if atualizados % 100 == 0:
                print(f"   Atualizados: {atualizados}/{len(pedidos)}")
                sys.stdout.flush()
    
    print(f"\nCONCLUIDO! {atualizados} pedidos atualizados")
    
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()



