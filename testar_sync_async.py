#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste assíncrono da sincronização - não espera resposta"""

import requests
import sys
import codecs

# Forçar UTF-8 no Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

API_URL = "http://72.60.61.40:5000"
SYNC_ENDPOINT = f"{API_URL}/sync"
API_TOKEN = 'prime-sync-2025-xY9kL2mP4nQ8wR5t'

headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

print("="*70)
print("INICIANDO SINCRONIZACAO (ASSINCRONA)")
print("="*70)

print(f"\nChamando: {SYNC_ENDPOINT}")
print("A sincronizacao sera executada em background.")
print("Verifique os logs do EasyPanel para acompanhar o progresso.\n")

try:
    # Fazer requisição sem esperar resposta completa
    response = requests.post(
        SYNC_ENDPOINT, 
        headers=headers, 
        timeout=10,  # Timeout curto apenas para iniciar
        stream=True  # Usar stream para não esperar resposta completa
    )
    
    print(f"Status HTTP inicial: {response.status_code}")
    
    if response.status_code in (200, 202):
        print("✅ Sincronizacao iniciada com sucesso!")
        print("\nA sincronizacao esta rodando em background.")
        print("Para verificar o progresso:")
        print("  1. Acesse o EasyPanel")
        print("  2. Vá em Logs do serviço prime-sync-api")
        print("  3. Acompanhe os logs em tempo real")
        print("\nOu aguarde alguns minutos e execute:")
        print("  py comparar_firebird_supabase.py")
        print("  para verificar se os dados foram sincronizados")
    else:
        print(f"❌ Erro HTTP: {response.status_code}")
        print(f"Resposta: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("⚠️  Timeout ao iniciar (normal se a sincronizacao demorar)")
    print("   A sincronizacao pode estar rodando em background.")
    print("   Verifique os logs do EasyPanel.")
    
except requests.exceptions.ConnectionError as e:
    print(f"❌ Erro de conexao: {e}")
    print("\nVerifique:")
    print("  1. Se a API esta rodando (docker service ps prime-sync-api_prime-sync)")
    print("  2. Se a porta 5000 esta exposta no EasyPanel")
    print("  3. Os logs do EasyPanel para ver se ha erros")
    
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)


