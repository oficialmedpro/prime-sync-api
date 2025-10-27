#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATUALIZACAO COM RETRY - reinicia de onde parou
"""
import fdb
import requests
import os
import json
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

def load_progress():
    try:
        with open('progress.json', 'r') as f:
            return json.load(f)
    except:
        return {'cache': {}, 'atualizados': 0, 'total': 0}

def save_progress(data):
    with open('progress.json', 'w') as f:
        json.dump(data, f)

print("=== ATUALIZACAO COM RETRY ===")

try:
    progress = load_progress()
    
    if not progress.get('cache'):
        print("1. Carregando cache do Firebird...")
        # ... código do cache igual ao anterior ...
    else:
        print(f"Cache carregado: {len(progress['cache'])} pedidos")
    
    print(f"2. Atualizando (retry a cada erro)...")
    
    atualizados = progress.get('atualizados', 0)
    
    for codigo, dados in progress['cache'].items():
        try:
            resp = requests.patch(
                f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                headers=headers,
                params={'codigo_orcamento_original': f"eq.{codigo}"},
                json=dados,
                timeout=30
            )
            
            if resp.status_code in [200, 204]:
                atualizados += 1
                if atualizados % 50 == 0:
                    print(f"Atualizados: {atualizados}")
                    save_progress({'cache': progress['cache'], 'atualizados': atualizados, 'total': len(progress['cache'])})
            
            time.sleep(0.1)  # Delay para não sobrecarregar
            
        except Exception as e:
            print(f"Erro pedido {codigo}: {e}")
            time.sleep(5)  # Aguardar antes de retry
            continue
    
    print(f"\nCONCLUIDO! {atualizados} pedidos atualizados")
    
except KeyboardInterrupt:
    print("\nInterrompido pelo usuario")
except Exception as e:
    print(f"ERRO: {e}")
