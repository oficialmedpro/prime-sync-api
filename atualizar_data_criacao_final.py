#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATUALIZACAO RETROATIVA: Preencher data_criacao com CADASTRO_DT
Atualiza TODOS os pedidos que estão com data_criacao vazia ou incorreta
Data: 27/10/2025
"""

import fdb
import requests
import os

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
print("ATUALIZACAO: Preencher data_criacao com CADASTRO_DT")
print("="*80)

try:
    # ========================================================================
    # 1. BUSCAR TODOS OS PEDIDOS NO SUPABASE
    # ========================================================================
    print("\n1. Buscando todos os pedidos no Supabase...")
    
    url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
    response = requests.get(
        url,
        headers={**headers, 'Prefer': 'count=exact'},
        params={
            'select': 'id,codigo_orcamento_original,data_criacao',
            'limit': 10000  # Ajuste se tiver mais pedidos
        }
    )
    
    if response.status_code != 200:
        print(f"   ERRO ao buscar pedidos: {response.status_code}")
        exit(1)
    
    pedidos_supabase = response.json()
    total_count = int(response.headers.get('Content-Range', '0').split('/')[-1])
    
    print(f"   Total de pedidos: {total_count}")
    
    if not pedidos_supabase:
        print("\n   Nenhum pedido encontrado!")
        exit(0)
    
    # Extrair códigos dos pedidos
    codigos_pedidos = [p['codigo_orcamento_original'] for p in pedidos_supabase]
    print(f"   Códigos: {min(codigos_pedidos)} até {max(codigos_pedidos)}")
    
    # ========================================================================
    # 2. BUSCAR CADASTRO_DT NO FIREBIRD (EM LOTE COM CACHE)
    # ========================================================================
    print("\n2. Buscando CADASTRO_DT no Firebird...")
    
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
            A.CADASTRO_DT,
            A.AVIADA_DT,
            A.ENTREGUE_DT
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO IN ({codigos_str})
    """)
    
    pedidos_firebird = cursor.fetchall()
    conn.close()
    
    print(f"   Encontrados: {len(pedidos_firebird)} pedidos no Firebird")
    
    # Criar cache (dict) para acesso rápido
    cache_firebird = {}
    for row in pedidos_firebird:
        codigo, cadastro_dt, aviada_dt, entregue_dt = row
        cache_firebird[codigo] = {
            'cadastro_dt': cadastro_dt.isoformat() if cadastro_dt else None,
            'aviada_dt': aviada_dt.isoformat() if aviada_dt else None,
            'entregue_dt': entregue_dt.isoformat() if entregue_dt else None
        }
    
    # ========================================================================
    # 3. ATUALIZAR EM LOTE NO SUPABASE
    # ========================================================================
    print("\n3. Atualizando pedidos no Supabase...")
    
    atualizados = 0
    erros = 0
    sem_dados = 0
    ja_corretos = 0
    
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
            
            # Verificar se precisa atualizar
            data_supabase = pedido.get('data_criacao')
            data_firebird = dados_firebird['cadastro_dt']
            
            if data_supabase == data_firebird:
                ja_corretos += 1
                continue
            
            # Preparar dados para atualização
            atualizacao = {
                'data_criacao': dados_firebird['cadastro_dt'],
                'data_aprovacao': dados_firebird['aviada_dt'],
                'data_entrega': dados_firebird['entregue_dt']
            }
            
            # Atualizar no Supabase
            url_update = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
            response = requests.patch(
                url_update,
                headers=headers,
                params={'id': f'eq.{pedido_id}'},
                json=atualizacao
            )
            
            if response.status_code in [200, 204]:
                atualizados += 1
            else:
                erros += 1
                print(f"   ERRO ao atualizar pedido {codigo}: {response.status_code}")
        
        # Progresso
        processados = min(i+batch_size, len(pedidos_supabase))
        porcentagem = (processados / len(pedidos_supabase)) * 100
        print(f"   Progresso: {processados}/{len(pedidos_supabase)} pedidos ({porcentagem:.1f}%)")
    
    # ========================================================================
    # 4. RESUMO
    # ========================================================================
    print("\n" + "="*80)
    print("RESUMO DA ATUALIZACAO")
    print("="*80)
    print(f"\nTotal de pedidos processados: {len(pedidos_supabase)}")
    print(f"Pedidos atualizados:          {atualizados}")
    print(f"Pedidos ja corretos:         {ja_corretos}")
    print(f"Pedidos sem dados Firebird:  {sem_dados}")
    print(f"Erros:                       {erros}")
    
    if atualizados > 0:
        print(f"\nSUCESSO! {atualizados} pedidos foram atualizados!")
    
    # ========================================================================
    # 5. VERIFICAR RESULTADO
    # ========================================================================
    print("\n" + "="*80)
    print("VERIFICANDO RESULTADO")
    print("="*80)
    
    # Pedidos sem data_criacao
    response_check = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers={**headers, 'Prefer': 'count=exact'},
        params={
            'select': 'id',
            'data_criacao': 'is.null',
            'limit': 0
        }
    )
    
    sem_data_criacao = int(response_check.headers.get('Content-Range', '0').split('/')[-1])
    
    print(f"\nPedidos sem data_criacao: {sem_data_criacao}")
    
    if sem_data_criacao == 0:
        print("\nPERFEITO! Todos os pedidos tem data_criacao preenchida!")
    else:
        print(f"\nAinda restam {sem_data_criacao} pedidos sem data_criacao")
        print("Execute o script novamente se necessario")
    
    # Estatisticas
    print("\n" + "="*80)
    print("ESTATISTICAS FINAIS")
    print("="*80)
    
    # Total com data_criacao
    response_total = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers={**headers, 'Prefer': 'count=exact'},
        params={
            'select': 'id',
            'limit': 0
        }
    )
    
    total_pedidos = int(response_total.headers.get('Content-Range', '0').split('/')[-1])
    pedidos_com_data = total_pedidos - sem_data_criacao
    porcentagem_com_data = (pedidos_com_data / total_pedidos * 100) if total_pedidos > 0 else 0
    
    print(f"\nTotal de pedidos:      {total_pedidos}")
    print(f"Com data_criacao:      {pedidos_com_data} ({porcentagem_com_data:.1f}%)")
    print(f"Sem data_criacao:      {sem_data_criacao} ({100-porcentagem_com_data:.1f}%)")
    
except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n")

