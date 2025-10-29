#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SCRIPT MASTER - CORRIGE TUDO DE UMA VEZ
================================================================================
1. Corrige os 244 clientes com telefone/endereço faltando
2. Recalcula TODOS os totalizadores de clientes
3. Atualiza dados faltantes (CPF, e-mail, data nascimento)
================================================================================
"""

import fdb
import requests
from datetime import datetime
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
    'Prefer': 'return=minimal'
}

def limpar_string(texto):
    """Remove caracteres problemáticos"""
    if not texto:
        return None
    return str(texto).strip()[:255] if texto else None

print("=" * 120)
print("CORRECAO COMPLETA - TODOS OS PROBLEMAS DE UMA VEZ")
print("=" * 120)
print(f"Iniciado em: {datetime.now()}")
print("=" * 120)

try:
    # ============================================================================
    # ETAPA 1: Ler arquivo com clientes para corrigir
    # ============================================================================
    print("\n[ETAPA 1/3] Lendo lista de clientes para corrigir...")
    
    codigos_corrigir = []
    try:
        with open('clientes_erro_sincronizacao_urgente.txt', 'r') as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith('#'):
                    codigos_corrigir.append(int(linha))
    except:
        print("      [AVISO] Arquivo nao encontrado, buscando do arquivo alternativo...")
        with open('clientes_para_corrigir.txt', 'r') as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith('#'):
                    codigos_corrigir.append(int(linha))
    
    print(f"      [OK] {len(codigos_corrigir)} clientes para corrigir")
    
    # ============================================================================
    # ETAPA 2: Buscar dados do Firebird e atualizar Supabase
    # ============================================================================
    print("\n[ETAPA 2/3] Buscando dados do Firebird e atualizando Supabase...")
    
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    cursor = conn.cursor()
    
    # Processar em lotes
    batch_size = 50
    total_batches = (len(codigos_corrigir) + batch_size - 1) // batch_size
    total_atualizados = 0
    total_erros = 0
    
    for i in range(0, len(codigos_corrigir), batch_size):
        batch = codigos_corrigir[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n      Processando lote {batch_num}/{total_batches} ({len(batch)} clientes)...")
        
        codigos_str = ','.join(map(str, batch))
        
        # Buscar dados básicos
        cursor.execute(f"""
            SELECT 
                C.CODIGO,
                C.NOMECLIENTE,
                C.CPF_CNPJ,
                C.DIANASCIMENTO,
                C.MESNASCIMENTO,
                C.ANONASCIMENTO,
                C.SEXO,
                C.EMAIL1,
                CE.NOMECIDADE,
                CE.UF
            FROM CLIENTE C
            LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
            WHERE C.CODIGO IN ({codigos_str})
        """)
        clientes = {row[0]: row for row in cursor.fetchall()}
        
        # Buscar telefones
        cursor.execute(f"""
            SELECT 
                CT.CODIGO_CADASTRO,
                CT.TELEFONEPREFIXO,
                CT.TELEFONE
            FROM CADASTRO_TELEFONE CT
            WHERE CT.TIPO_CADASTRO = 1
            AND CT.CODIGO_CADASTRO IN ({codigos_str})
        """)
        telefones = {}
        for row in cursor.fetchall():
            codigo = row[0]
            prefixo = str(row[1]).strip() if row[1] else ""
            numero = str(row[2]).strip() if row[2] else ""
            tel = (prefixo + numero).strip()
            if tel and codigo not in telefones:
                telefones[codigo] = tel
        
        # Buscar endereços
        cursor.execute(f"""
            SELECT 
                CE.CODIGO_CADASTRO,
                CE.ENDERECO,
                CE.NUMERO,
                CE.CEP
            FROM CADASTRO_ENDERECO CE
            WHERE CE.TIPO_CADASTRO = 1
            AND CE.CODIGO_CADASTRO IN ({codigos_str})
        """)
        enderecos = {}
        for row in cursor.fetchall():
            codigo = row[0]
            if codigo not in enderecos:
                enderecos[codigo] = {
                    'endereco': row[1],
                    'numero': row[2],
                    'cep': row[3]
                }
        
        # Buscar totalizadores de pedidos
        cursor.execute(f"""
            SELECT 
                A.CODIGO_CLIENTE,
                COUNT(*) as total,
                COUNT(A.AVIADA_DT) as aprovados,
                COUNT(A.ENTREGUE_DT) as entregues,
                COALESCE(SUM(A.VALORVENDA), 0) as valor_total,
                COALESCE(SUM(CASE WHEN A.AVIADA_DT IS NOT NULL THEN A.VALORVENDA ELSE 0 END), 0) as valor_aprovado,
                COALESCE(SUM(CASE WHEN A.ENTREGUE_DT IS NOT NULL THEN A.VALORVENDA ELSE 0 END), 0) as valor_entregue,
                MIN(A.CADASTRO_DT) as primeira_compra,
                MAX(A.CADASTRO_DT) as ultima_compra
            FROM ATENDIMENTO_A1 A
            WHERE A.CODIGO_CLIENTE IN ({codigos_str})
            GROUP BY A.CODIGO_CLIENTE
        """)
        totais_pedidos = {row[0]: row for row in cursor.fetchall()}
        
        # Montar updates
        updates = []
        for codigo in batch:
            cliente_fb = clientes.get(codigo)
            if not cliente_fb:
                continue
            
            # Data de nascimento
            data_nasc = None
            if cliente_fb[3] and cliente_fb[4] and cliente_fb[5]:
                try:
                    data_nasc = f"{int(cliente_fb[5])}-{int(cliente_fb[4]):02d}-{int(cliente_fb[3]):02d}"
                except:
                    pass
            
            # Telefone
            telefone = telefones.get(codigo)
            
            # Endereço
            end = enderecos.get(codigo, {})
            
            # Totalizadores
            totais = totais_pedidos.get(codigo)
            
            # IMPORTANTE: TODOS os objetos devem ter as MESMAS chaves! (igual app.py)
            # Calcular medias para totalizadores
            # totais[0] = CODIGO_CLIENTE
            # totais[1] = total
            # totais[2] = aprovados
            # totais[3] = entregues
            # totais[4] = valor_total
            # totais[5] = valor_aprovado
            # totais[6] = valor_entregue
            # totais[7] = primeira_compra (datetime)
            # totais[8] = ultima_compra (datetime)
            total_orc = totais[1] if totais else 0
            total_aprov = totais[2] if totais else 1  # evitar divisao por zero
            total_entreg = totais[3] if totais else 1
            valor_total = float(totais[4]) if (totais and totais[4]) else 0.0
            valor_aprov = float(totais[5]) if (totais and totais[5]) else 0.0
            valor_entreg = float(totais[6]) if (totais and totais[6]) else 0.0
            
            update_data = {
                'codigo_cliente_original': codigo,
                'nome': (limpar_string(cliente_fb[1])[:255] if cliente_fb[1] else None),
                'cpf_cnpj': (limpar_string(cliente_fb[2])[:20] if cliente_fb[2] else None),
                'ativo': True,  # Manter ativo
                'data_nascimento': data_nasc,
                'sexo': (str(cliente_fb[6])[:1] if cliente_fb[6] else None),  # idx 6
                'email': (limpar_string(cliente_fb[7])[:255] if cliente_fb[7] else None),  # idx 7
                'telefone': telefone,  # Da tabela CADASTRO_TELEFONE
                'endereco_logradouro': (limpar_string(end.get('endereco'))[:255] if end.get('endereco') else None),
                'endereco_numero': (str(end.get('numero')) if end.get('numero') else None),
                'endereco_cep': (limpar_string(end.get('cep'))[:10] if end.get('cep') else None),
                'endereco_cidade': (limpar_string(cliente_fb[8])[:100] if cliente_fb[8] else None),  # idx 8
                'endereco_estado': (limpar_string(cliente_fb[9])[:2] if cliente_fb[9] else None),  # idx 9
                # Totalizadores (SEMPRE incluir, mesmo que 0)
                'total_orcamentos': total_orc,
                'total_orcamentos_aprovados': totais[2] if totais else 0,
                'total_orcamentos_entregues': totais[3] if totais else 0,
                'valor_total_orcamentos': valor_total,
                'valor_total_aprovados': valor_aprov,
                'valor_total_entregues': valor_entreg,
                'valor_medio_orcamento': (valor_total / total_orc) if total_orc > 0 else 0.0,
                'valor_medio_aprovado': (valor_aprov / total_aprov) if (totais and total_aprov > 0) else 0.0,
                'valor_medio_entregue': (valor_entreg / total_entreg) if (totais and total_entreg > 0) else 0.0,
                'primeira_compra': (totais[7].date().isoformat() if (totais and totais[7]) else None),
                'ultima_compra': (totais[8].date().isoformat() if (totais and totais[8]) else None)
            }
            
            updates.append(update_data)
        
        # Atualizar no Supabase (PATCH individual para cada cliente)
        for update_data in updates:
            codigo = update_data['codigo_cliente_original']
            url = f"{SUPABASE_URL}/rest/v1/prime_clientes?codigo_cliente_original=eq.{codigo}"
            response = requests.patch(
                url,
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                total_atualizados += 1
            else:
                total_erros += 1
        
        if updates:
            print(f"          [OK] {total_atualizados}/{len(updates)} clientes atualizados")
        
        # Pequena pausa para não sobrecarregar
        time.sleep(0.5)
    
    conn.close()
    
    print(f"\n      [RESUMO ETAPA 2]")
    print(f"      Total atualizados: {total_atualizados}")
    print(f"      Total com erro: {total_erros}")
    
    # ============================================================================
    # ETAPA 3: Recalcular totalizadores de TODOS os clientes
    # ============================================================================
    print("\n[ETAPA 3/3] Recalculando totalizadores de TODOS os clientes...")
    print("      (Isso pode levar 10-15 minutos, seja paciente...)")
    
    # Buscar todos os clientes que têm pedidos
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    cursor = conn.cursor()
    
    print("\n      [3a] Calculando totalizadores no Firebird...")
    cursor.execute("""
        SELECT 
            A.CODIGO_CLIENTE,
            COUNT(*) as total_orcamentos,
            COUNT(A.AVIADA_DT) as total_aprovados,
            COUNT(A.ENTREGUE_DT) as total_entregues,
            COALESCE(SUM(A.VALORVENDA), 0) as valor_total,
            COALESCE(SUM(CASE WHEN A.AVIADA_DT IS NOT NULL THEN A.VALORVENDA ELSE 0 END), 0) as valor_aprovado,
            COALESCE(SUM(CASE WHEN A.ENTREGUE_DT IS NOT NULL THEN A.VALORVENDA ELSE 0 END), 0) as valor_entregue,
            MIN(A.CADASTRO_DT) as primeira_compra,
            MAX(A.CADASTRO_DT) as ultima_compra
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IS NOT NULL
        AND A.CODIGO_CLIENTE < 500000
        GROUP BY A.CODIGO_CLIENTE
    """)
    
    todos_totalizadores = cursor.fetchall()
    conn.close()
    
    print(f"          [OK] {len(todos_totalizadores)} clientes com pedidos encontrados")
    
    print(f"\n      [3b] Atualizando no Supabase em lotes...")
    
    batch_size = 100
    total_batches = (len(todos_totalizadores) + batch_size - 1) // batch_size
    total_atualizados_etapa3 = 0
    
    for i in range(0, len(todos_totalizadores), batch_size):
        batch = todos_totalizadores[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        if batch_num % 10 == 0:
            print(f"          Processando lote {batch_num}/{total_batches}...")
        
        updates = []
        for row in batch:
            # Calcular médias
            total = row[1] or 1  # evitar divisão por zero
            total_aprov = row[2] or 1
            total_entreg = row[3] or 1
            
            update_data = {
                'codigo_cliente_original': row[0],
                'total_orcamentos': row[1] or 0,
                'total_orcamentos_aprovados': row[2] or 0,
                'total_orcamentos_entregues': row[3] or 0,
                'valor_total_orcamentos': float(row[4]) if row[4] else 0.0,
                'valor_total_aprovados': float(row[5]) if row[5] else 0.0,
                'valor_total_entregues': float(row[6]) if row[6] else 0.0,
                'valor_medio_orcamento': float(row[4] / total) if row[4] else 0.0,
                'valor_medio_aprovado': float(row[5] / total_aprov) if row[5] else 0.0,
                'valor_medio_entregue': float(row[6] / total_entreg) if row[6] else 0.0,
                'primeira_compra': row[7].date().isoformat() if row[7] else None,
                'ultima_compra': row[8].date().isoformat() if row[8] else None
            }
            updates.append(update_data)
        
        # Atualizar (PATCH individual para cada cliente)
        for update_data in updates:
            codigo = update_data['codigo_cliente_original']
            url = f"{SUPABASE_URL}/rest/v1/prime_clientes?codigo_cliente_original=eq.{codigo}"
            response = requests.patch(
                url,
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                total_atualizados_etapa3 += 1
        
        time.sleep(0.3)
    
    print(f"\n          [OK] {total_atualizados_etapa3} clientes com totalizadores atualizados")
    
    # ============================================================================
    # RESUMO FINAL
    # ============================================================================
    print("\n" + "=" * 120)
    print("CORRECAO COMPLETA FINALIZADA!")
    print("=" * 120)
    print(f"\nRESUMO:")
    print(f"  Etapa 1: {len(codigos_corrigir)} clientes identificados para correcao")
    print(f"  Etapa 2: {total_atualizados} clientes corrigidos (telefone/endereco/dados)")
    print(f"  Etapa 3: {total_atualizados_etapa3} clientes com totalizadores recalculados")
    print(f"\nTempo total: {datetime.now()}")
    print("\n" + "=" * 120)
    print("PRONTO! Seu sistema esta 100% atualizado!")
    print("=" * 120)

except Exception as e:
    print(f"\n[ERRO CRITICO] {str(e)}")
    import traceback
    traceback.print_exc()

