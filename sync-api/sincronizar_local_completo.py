#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZACAO LOCAL COMPLETA
Conecta direto em Firebird e Supabase
Sincroniza TUDO sem depender da API online
"""
import fdb
import requests
import time
from datetime import datetime

# Configurações
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

def sincronizar_formulas_itens():
    """Sincroniza TODOS os itens de formulas (ATENDIMENTO_A3)"""
    print("\n" + "="*80)
    print("SINCRONIZANDO: FORMULAS ITENS (ATENDIMENTO_A3)")
    print("="*80)
    
    try:
        # Conectar Firebird
        conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
        cursor = conn.cursor()
        
        # Buscar TODOS os itens COM seus pedidos
        print("\n1. Buscando itens no Firebird...")
        cursor.execute("""
            SELECT
                A3.CODIGO_ATEND_A1,
                A1.CODIGO_CLIENTE,
                A3.NUMEROFORMULA,
                A3.NUMEROLINHA,
                A3.CODIGO_PRODUTO,
                EG.NOMEPRODUTO,
                A3.QUANTIDADE,
                A3.UNIDADE,
                A3.VALORCUSTO,
                A3.VALORVENDA,
                A3.OBSERVACAO
            FROM ATENDIMENTO_A3 A3
            LEFT JOIN ATENDIMENTO_A1 A1 ON A3.CODIGO_ATEND_A1 = A1.CODIGO
            LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
            ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
        """)
        
        todos_itens = cursor.fetchall()
        print(f"   Encontrados: {len(todos_itens)} itens no Firebird")
        
        # Buscar codigos já sincronizados
        print("\n2. Buscando já sincronizados no Supabase...")
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/api.prime_formulas_itens",
            headers={**headers, 'Prefer': 'count=exact'},
            params={'select': 'codigo_atendimento_original,numero_formula,numero_linha', 'limit': 10000}
        )
        
        codigos_sync = set()
        if resp.status_code == 200:
            for item in resp.json():
                chave = (item['codigo_atendimento_original'], item['numero_formula'], item['numero_linha'])
                codigos_sync.add(chave)
        
        print(f"   Já sincronizados: {len(codigos_sync)}")
        
        # Filtrar NOVOS
        itens_novos = []
        for item in todos_itens:
            cod_atend, cod_cliente, num_form, num_linha = item[0], item[1], item[2], item[3]
            chave = (cod_atend, num_form, num_linha)
            if chave not in codigos_sync:
                itens_novos.append(item)
        
        print(f"   NOVOS para sincronizar: {len(itens_novos)}")
        
        if not itens_novos:
            print("\n   Nenhum item novo!")
            return 0
        
        # Buscar clientes em cache
        print("\n3. Montando cache de clientes...")
        resp_clientes = requests.get(
            f"{SUPABASE_URL}/rest/v1/api.prime_clientes",
            headers=headers,
            params={'select': 'id,codigo_cliente_original', 'limit': 50000}
        )
        
        cache_clientes = {}
        if resp_clientes.status_code == 200:
            for cli in resp_clientes.json():
                cache_clientes[cli['codigo_cliente_original']] = cli['id']
        
        print(f"   Cache: {len(cache_clientes)} clientes")
        
        # Buscar pedidos em cache
        print("\n4. Montando cache de pedidos...")
        resp_pedidos = requests.get(
            f"{SUPABASE_URL}/rest/v1/api.prime_pedidos",
            headers=headers,
            params={'select': 'id,codigo_orcamento_original', 'limit': 50000}
        )
        
        cache_pedidos = {}
        if resp_pedidos.status_code == 200:
            for ped in resp_pedidos.json():
                cache_pedidos[ped['codigo_orcamento_original']] = ped['id']
        
        print(f"   Cache: {len(cache_pedidos)} pedidos")
        
        # Preparar dados
        print("\n5. Preparando dados...")
        dados_itens = []
        for item in itens_novos:
            cod_atend, cod_cliente, num_form, num_linha, cod_prod, nome_prod, qtd, unidade, val_custo, val_venda, obs = item
            
            # Buscar IDs
            cliente_id = cache_clientes.get(cod_cliente)
            pedido_id = cache_pedidos.get(cod_atend)
            
            if not pedido_id:
                continue  # Pular se pedido não existe
            
            dado = {
                'codigo_atendimento_original': cod_atend,
                'numero_formula': num_form,
                'numero_linha': num_linha,
                'codigo_produto': cod_prod,
                'nome_produto': (nome_prod or 'N/A')[:255],
                'quantidade': float(qtd) if qtd else 0.0,
                'unidade': (unidade or 'u')[:50],
                'quantidade_calculo': float(qtd) if qtd else 0.0,
                'valor_custo': float(val_custo) if val_custo else 0.0,
                'valor_venda': float(val_venda) if val_venda else 0.0,
                'observacao': (obs or '')[:255] if obs else '',
                'pedido_id': pedido_id,
                'cliente_id': cliente_id
            }
            dados_itens.append(dado)
        
        # Inserir em lotes
        print(f"\n6. Inserindo {len(dados_itens)} itens...")
        batch_size = 100
        inseridos = 0
        
        for i in range(0, len(dados_itens), batch_size):
            batch = dados_itens[i:i+batch_size]
            
            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/api.prime_formulas_itens",
                headers=headers,
                json=batch,
                timeout=120
            )
            
            if resp.status_code in [200, 201]:
                inseridos += len(batch)
                print(f"   {inseridos}/{len(dados_itens)} inseridos")
            else:
                print(f"   ERRO {resp.status_code}: {resp.text[:300]}")
            
            time.sleep(1)
        
        conn.close()
        
        print(f"\n✓ COMPLETO: {inseridos} itens sincronizados!")
        return inseridos
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        return 0

def sincronizar_rastreabilidade():
    """Sincroniza rastreabilidade (PROCESSO_MANIPULACAO)"""
    print("\n" + "="*80)
    print("SINCRONIZANDO: RASTREABILIDADE (PROCESSO_MANIPULACAO)")
    print("="*80)
    
    try:
        conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
        cursor = conn.cursor()
        
        print("\n1. Buscando registros no Firebird...")
        cursor.execute("""
            SELECT
                PM.CODIGO,
                PM.TIPO_MOV,
                PM.CODIGO_MOV,
                PM.CODIGO_PROCESSO_TIPO,
                PM.CODIGO_FUNCIONARIO,
                PM.DATA_PROCESSO,
                PM.HORA_PROCESSO,
                PM.SEQUENCIA
            FROM PROCESSO_MANIPULACAO PM
            ORDER BY PM.CODIGO
        """)
        
        todos_registros = cursor.fetchall()
        print(f"   Encontrados: {len(todos_registros)}")
        
        print("\n2. Buscando ja sincronizados no Supabase...")
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/api.prime_rastreabilidade",
            headers={**headers, 'Prefer': 'count=exact'},
            params={'select': 'codigo_processo_original', 'limit': 10000}
        )
        
        codigos_sync = set()
        if resp.status_code == 200:
            for item in resp.json():
                codigos_sync.add(item['codigo_processo_original'])
        
        print(f"   Ja sincronizados: {len(codigos_sync)}")
        
        novos = [r for r in todos_registros if r[0] not in codigos_sync]
        print(f"   NOVOS: {len(novos)}")
        
        if not novos:
            return 0
        
        print(f"\n3. Inserindo {len(novos)}...")
        inseridos = 0
        
        for reg in novos:
            cod, tipo, cod_mov, cod_tipo, cod_func, dt, hora, seq = reg
            
            dado = {
                'codigo_processo_original': cod,
                'tipo_movimento': tipo,
                'codigo_movimento': cod_mov,
                'codigo_tipo_processo': cod_tipo,
                'codigo_funcionario': cod_func,
                'data_processo': dt.isoformat() if dt else None,
                'hora_processo': str(hora) if hora else None,
                'sequencia': seq
            }
            
            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/api.prime_rastreabilidade",
                headers=headers,
                json=dado,
                timeout=30
            )
            
            if resp.status_code in [200, 201]:
                inseridos += 1
                if inseridos % 100 == 0:
                    print(f"   {inseridos}/{len(novos)}")
            
            time.sleep(0.2)
        
        conn.close()
        print(f"\n✓ COMPLETO: {inseridos} sincronizados!")
        return inseridos
        
    except Exception as e:
        print(f"\nERRO: {e}")
        return 0

# EXECUTAR
if __name__ == '__main__':
    print("="*80)
    print("SINCRONIZACAO LOCAL COMPLETA")
    print("="*80)
    print(f"Inicio: {datetime.now()}")
    
    total = 0
    
    # Sincronizar formulas_itens (4.605 pendentes)
    total += sincronizar_formulas_itens()
    
    # Sincronizar rastreabilidade (3.168 pendentes)
    total += sincronizar_rastreabilidade()
    
    print("\n" + "="*80)
    print(f"TOTAL SINCRONIZADO: {total} registros")
    print(f"Fim: {datetime.now()}")
    print("="*80)
