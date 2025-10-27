#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Teste - Validar Correção de Sincronização
Data: 27/10/2025
Uso: python testar_correcao_local.py
"""

import requests
import os
from datetime import datetime, timedelta

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Ler da env ou usar valores padrão
SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('VITE_SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERRO: Configure as variáveis de ambiente:")
    print("   SUPABASE_URL ou VITE_SUPABASE_URL")
    print("   SUPABASE_KEY ou VITE_SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api'
}

# ============================================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================================

def print_header(texto):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*80)
    print(f"  {texto}")
    print("="*80)

def print_status(ok, mensagem):
    """Imprime status com emoji"""
    emoji = "✅" if ok else "❌"
    print(f"{emoji} {mensagem}")

def verificar_registros_corrompidos():
    """Verifica se existem registros com códigos absurdos"""
    print_header("1️⃣ VERIFICANDO REGISTROS CORROMPIDOS")
    
    # Clientes
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
    response = requests.get(
        url,
        headers=headers,
        params={
            'select': 'id,codigo_cliente_original,nome,created_at',
            'codigo_cliente_original': 'gt.500000',
            'order': 'codigo_cliente_original.desc'
        }
    )
    
    if response.status_code == 200:
        registros = response.json()
        if registros:
            print_status(False, f"Encontrados {len(registros)} clientes com códigos suspeitos:")
            for r in registros:
                print(f"   → ID: {r['id']}, Código: {r['codigo_cliente_original']}, Nome: {r.get('nome', 'N/A')}")
            return False
        else:
            print_status(True, "Nenhum cliente com código suspeito encontrado")
            return True
    else:
        print_status(False, f"Erro ao consultar Supabase: {response.status_code}")
        return False

def verificar_ultimo_codigo_real():
    """Verifica qual é o último código REAL de cliente"""
    print_header("2️⃣ VERIFICANDO ÚLTIMO CÓDIGO REAL")
    
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
    response = requests.get(
        url,
        headers=headers,
        params={
            'select': 'codigo_cliente_original,nome,created_at',
            'codigo_cliente_original': 'lt.500000',  # Códigos normais
            'order': 'codigo_cliente_original.desc',
            'limit': 5
        }
    )
    
    if response.status_code == 200:
        registros = response.json()
        if registros:
            ultimo = registros[0]
            print_status(True, f"Último código real: {ultimo['codigo_cliente_original']}")
            print(f"   → Nome: {ultimo.get('nome', 'N/A')}")
            print(f"   → Criado em: {ultimo['created_at']}")
            print(f"\n   📋 Últimos 5 clientes:")
            for r in registros:
                print(f"      {r['codigo_cliente_original']} - {r.get('nome', 'N/A')[:40]}")
            return ultimo['codigo_cliente_original']
        else:
            print_status(False, "Nenhum cliente encontrado")
            return 0
    else:
        print_status(False, f"Erro ao consultar Supabase: {response.status_code}")
        return 0

def verificar_sincronizacao_recente():
    """Verifica se houve sincronização nas últimas 24h"""
    print_header("3️⃣ VERIFICANDO SINCRONIZAÇÃO RECENTE")
    
    tabelas = [
        ('prime_clientes', 'codigo_cliente_original'),
        ('prime_pedidos', 'codigo_orcamento_original'),
        ('prime_formulas', 'codigo_orcamento_original'),
        ('prime_formulas_itens', 'codigo_atendimento_original'),
        ('prime_rastreabilidade', 'codigo_processo_original'),
        ('prime_tipos_processo', 'codigo_tipo_original')
    ]
    
    resultados = []
    
    for tabela, campo_codigo in tabelas:
        url = f"{SUPABASE_URL}/rest/v1/{tabela}"
        
        # Total
        response_total = requests.get(
            url,
            headers={**headers, 'Prefer': 'count=exact'},
            params={'select': 'id', 'limit': 0}
        )
        
        total = 0
        if response_total.status_code == 200:
            total = int(response_total.headers.get('Content-Range', '0').split('/')[-1])
        
        # Últimas 24h
        data_limite = (datetime.now() - timedelta(hours=24)).isoformat()
        response_24h = requests.get(
            url,
            headers={**headers, 'Prefer': 'count=exact'},
            params={
                'select': 'id',
                'created_at': f'gte.{data_limite}',
                'limit': 0
            }
        )
        
        ultimas_24h = 0
        if response_24h.status_code == 200:
            ultimas_24h = int(response_24h.headers.get('Content-Range', '0').split('/')[-1])
        
        # Último código
        response_ultimo = requests.get(
            url,
            headers=headers,
            params={
                'select': campo_codigo,
                'order': f'{campo_codigo}.desc',
                'limit': 1
            }
        )
        
        ultimo_codigo = 0
        if response_ultimo.status_code == 200:
            dados = response_ultimo.json()
            if dados:
                ultimo_codigo = dados[0][campo_codigo]
        
        status_ok = ultimas_24h > 0 or tabela in ['prime_clientes', 'prime_tipos_processo']
        emoji = "✅" if status_ok else "⚠️"
        
        print(f"\n{emoji} {tabela}")
        print(f"   Total: {total:,} registros")
        print(f"   Últimas 24h: {ultimas_24h} registros")
        print(f"   Último código: {ultimo_codigo}")
        
        resultados.append({
            'tabela': tabela,
            'total': total,
            'ultimas_24h': ultimas_24h,
            'ultimo_codigo': ultimo_codigo,
            'ok': status_ok
        })
    
    return resultados

def verificar_duplicatas_tipos_processo():
    """Verifica se há duplicatas em prime_tipos_processo"""
    print_header("4️⃣ VERIFICANDO DUPLICATAS EM TIPOS_PROCESSO")
    
    url = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
    response = requests.get(
        url,
        headers=headers,
        params={'select': 'id,codigo_tipo_original,nome_processo,created_at'}
    )
    
    if response.status_code == 200:
        registros = response.json()
        
        # Agrupar por código
        grupos = {}
        for r in registros:
            codigo = r['codigo_tipo_original']
            if codigo not in grupos:
                grupos[codigo] = []
            grupos[codigo].append(r)
        
        # Encontrar duplicatas
        duplicatas = {k: v for k, v in grupos.items() if len(v) > 1}
        
        if duplicatas:
            print_status(False, f"Encontradas {len(duplicatas)} códigos duplicados:")
            for codigo, regs in duplicatas.items():
                print(f"\n   Código {codigo} ({len(regs)} registros):")
                for r in regs:
                    print(f"      → ID: {r['id']}, Nome: {r.get('nome_processo', 'N/A')}, Criado: {r['created_at']}")
            return False
        else:
            print_status(True, "Nenhuma duplicata encontrada")
            return True
    else:
        print_status(False, f"Erro ao consultar Supabase: {response.status_code}")
        return False

def testar_endpoint_sync():
    """Testa o endpoint /sync da API"""
    print_header("5️⃣ TESTANDO ENDPOINT DE SINCRONIZAÇÃO")
    
    url = "https://sincro.oficialmed.com.br/sync"
    
    print("🔄 Chamando endpoint /sync...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            dados = response.json()
            print_status(True, "Endpoint respondeu com sucesso!")
            
            if 'clientes' in dados:
                print(f"\n   📊 Clientes: {dados['clientes']}")
            if 'pedidos' in dados:
                print(f"   📊 Pedidos: {dados['pedidos']}")
            if 'tipos_processo' in dados:
                print(f"   📊 Tipos Processo: {dados['tipos_processo']}")
            if 'total_inseridos' in dados:
                print(f"\n   ✅ Total sincronizado: {dados['total_inseridos']} registros")
            
            return True
        else:
            print_status(False, f"Endpoint retornou erro: {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print_status(False, "Timeout ao chamar endpoint (>60s)")
        return False
    except Exception as e:
        print_status(False, f"Erro ao chamar endpoint: {e}")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*15 + "🔍 TESTE DE VALIDAÇÃO DE SINCRONIZAÇÃO" + " "*24 + "║")
    print("║" + " "*20 + "Prime/Firebird → Supabase" + " "*32 + "║")
    print("╚" + "═"*78 + "╝")
    
    print(f"\n⏰ Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔗 Supabase URL: {SUPABASE_URL}")
    
    # Executar testes
    resultado_1 = verificar_registros_corrompidos()
    ultimo_codigo = verificar_ultimo_codigo_real()
    resultados_sync = verificar_sincronizacao_recente()
    resultado_4 = verificar_duplicatas_tipos_processo()
    
    # Resumo
    print_header("📊 RESUMO GERAL")
    
    todos_ok = resultado_1 and resultado_4
    
    print(f"\n{'✅' if resultado_1 else '❌'} Registros corrompidos: {'Nenhum' if resultado_1 else 'ENCONTRADOS'}")
    print(f"{'✅' if ultimo_codigo < 500000 else '❌'} Último código real: {ultimo_codigo}")
    print(f"{'✅' if resultado_4 else '❌'} Duplicatas em tipos_processo: {'Nenhuma' if resultado_4 else 'ENCONTRADAS'}")
    
    print("\n📊 Status de sincronização por tabela:")
    for r in resultados_sync:
        emoji = "✅" if r['ok'] else "⚠️"
        print(f"{emoji} {r['tabela']}: {r['ultimas_24h']} reg (24h), último código: {r['ultimo_codigo']}")
    
    print_header("🎯 CONCLUSÃO")
    
    if not resultado_1:
        print("❌ AÇÃO NECESSÁRIA: Executar 'corrigir_cliente_corrompido.sql'")
        print("   Este script irá deletar registros com código > 500000")
    
    if not resultado_4:
        print("❌ AÇÃO NECESSÁRIA: Executar 'corrigir_tipos_processo_duplicados.sql'")
        print("   Este script irá remover duplicatas mantendo o registro mais antigo")
    
    if resultado_1 and resultado_4:
        print("✅ Tudo OK! Não há registros corrompidos ou duplicatas")
        print("   A sincronização deve estar funcionando normalmente")
        
        # Testar endpoint
        print("\n🔄 Deseja testar o endpoint de sincronização agora? (s/n)")
        resposta = input().strip().lower()
        if resposta == 's':
            testar_endpoint_sync()
    
    print(f"\n⏰ Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()

