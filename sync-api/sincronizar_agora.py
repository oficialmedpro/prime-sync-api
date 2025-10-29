#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZAR AGORA: Chamar /sync até zerar os pendentes
Use este script para sincronizar TODOS os registros pendentes rapidamente
"""
import requests
import time
import json

SYNC_URL = "https://sincro.oficialmed.com.br/sync"
MAX_TENTATIVAS = 50

print("="*80)
print("SINCRONIZACAO RAPIDA: 8.431 registros pendentes")
print("="*80)
print(f"\nURL: {SYNC_URL}")
print(f"Tentativas maximas: {MAX_TENTATIVAS}")
print(f"Intervalo: 5 segundos entre chamadas\n")

tentativa = 1
total_sincronizado = 0
erros_consecutivos = 0

while tentativa <= MAX_TENTATIVAS:
    print(f"\n[{tentativa}/{MAX_TENTATIVAS}] Executando sync...")
    
    try:
        # Fazer requisição com timeout maior
        resp = requests.post(SYNC_URL, timeout=180)
        
        print(f"HTTP Status: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                resultado = resp.json()
            except:
                resultado = resp.text
            
            print(f"Resposta completa: {resultado}")
            
            if isinstance(resultado, dict):
                # Extrair total sincronizado
                total = resultado.get('total_inseridos', 0)
                total_sincronizado += total
                
                print(f"  Clientes: {resultado.get('clientes', {}).get('inseridos', 0)}")
                print(f"  Pedidos: {resultado.get('pedidos', {}).get('inseridos', 0)}")
                print(f"  Formulas: {resultado.get('formulas', {}).get('inseridos', 0)}")
                print(f"  Formulas Itens: {resultado.get('formulas_itens', {}).get('inseridos', 0)}")
                print(f"  Rastreabilidade: {resultado.get('rastreabilidade', {}).get('inseridos', 0)}")
                print(f"  Tipos Processo: {resultado.get('tipos_processo', {}).get('inseridos', 0)}")
                print(f"  TOTAL DESTA EXECUCAO: {total}")
                
                if total == 0:
                    print("\n✓ Nenhum registro novo encontrado")
                    erros_consecutivos += 1
                    if erros_consecutivos >= 3:
                        print("\n✓ 3 execucoes sem novos registros = TUDO SINCRONIZADO!")
                        break
                else:
                    erros_consecutivos = 0
            
        else:
            print(f"ERRO HTTP {resp.status_code}: {resp.text[:200]}")
            erros_consecutivos += 1
        
        tentativa += 1
        time.sleep(5)  # Aguardar 5s entre chamadas
        
    except requests.exceptions.Timeout:
        print(f"TIMEOUT (>180s) - Servidor demorando")
        tentativa += 1
        time.sleep(10)
        
    except Exception as e:
        print(f"ERRO: {e}")
        tentativa += 1
        time.sleep(10)

print("\n" + "="*80)
print(f"TOTAL SINCRONIZADO: {total_sincronizado} registros")
print("="*80)
print("\nProximos passos:")
print("1. Execute: python comparar_firebird_supabase.py")
print("2. Verifique o status atual\n")
