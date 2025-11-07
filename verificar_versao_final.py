#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica versão final da API após deploy"""

import requests
import sys
import codecs

# Forçar UTF-8 no Windows
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

API_URL = "http://72.60.61.40:5000"  # IP do EasyPanel
HEALTH_ENDPOINT = f"{API_URL}/health"

print("="*70)
print("VERIFICANDO VERSAO FINAL DA API")
print("="*70)

try:
    print(f"\nChamando: {HEALTH_ENDPOINT}")
    response = requests.get(HEALTH_ENDPOINT, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        version = data.get('version', 'N/A')
        status = data.get('status', 'N/A')
        timestamp = data.get('timestamp', 'N/A')
        
        print(f"\nStatus: {status}")
        print(f"Versao: {version}")
        print(f"Timestamp: {timestamp}")
        
        versoes_validas = [
            '3.3.0-MELHORIAS-COMPLETAS',
            '3.4.0-FIX-STATUS-PEDIDOS'
        ]

        if version in versoes_validas:
            print(f"\n✅ SUCESSO! API esta rodando a versao {version}")
            print("   Todas as melhorias foram aplicadas:")
            print("   - Retry com backoff exponencial")
            print("   - Sanitizacao de dados")
            print("   - Validacao de integridade referencial")
            if version == '3.4.0-FIX-STATUS-PEDIDOS':
                print("   - Correcao do campo 'status' em pedidos faltantes")
        else:
            print(f"\n⚠️  ATENCAO! API ainda esta rodando versao antiga.")
            print(f"   Esperado: {versoes_validas[-1]}")
            print(f"   Atual: {version}")
            print("\n   Execute novamente o comando de atualizacao:")
            print("   docker service scale prime-sync-api_prime-sync=0 && sleep 5 && docker service update --image easypanel/prime-sync-api/prime-sync:latest prime-sync-api_prime-sync --force && docker service scale prime-sync-api_prime-sync=1")
    else:
        print(f"\n❌ Erro ao acessar /health: {response.status_code}")
        print(f"Resposta: {response.text[:200]}")
        sys.exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ Erro de conexao ao /health: {e}")
    print("\nVerifique se:")
    print("  1. A API esta rodando (docker service ps prime-sync-api_prime-sync)")
    print("  2. A porta 5000 esta exposta no EasyPanel")
    print("  3. O firewall permite conexoes na porta 5000")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("VERIFICACAO CONCLUIDA")
print("="*70)

