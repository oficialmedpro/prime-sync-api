#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZAR AGORA: Chamar /sync até zerar os pendentes
Use este script para sincronizar TODOS os registros pendentes rapidamente
"""
import requests
import time

SYNC_URL = "https://sincro.oficialmed.com.br/sync"
MAX_TENTATIVAS = 50

print("="*80)
print("SINCRONIZACAO RAPIDA: 8.460 registros pendentes")
print("="*80)
print(f"\nURL: {SYNC_URL}")
print(f"Tentativas maximas: {MAX_TENTATIVAS}")
print(f"Intervalo: 10 segundos entre chamadas\n")

tentativa = 1
total_sincronizado = 0

while tentativa <= MAX_TENTATIVAS:
    print(f"\n[{tentativa}/{MAX_TENTATIVAS}] Executando sync...")
    
    try:
        resp = requests.post(SYNC_URL, timeout=120)
        
        if resp.status_code == 200:
            resultado = resp.json()
            print(f"Status: {resp.status_code} OK")
            print(f"Resposta: {resultado}")
            
            # Extrair total sincronizado
            total = resultado.get('total_inseridos', 0)
            total_sincronizado += total
            
            if total == 0:
                print("\n✓ PRONTO! Nenhum registro novo.")
                break
            
        else:
            print(f"Status: {resp.status_code}")
            print(f"Resposta: {resp.text[:200]}")
        
        tentativa += 1
        time.sleep(10)  # Aguardar 10s entre chamadas
        
    except Exception as e:
        print(f"ERRO: {e}")
        tentativa += 1
        time.sleep(10)

print("\n" + "="*80)
print(f"TOTAL SINCRONIZADO: {total_sincronizado} registros")
print("="*80)
print("\nProximos passos:")
print("1. Aguarde ~30 segundos")
print("2. Execute: python comparar_firebird_supabase.py")
print("3. Verifique se chegou a 100%\n")
