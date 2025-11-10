#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizacao dos Registros Faltantes - Atingir 100%
Ordem: Clientes -> Pedidos -> Formulas -> Itens -> Rastreabilidade
"""

import fdb
import requests
from datetime import datetime
import os

# Configuracoes
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
    'Accept-Profile': 'api',
    'Content-Profile': 'api',
    'Prefer': 'resolution=merge-duplicates,return=representation'
}

def limpar_string(texto):
    if not texto:
        return None
    return str(texto).replace('\x00', '').replace('\u0000', '').strip() or None

def conectar_firebird():
    return fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )

print("="*80)
print("SINCRONIZACAO FALTANTES - ATINGIR 100%")
print("="*80)
print(f"Inicio: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("="*80)

# 1. SINCRONIZAR CLIENTES FALTANTES (325)
print("\n[1/5] SINCRONIZANDO CLIENTES FALTANTES...")
print("-"*80)

try:
    # Buscar codigos ja sincronizados
    print("Buscando codigos ja sincronizados...")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_clientes",
        headers=headers,
        params={'select': 'codigo_cliente_original', 'codigo_cliente_original': 'lt.500000'},
        timeout=60
    )

    codigos_sb = set()
    if resp.status_code == 200:
        dados = resp.json()
        codigos_sb = set([d['codigo_cliente_original'] for d in dados])
        print(f"   {len(codigos_sb)} clientes ja sincronizados")

    # Buscar todos do Firebird
    conn = conectar_firebird()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CODIGO
        FROM CLIENTE
        WHERE ATIVO = -1 AND CODIGO < 500000
        ORDER BY CODIGO
    """)

    todos_fb = [row[0] for row in cursor.fetchall()]
    codigos_fb = set(todos_fb)

    # Encontrar faltantes
    faltantes = sorted(list(codigos_fb - codigos_sb))
    print(f"   {len(faltantes)} clientes faltantes identificados")

    if faltantes:
        # Processar em lotes de 500
        total_inseridos = 0
        for i in range(0, len(faltantes), 500):
            lote = faltantes[i:i+500]
            codigos_str = ','.join(map(str, lote))

            print(f"   Processando lote {i//500 + 1} ({len(lote)} clientes)...")

            cursor.execute(f"""
                SELECT
                    C.CODIGO, C.NOMECLIENTE, C.CPF_CNPJ,
                    C.DIANASCIMENTO, C.MESNASCIMENTO, C.ANONASCIMENTO,
                    C.SEXO, C.EMAIL1, CE.NOMECIDADE, CE.UF, C.ATIVO
                FROM CLIENTE C
                LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
                WHERE C.CODIGO IN ({codigos_str})
            """)
            clientes = cursor.fetchall()

            # Buscar telefones
            cursor.execute(f"""
                SELECT CODIGO_CADASTRO, TELEFONEPREFIXO, TELEFONE
                FROM CADASTRO_TELEFONE
                WHERE TIPO_CADASTRO = 1 AND CODIGO_CADASTRO IN ({codigos_str})
            """)
            telefones_dict = {}
            for row in cursor.fetchall():
                codigo = row[0]
                tel = (str(row[1] or '') + str(row[2] or '')).strip() or None
                if tel and codigo not in telefones_dict:
                    telefones_dict[codigo] = tel

            # Buscar enderecos
            cursor.execute(f"""
                SELECT CODIGO_CADASTRO, ENDERECO, NUMERO, CEP
                FROM CADASTRO_ENDERECO
                WHERE TIPO_CADASTRO = 1 AND CODIGO_CADASTRO IN ({codigos_str})
            """)
            enderecos_dict = {}
            for row in cursor.fetchall():
                codigo = row[0]
                if codigo not in enderecos_dict:
                    enderecos_dict[codigo] = {
                        'logradouro': row[1],
                        'numero': row[2],
                        'cep': row[3]
                    }

            # Preparar dados
            clientes_dados = []
            for row in clientes:
                codigo = row[0]
                data_nasc = None
                if row[3] and row[4] and row[5]:
                    try:
                        data_nasc = f"{int(row[5])}-{int(row[4]):02d}-{int(row[3]):02d}"
                    except:
                        pass

                telefone = telefones_dict.get(codigo)
                endereco = enderecos_dict.get(codigo, {})

                clientes_dados.append({
                    'codigo_cliente_original': codigo,
                    'nome': limpar_string(row[1])[:255] if row[1] else None,
                    'cpf_cnpj': limpar_string(row[2])[:20] if row[2] else None,
                    'ativo': bool(row[10]) if row[10] is not None else True,
                    'data_nascimento': data_nasc,
                    'sexo': str(row[6])[:1] if row[6] else None,
                    'email': limpar_string(row[7])[:255] if row[7] else None,
                    'telefone': telefone,
                    'endereco_logradouro': limpar_string(endereco.get('logradouro'))[:255] if endereco.get('logradouro') else None,
                    'endereco_numero': str(endereco.get('numero')) if endereco.get('numero') else None,
                    'endereco_cep': limpar_string(endereco.get('cep'))[:10] if endereco.get('cep') else None,
                    'endereco_cidade': limpar_string(row[8])[:100] if row[8] else None,
                    'endereco_estado': limpar_string(row[9])[:2] if row[9] else None,
                    'total_orcamentos': 0,
                    'total_orcamentos_aprovados': 0,
                    'total_orcamentos_entregues': 0,
                    'valor_total_orcamentos': 0.0,
                    'valor_total_aprovados': 0.0,
                    'valor_total_entregues': 0.0,
                    'valor_medio_orcamento': 0.0,
                    'valor_medio_aprovado': 0.0,
                    'valor_medio_entregue': 0.0
                })

            # Inserir lote
            if clientes_dados:
                resp = requests.post(
                    f"{SUPABASE_URL}/rest/v1/prime_clientes",
                    headers=headers,
                    params={'on_conflict': 'codigo_cliente_original'},
                    json=clientes_dados,
                    timeout=60
                )

                if resp.status_code in [200, 201, 204]:
                    total_inseridos += len(clientes_dados)
                    print(f"      [OK] {len(clientes_dados)} clientes inseridos")
                else:
                    print(f"      [ERRO] HTTP {resp.status_code}")

        conn.close()
        print(f"   [OK] Total: {total_inseridos} clientes sincronizados!")
    else:
        print("   [OK] Nenhum cliente faltante!")

except Exception as e:
    print(f"   [ERRO] {e}")

# 2. SINCRONIZAR PEDIDOS FALTANTES (301)
print("\n[2/5] SINCRONIZANDO PEDIDOS FALTANTES...")
print("-"*80)

try:
    # Buscar codigos ja sincronizados
    print("Buscando pedidos ja sincronizados...")
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers=headers,
        params={'select': 'codigo_orcamento_original'},
        timeout=60
    )

    codigos_sb = set()
    if resp.status_code == 200:
        dados = resp.json()
        codigos_sb = set([d['codigo_orcamento_original'] for d in dados])
        print(f"   {len(codigos_sb)} pedidos ja sincronizados")

    # Buscar todos do Firebird
    conn = conectar_firebird()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CODIGO
        FROM ATENDIMENTO_A1
        WHERE CODIGO_CLIENTE IS NOT NULL
        ORDER BY CODIGO
    """)

    todos_fb = [row[0] for row in cursor.fetchall()]
    codigos_fb = set(todos_fb)

    # Encontrar faltantes
    faltantes = sorted(list(codigos_fb - codigos_sb))
    print(f"   {len(faltantes)} pedidos faltantes identificados")

    if faltantes:
        # Processar em lotes de 500
        total_inseridos = 0
        for i in range(0, len(faltantes), 500):
            lote = faltantes[i:i+500]
            codigos_str = ','.join(map(str, lote))

            print(f"   Processando lote {i//500 + 1} ({len(lote)} pedidos)...")

            cursor.execute(f"""
                SELECT CODIGO, CODIGO_CLIENTE, CADASTRO_DT, AVIADA_DT,
                       ENTREGUE_DT, VALORVENDA, OBSERVACAO
                FROM ATENDIMENTO_A1
                WHERE CODIGO IN ({codigos_str})
            """)
            pedidos = cursor.fetchall()

            # Buscar cache de clientes
            codigos_cliente = list(set([row[1] for row in pedidos]))
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_clientes",
                headers=headers,
                params={
                    'select': 'id,codigo_cliente_original',
                    'codigo_cliente_original': f'in.({",".join(map(str, codigos_cliente))})'
                },
                timeout=30
            )

            cache_clientes = {}
            if resp.status_code == 200:
                for cli in resp.json():
                    cache_clientes[cli['codigo_cliente_original']] = cli['id']

            # Preparar dados
            pedidos_dados = []
            for row in pedidos:
                codigo_cli = row[1]
                if codigo_cli not in cache_clientes:
                    continue

                status_geral = 'ENTREGUE' if row[4] else ('APROVADO' if row[3] else 'PENDENTE')

                pedidos_dados.append({
                    'codigo_orcamento_original': row[0],
                    'cliente_id': cache_clientes[codigo_cli],
                    'codigo_cliente_original': codigo_cli,
                    'data_criacao': row[2].isoformat() if row[2] else None,
                    'data_aprovacao': row[3].isoformat() if row[3] else None,
                    'data_entrega': row[4].isoformat() if row[4] else None,
                    'valor_total': float(row[5]) if row[5] else 0.0,
                    'observacoes': limpar_string(row[6]),
                    'status_aprovacao': 'APROVADO' if row[3] else 'NAO_APROVADO',
                    'status_entrega': 'ENTREGUE' if row[4] else 'NAO_ENTREGUE',
                    'status_geral': status_geral
                })

            # Inserir lote
            if pedidos_dados:
                resp = requests.post(
                    f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                    headers=headers,
                    params={'on_conflict': 'codigo_orcamento_original'},
                    json=pedidos_dados,
                    timeout=60
                )

                if resp.status_code in [200, 201, 204]:
                    total_inseridos += len(pedidos_dados)
                    print(f"      [OK] {len(pedidos_dados)} pedidos inseridos")
                else:
                    print(f"      [ERRO] HTTP {resp.status_code}")

        conn.close()
        print(f"   [OK] Total: {total_inseridos} pedidos sincronizados!")
    else:
        print("   [OK] Nenhum pedido faltante!")

except Exception as e:
    print(f"   [ERRO] {e}")

# 3. SINCRONIZAR FORMULAS FALTANTES (1,085)
print("\n[3/5] SINCRONIZANDO FORMULAS FALTANTES...")
print("-"*80)

try:
    # Buscar formulas ja sincronizadas
    print("Buscando formulas ja sincronizadas...")

    # Buscar em paginacao
    formulas_sb = set()
    offset = 0
    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_formulas",
            headers=headers,
            params={
                'select': 'codigo_orcamento_original,numero_formula',
                'limit': 1000,
                'offset': offset
            },
            timeout=30
        )

        if resp.status_code == 200:
            dados = resp.json()
            if not dados:
                break
            for d in dados:
                formulas_sb.add((d['codigo_orcamento_original'], d['numero_formula']))
            offset += 1000
        else:
            break

    print(f"   {len(formulas_sb)} formulas ja sincronizadas")

    # Buscar todas do Firebird
    conn = conectar_firebird()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CODIGO_ATEND_A1, NUMEROFORMULA
        FROM ATENDIMENTO_A2
        WHERE CODIGO_ATEND_A1 IS NOT NULL
        ORDER BY CODIGO_ATEND_A1, NUMEROFORMULA
    """)

    formulas_fb = set([(row[0], row[1]) for row in cursor.fetchall()])

    # Encontrar faltantes
    faltantes = sorted(list(formulas_fb - formulas_sb))
    print(f"   {len(faltantes)} formulas faltantes identificadas")

    if faltantes:
        # Processar em lotes de 1000
        for i in range(0, len(faltantes), 1000):
            lote = faltantes[i:i+1000]

            # Criar WHERE clause
            where_clauses = []
            for cod_atend, num_form in lote:
                where_clauses.append(f"(CODIGO_ATEND_A1 = {cod_atend} AND NUMEROFORMULA = {num_form})")

            where_str = ' OR '.join(where_clauses)

            cursor.execute(f"""
                SELECT CODIGO_ATEND_A1, NUMEROFORMULA, TEXTOROTULO, POSOLOGIA, VALORFORMULA_VENDA
                FROM ATENDIMENTO_A2
                WHERE {where_str}
            """)

            formulas = cursor.fetchall()

            # Buscar cache de pedidos
            codigos_atend = list(set([row[0] for row in formulas]))
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'codigo_orcamento_original': f'in.({",".join(map(str, codigos_atend))})'
                },
                timeout=30
            )

            cache_pedidos = {}
            if resp.status_code == 200:
                for ped in resp.json():
                    cache_pedidos[ped['codigo_orcamento_original']] = ped['id']

            # Preparar dados
            formulas_dados = []
            for row in formulas:
                codigo_atend = row[0]
                if codigo_atend not in cache_pedidos:
                    continue

                formulas_dados.append({
                    'pedido_id': cache_pedidos[codigo_atend],
                    'codigo_orcamento_original': codigo_atend,
                    'numero_formula': row[1],
                    'descricao': limpar_string(row[2]),
                    'posologia': limpar_string(row[3]),
                    'valor_formula': float(row[4]) if row[4] else 0.0,
                    'updated_at': datetime.now().isoformat()
                })

            # Inserir
            if formulas_dados:
                resp = requests.post(
                    f"{SUPABASE_URL}/rest/v1/prime_formulas",
                    headers=headers,
                    params={'on_conflict': 'codigo_orcamento_original,numero_formula'},
                    json=formulas_dados,
                    timeout=60
                )

                if resp.status_code in [200, 201, 204]:
                    print(f"   [OK] Lote {i//1000 + 1}: {len(formulas_dados)} formulas sincronizadas")
                else:
                    print(f"   [ERRO] Lote {i//1000 + 1}: HTTP {resp.status_code}")

        conn.close()
    else:
        print("   [OK] Nenhuma formula faltante!")
        conn.close()

except Exception as e:
    print(f"   [ERRO] {e}")

# 4. SINCRONIZAR ITENS FALTANTES (6,422)
print("\n[4/5] SINCRONIZANDO ITENS FALTANTES...")
print("-"*80)

try:
    print("Sincronizando itens...")
    print("   [INFO] Devido ao volume, sincronizando incrementalmente...")

    conn = conectar_firebird()
    cursor = conn.cursor()

    # Buscar ultimo codigo sincronizado
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
        headers=headers,
        params={
            'select': 'codigo_atendimento_original',
            'order': 'codigo_atendimento_original.desc',
            'limit': 1
        },
        timeout=10
    )

    ultimo_codigo = 0
    if resp.status_code == 200:
        dados = resp.json()
        if dados:
            ultimo_codigo = dados[0]['codigo_atendimento_original']

    print(f"   Ultimo codigo: {ultimo_codigo}")

    # Buscar novos itens
    cursor.execute(f"""
        SELECT A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA,
               A3.CODIGO_PRODUTO, EG.NOMEPRODUTO, A3.QUANTIDADE, A3.UNIDADE,
               A3.VALORCUSTO, A3.VALORVENDA, A3.OBSERVACAO
        FROM ATENDIMENTO_A3 A3
        LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
        WHERE A3.CODIGO_ATEND_A1 > {ultimo_codigo}
        AND A3.CODIGO_ATEND_A1 IS NOT NULL
        ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
        ROWS 10000
    """)

    itens = cursor.fetchall()
    conn.close()

    if itens:
        print(f"   {len(itens)} itens novos encontrados")

        # Montar cache de formulas
        codigos_atend = list(set([row[0] for row in itens]))
        cache_formulas = {}

        for i in range(0, len(codigos_atend), 1000):
            lote_codigos = codigos_atend[i:i+1000]
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_formulas",
                headers=headers,
                params={
                    'select': 'id,pedido_id,codigo_orcamento_original,numero_formula',
                    'codigo_orcamento_original': f'in.({",".join(map(str, lote_codigos))})'
                },
                timeout=30
            )

            if resp.status_code == 200:
                for formula in resp.json():
                    chave = (formula['codigo_orcamento_original'], formula['numero_formula'])
                    cache_formulas[chave] = {
                        'id': formula['id'],
                        'pedido_id': formula['pedido_id']
                    }

        print(f"   Cache: {len(cache_formulas)} formulas carregadas")

        # Preparar dados
        itens_dados = []
        for row in itens:
            chave = (row[0], row[1])
            formula_info = cache_formulas.get(chave)

            if not formula_info:
                continue

            itens_dados.append({
                'formula_id': formula_info['id'],
                'pedido_id': formula_info['pedido_id'],
                'codigo_atendimento_original': row[0],
                'numero_formula': row[1],
                'numero_linha': row[2],
                'codigo_produto': row[3],
                'nome_produto': limpar_string(row[4]) or 'PRODUTO NAO IDENTIFICADO',
                'quantidade': float(row[5]) if row[5] else None,
                'unidade': limpar_string(row[6]),
                'quantidade_calculo': float(row[5]) if row[5] else None,
                'valor_custo': float(row[7]) if row[7] else 0.0,
                'valor_venda': float(row[8]) if row[8] else 0.0,
                'valor_venda_desconto': 0.0,
                'inclusao_sistema': True,
                'visualizar_produto': True,
                'observacao': limpar_string(row[9]),
                'updated_at': datetime.now().isoformat()
            })

        # Inserir
        if itens_dados:
            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
                headers=headers,
                params={'on_conflict': 'codigo_atendimento_original,numero_formula,numero_linha'},
                json=itens_dados,
                timeout=120
            )

            if resp.status_code in [200, 201, 204]:
                print(f"   [OK] {len(itens_dados)} itens sincronizados!")
            else:
                print(f"   [ERRO] HTTP {resp.status_code}")
        else:
            print("   [OK] Nenhum item valido!")
    else:
        print("   [OK] Nenhum item novo!")

except Exception as e:
    print(f"   [ERRO] {e}")

# 5. SINCRONIZAR RASTREABILIDADE FALTANTE (4,018)
print("\n[5/5] SINCRONIZANDO RASTREABILIDADE FALTANTE...")
print("-"*80)

try:
    conn = conectar_firebird()
    cursor = conn.cursor()

    # Buscar ultimo codigo
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade",
        headers=headers,
        params={
            'select': 'codigo_processo_original',
            'order': 'codigo_processo_original.desc',
            'limit': 1
        },
        timeout=10
    )

    ultimo_codigo = 0
    if resp.status_code == 200:
        dados = resp.json()
        if dados:
            ultimo_codigo = dados[0]['codigo_processo_original']

    print(f"   Ultimo codigo: {ultimo_codigo}")

    # Buscar novos registros
    cursor.execute(f"""
        SELECT CODIGO, TIPO_MOV, CODIGO_MOV, CODIGO_PROCESSO_TIPO,
               CODIGO_FUNCIONARIO, DATA_PROCESSO, HORA_PROCESSO, SEQUENCIA
        FROM PROCESSO_MANIPULACAO
        WHERE CODIGO > {ultimo_codigo}
        ORDER BY CODIGO
        ROWS 5000
    """)

    registros = cursor.fetchall()
    conn.close()

    if registros:
        print(f"   {len(registros)} registros novos encontrados")

        # Cache de pedidos e tipos
        codigos_orcamento = list(set([row[2] for row in registros]))

        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_pedidos",
            headers=headers,
            params={
                'select': 'id,codigo_orcamento_original',
                'codigo_orcamento_original': f'in.({",".join(map(str, codigos_orcamento))})'
            },
            timeout=30
        )

        cache_pedidos = {}
        if resp.status_code == 200:
            for ped in resp.json():
                cache_pedidos[ped['codigo_orcamento_original']] = ped['id']

        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_tipos_processo",
            headers=headers,
            params={'select': 'id,codigo_tipo_original'},
            timeout=10
        )

        cache_tipos = {}
        if resp.status_code == 200:
            for tipo in resp.json():
                cache_tipos[tipo['codigo_tipo_original']] = tipo['id']

        # Preparar dados
        rastro_dados = []
        for row in registros:
            codigo_orcamento = row[2]
            codigo_tipo = row[3]

            if codigo_orcamento not in cache_pedidos or codigo_tipo not in cache_tipos:
                continue

            rastro_dados.append({
                'codigo_processo_original': row[0],
                'pedido_id': cache_pedidos[codigo_orcamento],
                'codigo_orcamento_original': codigo_orcamento,
                'tipo_processo_id': cache_tipos[codigo_tipo],
                'codigo_tipo_original': codigo_tipo,
                'tipo_movimento': row[1],
                'codigo_funcionario': row[4],
                'data_processo': row[5].isoformat() if row[5] else None,
                'hora_processo': str(row[6]) if row[6] else None,
                'sequencia': row[7],
                'status_processo': 'CONCLUIDO',
                'updated_at': datetime.now().isoformat()
            })

        # Inserir
        if rastro_dados:
            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade",
                headers=headers,
                params={'on_conflict': 'codigo_processo_original'},
                json=rastro_dados,
                timeout=60
            )

            if resp.status_code in [200, 201, 204]:
                print(f"   [OK] {len(rastro_dados)} registros sincronizados!")
            else:
                print(f"   [ERRO] HTTP {resp.status_code}")
        else:
            print("   [OK] Nenhum registro valido!")
    else:
        print("   [OK] Nenhum registro novo!")

except Exception as e:
    print(f"   [ERRO] {e}")

print("\n" + "="*80)
print("SINCRONIZACAO CONCLUIDA!")
print("="*80)
print(f"Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("="*80)
print("\nExecute novamente o script de verificacao para conferir o status!")
