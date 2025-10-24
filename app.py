#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask para Sincronização Incremental Firebird -> Supabase
Endpoint: /sync (POST ou GET)
Versão: 2.0.0 - Atualizado com prime_formulas_itens e TEXTOROTULO
"""

from flask import Flask, jsonify, request
import fdb
import requests
import os
from datetime import datetime
import logging

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_secret(env_var):
    """Lê secret de arquivo ou variável de ambiente"""
    file_path_var = f"{env_var}_FILE"
    if file_path_var in os.environ:
        with open(os.environ[file_path_var], 'r') as f:
            return f.read().strip()
    return os.getenv(env_var, '')

# Configurações
FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or read_secret('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or read_secret('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or read_secret('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or read_secret('FIREBIRD_PASS')

SUPABASE_URL = os.getenv('SUPABASE_URL') or read_secret('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or read_secret('SUPABASE_KEY')
API_TOKEN = os.getenv('API_TOKEN') or read_secret('API_TOKEN')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api',
    'Prefer': 'resolution=merge-duplicates'
}

def limpar_string(texto):
    """Limpa strings removendo caracteres inválidos"""
    if not texto:
        return None
    return str(texto).replace('\x00', '').replace('\u0000', '').strip() or None

def get_ultimo_id_supabase(tabela, campo_id='codigo_cliente_original'):
    """Pega o maior ID já migrado"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tabela}"
        response = requests.get(
            url,
            headers=headers,
            params={
                'select': campo_id,
                'order': f'{campo_id}.desc',
                'limit': 1
            },
            timeout=10
        )

        if response.status_code == 200:
            dados = response.json()
            if dados:
                return dados[0][campo_id]
        return 0
    except Exception as e:
        logger.error(f"Erro ao buscar último ID de {tabela}: {e}")
        return 0

def conectar_firebird():
    """Conecta ao Firebird"""
    return fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )

def sync_clientes_novos():
    """Sincroniza apenas clientes novos"""
    try:
        ultimo_codigo = get_ultimo_id_supabase('prime_clientes', 'codigo_cliente_original')
        logger.info(f"📊 Clientes - Último código: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                C.CODIGO,
                C.NOMECLIENTE,
                C.CPF_CNPJ,
                C.EMAIL1,
                C.TELEFONE1,
                C.TELEFONE2,
                C.CELULAR,
                C.ENDERECO,
                C.NUMERO,
                C.COMPLEMENTO,
                C.BAIRRO,
                C.CIDADE,
                C.UF,
                C.CEP,
                C.DIANASCIMENTO,
                C.MESNASCIMENTO,
                C.ANONASCIMENTO,
                C.SEXO,
                C.DATACADASTRO
            FROM CLIENTE C
            WHERE C.ATIVO = -1
            AND C.CODIGO > {ultimo_codigo}
            ORDER BY C.CODIGO
            FETCH FIRST 1000 ROWS ONLY
        """)

        novos_clientes = cursor.fetchall()
        conn.close()

        if not novos_clientes:
            return {'inseridos': 0, 'mensagem': 'Nenhum cliente novo'}

        logger.info(f"✅ Encontrados {len(novos_clientes)} clientes novos")

        # Preparar dados
        clientes_dados = []
        for row in novos_clientes:
            data_nasc = None
            if row[14] and row[15] and row[16]:
                try:
                    data_nasc = f"{int(row[16])}-{int(row[15]):02d}-{int(row[14]):02d}"
                except:
                    pass

            cliente = {
                'codigo_cliente_original': row[0],
                'nome': limpar_string(row[1])[:255] if row[1] else None,
                'cpf_cnpj': limpar_string(row[2])[:20] if row[2] else None,
                'email': limpar_string(row[3])[:255] if row[3] else None,
                'telefone': limpar_string(row[4] or row[5] or row[6]),
                'endereco_logradouro': limpar_string(row[7])[:255] if row[7] else None,
                'endereco_numero': str(row[8]) if row[8] else None,
                'endereco_complemento': limpar_string(row[9])[:100] if row[9] else None,
                'endereco_bairro': limpar_string(row[10])[:100] if row[10] else None,
                'endereco_cidade': limpar_string(row[11])[:100] if row[11] else None,
                'endereco_estado': limpar_string(row[12])[:2] if row[12] else None,
                'endereco_cep': limpar_string(row[13])[:10] if row[13] else None,
                'data_nascimento': data_nasc,
                'sexo': str(row[17])[:1] if row[17] else None,
                'data_cadastro': row[18].isoformat() if row[18] else None,
                'ativo': True,
                'updated_at': datetime.now().isoformat()
            }
            clientes_dados.append(cliente)

        # Inserir no Supabase
        url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
        response = requests.post(url, headers=headers, json=clientes_dados, timeout=30)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(clientes_dados),
                'mensagem': f'{len(clientes_dados)} clientes sincronizados'
            }
        else:
            logger.error(f"❌ Erro ao inserir clientes: {response.status_code} - {response.text[:200]}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_clientes_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_pedidos_novos():
    """Sincroniza apenas pedidos novos"""
    try:
        ultimo_codigo = get_ultimo_id_supabase('prime_pedidos', 'codigo_orcamento_original')
        logger.info(f"📊 Pedidos - Último código: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                A.CODIGO,
                A.CODIGO_CLIENTE,
                A.AVIADA_DT,
                A.ENTREGUE_DT,
                A.VALORVENDA,
                A.OBSERVACAO
            FROM ATENDIMENTO_A1 A
            WHERE A.CODIGO_CLIENTE IS NOT NULL
            AND A.CODIGO > {ultimo_codigo}
            ORDER BY A.CODIGO
            FETCH FIRST 1000 ROWS ONLY
        """)

        novos_pedidos = cursor.fetchall()
        conn.close()

        if not novos_pedidos:
            return {'inseridos': 0, 'mensagem': 'Nenhum pedido novo'}

        logger.info(f"✅ Encontrados {len(novos_pedidos)} pedidos novos")

        # Buscar clientes em lote
        codigos_cliente = list(set([row[1] for row in novos_pedidos]))
        url_clientes = f"{SUPABASE_URL}/rest/v1/prime_clientes"
        response = requests.get(
            url_clientes,
            headers=headers,
            params={
                'select': 'id,codigo_cliente_original',
                'codigo_cliente_original': f'in.({",".join(map(str, codigos_cliente))})'
            },
            timeout=30
        )

        cache_clientes = {}
        if response.status_code == 200:
            for cli in response.json():
                cache_clientes[cli['codigo_cliente_original']] = cli['id']

        pedidos_dados = []
        for row in novos_pedidos:
            codigo_orcamento, codigo_cliente, aviada_dt, entregue_dt, valor_venda, observacao = row

            cliente_id = cache_clientes.get(codigo_cliente)
            if not cliente_id:
                continue

            status_aprovacao = 'APROVADO' if aviada_dt else 'NAO_APROVADO'
            status_entrega = 'ENTREGUE' if entregue_dt else 'NAO_ENTREGUE'

            if entregue_dt:
                status_geral = 'ENTREGUE'
            elif aviada_dt:
                status_geral = 'APROVADO'
            else:
                status_geral = 'PENDENTE'

            pedido = {
                'codigo_orcamento_original': codigo_orcamento,
                'codigo_cliente_original': codigo_cliente,
                'cliente_id': cliente_id,
                'data_aprovacao': aviada_dt.isoformat() if aviada_dt else None,
                'data_entrega': entregue_dt.isoformat() if entregue_dt else None,
                'valor_total': float(valor_venda) if valor_venda else 0.0,
                'observacoes': limpar_string(observacao),
                'status_aprovacao': status_aprovacao,
                'status_entrega': status_entrega,
                'status_geral': status_geral,
                'updated_at': datetime.now().isoformat()
            }
            pedidos_dados.append(pedido)

        if not pedidos_dados:
            return {'inseridos': 0, 'mensagem': 'Pedidos sem clientes correspondentes'}

        url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
        response = requests.post(url, headers=headers, json=pedidos_dados, timeout=30)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(pedidos_dados),
                'mensagem': f'{len(pedidos_dados)} pedidos sincronizados'
            }
        else:
            logger.error(f"❌ Erro ao inserir pedidos: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_pedidos_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_formulas_novas():
    """Sincroniza fórmulas novas com TEXTOROTULO"""
    try:
        # Buscar último código de fórmula baseado no pedido
        url_formulas = f"{SUPABASE_URL}/rest/v1/prime_formulas"
        response = requests.get(
            url_formulas,
            headers=headers,
            params={
                'select': 'codigo_orcamento_original',
                'order': 'codigo_orcamento_original.desc',
                'limit': 1
            },
            timeout=10
        )

        ultimo_codigo = 0
        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_codigo = dados[0]['codigo_orcamento_original']

        logger.info(f"📊 Fórmulas - Último código atendimento: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                A2.CODIGO_ATEND_A1,
                A2.NUMEROFORMULA,
                A2.TEXTOROTULO,
                A2.POSOLOGIA,
                A2.VALORFORMULA_VENDA
            FROM ATENDIMENTO_A2 A2
            WHERE A2.CODIGO_ATEND_A1 > {ultimo_codigo}
            AND A2.CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY A2.CODIGO_ATEND_A1, A2.NUMEROFORMULA
            FETCH FIRST 2000 ROWS ONLY
        """)

        novas_formulas = cursor.fetchall()
        conn.close()

        if not novas_formulas:
            return {'inseridos': 0, 'mensagem': 'Nenhuma fórmula nova'}

        logger.info(f"✅ Encontradas {len(novas_formulas)} fórmulas novas")

        # Buscar pedidos em lote
        codigos_orcamento = list(set([row[0] for row in novas_formulas]))
        url_pedidos = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
        response = requests.get(
            url_pedidos,
            headers=headers,
            params={
                'select': 'id,codigo_orcamento_original',
                'codigo_orcamento_original': f'in.({",".join(map(str, codigos_orcamento))})'
            },
            timeout=30
        )

        cache_pedidos = {}
        if response.status_code == 200:
            for ped in response.json():
                cache_pedidos[ped['codigo_orcamento_original']] = ped['id']

        formulas_dados = []
        for row in novas_formulas:
            codigo_atend, num_formula, texto_rotulo, posologia, valor = row

            pedido_id = cache_pedidos.get(codigo_atend)
            if not pedido_id:
                continue

            formula = {
                'pedido_id': pedido_id,
                'codigo_orcamento_original': codigo_atend,
                'numero_formula': num_formula,
                'descricao': limpar_string(texto_rotulo),  # TEXTOROTULO completo!
                'posologia': limpar_string(posologia),
                'valor_formula': float(valor) if valor else 0.0,
                'updated_at': datetime.now().isoformat()
            }
            formulas_dados.append(formula)

        if not formulas_dados:
            return {'inseridos': 0, 'mensagem': 'Fórmulas sem pedidos correspondentes'}

        url = f"{SUPABASE_URL}/rest/v1/prime_formulas"
        response = requests.post(url, headers=headers, json=formulas_dados, timeout=60)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(formulas_dados),
                'mensagem': f'{len(formulas_dados)} fórmulas sincronizadas'
            }
        else:
            logger.error(f"❌ Erro ao inserir fórmulas: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_formulas_novas: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_formulas_itens_novos():
    """Sincroniza itens das fórmulas (ATENDIMENTO_A3) - NOVA FUNCIONALIDADE"""
    try:
        # Buscar último código de item
        url_itens = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
        response = requests.get(
            url_itens,
            headers=headers,
            params={
                'select': 'codigo_atendimento_original',
                'order': 'codigo_atendimento_original.desc',
                'limit': 1
            },
            timeout=10
        )

        ultimo_codigo = 0
        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_codigo = dados[0]['codigo_atendimento_original']

        logger.info(f"📊 Fórmulas Itens - Último código atendimento: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                A3.CODIGO_ATEND_A1,
                A3.NUMEROFORMULA,
                A3.NUMEROLINHA,
                A3.CODIGO_PRODUTO,
                A3.NOME_PRODUTO,
                A3.QUANTIDADE,
                A3.UNIDADE,
                A3.QUANTIDADE_CALCULO,
                A3.VALORCUSTO,
                A3.VALORVENDA,
                A3.VALORVENDA_DESC,
                A3.INCLUSAOSISTEMA,
                A3.VISUALIZARPRODUTO,
                A3.OBSERVACAO
            FROM ATENDIMENTO_A3 A3
            WHERE A3.CODIGO_ATEND_A1 > {ultimo_codigo}
            AND A3.CODIGO_ATEND_A1 IS NOT NULL
            AND A3.NOME_PRODUTO IS NOT NULL
            ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
            FETCH FIRST 5000 ROWS ONLY
        """)

        novos_itens = cursor.fetchall()
        conn.close()

        if not novos_itens:
            return {'inseridos': 0, 'mensagem': 'Nenhum item novo'}

        logger.info(f"✅ Encontrados {len(novos_itens)} itens novos")

        # Buscar fórmulas em lote (cache)
        chaves_formula = list(set([(row[0], row[1]) for row in novos_itens]))

        # Montar cache de fórmulas
        cache_formulas = {}
        for codigo_atend, num_formula in chaves_formula[:100]:  # Limitar para não sobrecarregar
            url_formula = f"{SUPABASE_URL}/rest/v1/prime_formulas"
            response = requests.get(
                url_formula,
                headers=headers,
                params={
                    'select': 'id,pedido_id',
                    'codigo_orcamento_original': f'eq.{codigo_atend}',
                    'numero_formula': f'eq.{num_formula}',
                    'limit': 1
                },
                timeout=5
            )

            if response.status_code == 200:
                dados = response.json()
                if dados:
                    cache_formulas[(codigo_atend, num_formula)] = dados[0]

        itens_dados = []
        for row in novos_itens:
            (codigo_atend, num_formula, num_linha, codigo_produto, nome_produto,
             quantidade, unidade, qtd_calculo, valor_custo, valor_venda,
             valor_venda_desc, inclusao_sistema, visualizar_produto, observacao) = row

            chave = (codigo_atend, num_formula)
            formula_info = cache_formulas.get(chave)

            if not formula_info:
                continue

            item = {
                'formula_id': formula_info['id'],
                'pedido_id': formula_info['pedido_id'],
                'codigo_atendimento_original': codigo_atend,
                'numero_formula': num_formula,
                'numero_linha': num_linha,
                'codigo_produto': codigo_produto,
                'nome_produto': limpar_string(nome_produto),
                'quantidade': float(quantidade) if quantidade else None,
                'unidade': limpar_string(unidade),
                'quantidade_calculo': float(qtd_calculo) if qtd_calculo else None,
                'valor_custo': float(valor_custo) if valor_custo else 0.0,
                'valor_venda': float(valor_venda) if valor_venda else 0.0,
                'valor_venda_desconto': float(valor_venda_desc) if valor_venda_desc else 0.0,
                'inclusao_sistema': bool(inclusao_sistema) if inclusao_sistema is not None else False,
                'visualizar_produto': bool(visualizar_produto) if visualizar_produto is not None else True,
                'observacao': limpar_string(observacao)
            }
            itens_dados.append(item)

        if not itens_dados:
            return {'inseridos': 0, 'mensagem': 'Itens sem fórmulas correspondentes'}

        url = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
        response = requests.post(url, headers=headers, json=itens_dados, timeout=60)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(itens_dados),
                'mensagem': f'{len(itens_dados)} itens sincronizados'
            }
        else:
            logger.error(f"❌ Erro ao inserir itens: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_formulas_itens_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_rastreabilidade_nova():
    """Sincroniza rastreabilidade nova (ATENDIMENTO_A2.CONTROLERASTREABILIDADE)"""
    try:
        logger.info("📋 Sincronizando rastreabilidade...")

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        # Buscar último registro
        url_ultimo = f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade"
        response = requests.get(
            url_ultimo,
            headers=headers,
            params={
                'select': 'codigo_atendimento_original',
                'order': 'codigo_atendimento_original.desc',
                'limit': 1
            },
            timeout=10
        )

        ultimo_codigo = 0
        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_codigo = dados[0]['codigo_atendimento_original']

        logger.info(f"📊 Rastreabilidade - Último código: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                A2.CODIGO_ATEND_A1,
                A2.NUMEROFORMULA,
                A2.CONTROLERASTREABILIDADE
            FROM ATENDIMENTO_A2 A2
            WHERE A2.CODIGO_ATEND_A1 > {ultimo_codigo}
            AND A2.CODIGO_ATEND_A1 IS NOT NULL
            AND A2.CONTROLERASTREABILIDADE IS NOT NULL
            ORDER BY A2.CODIGO_ATEND_A1
            FETCH FIRST 5000 ROWS ONLY
        """)

        novos_registros = cursor.fetchall()
        conn.close()

        if not novos_registros:
            return {'inseridos': 0, 'mensagem': 'Nenhum registro novo'}

        logger.info(f"✅ Encontrados {len(novos_registros)} registros novos")

        # Buscar fórmulas correspondentes
        chaves_formula = list(set([(row[0], row[1]) for row in novos_registros]))
        cache_formulas = {}

        for codigo_atend, num_formula in chaves_formula[:100]:
            url_formula = f"{SUPABASE_URL}/rest/v1/prime_formulas"
            response = requests.get(
                url_formula,
                headers=headers,
                params={
                    'select': 'id,pedido_id',
                    'codigo_orcamento_original': f'eq.{codigo_atend}',
                    'numero_formula': f'eq.{num_formula}',
                    'limit': 1
                },
                timeout=5
            )

            if response.status_code == 200:
                dados = response.json()
                if dados:
                    cache_formulas[(codigo_atend, num_formula)] = dados[0]

        rastreabilidade_dados = []
        for row in novos_registros:
            codigo_atend, num_formula, controle_rastreabilidade = row

            chave = (codigo_atend, num_formula)
            formula_info = cache_formulas.get(chave)

            if not formula_info:
                continue

            registro = {
                'formula_id': formula_info['id'],
                'pedido_id': formula_info['pedido_id'],
                'codigo_atendimento_original': codigo_atend,
                'numero_formula': num_formula,
                'controle_rastreabilidade': limpar_string(controle_rastreabilidade)
            }
            rastreabilidade_dados.append(registro)

        if not rastreabilidade_dados:
            return {'inseridos': 0, 'mensagem': 'Registros sem fórmulas correspondentes'}

        url = f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade"
        response = requests.post(url, headers=headers, json=rastreabilidade_dados, timeout=60)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(rastreabilidade_dados),
                'mensagem': f'{len(rastreabilidade_dados)} registros sincronizados'
            }
        else:
            logger.error(f"❌ Erro ao inserir rastreabilidade: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_rastreabilidade_nova: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_tipos_processo_novos():
    """Sincroniza tipos de processo (ATENDIMENTO_A1.TIPODEPROCESSO)"""
    try:
        logger.info("📋 Sincronizando tipos de processo...")

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        }

        # Buscar último código de atendimento processado
        url_ultimo = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
        response = requests.get(
            url_ultimo,
            headers=headers,
            params={
                'select': 'codigo_atendimento_original',
                'order': 'codigo_atendimento_original.desc',
                'limit': 1
            },
            timeout=10
        )

        ultimo_codigo = 0
        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_codigo = dados[0]['codigo_atendimento_original']

        logger.info(f"📊 Tipos Processo - Último código: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                A1.CODIGO,
                A1.TIPODEPROCESSO
            FROM ATENDIMENTO_A1 A1
            WHERE A1.CODIGO > {ultimo_codigo}
            AND A1.CODIGO IS NOT NULL
            AND A1.TIPODEPROCESSO IS NOT NULL
            ORDER BY A1.CODIGO
            FETCH FIRST 5000 ROWS ONLY
        """)

        novos_tipos = cursor.fetchall()
        conn.close()

        if not novos_tipos:
            return {'inseridos': 0, 'mensagem': 'Nenhum tipo novo'}

        logger.info(f"✅ Encontrados {len(novos_tipos)} tipos novos")

        # Buscar pedidos correspondentes
        codigos_atendimento = [row[0] for row in novos_tipos]
        cache_pedidos = {}

        for codigo_atend in codigos_atendimento[:100]:
            url_pedido = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
            response = requests.get(
                url_pedido,
                headers=headers,
                params={
                    'select': 'id',
                    'codigo_orcamento_original': f'eq.{codigo_atend}',
                    'limit': 1
                },
                timeout=5
            )

            if response.status_code == 200:
                dados = response.json()
                if dados:
                    cache_pedidos[codigo_atend] = dados[0]['id']

        tipos_dados = []
        for row in novos_tipos:
            codigo_atend, tipo_processo = row

            pedido_id = cache_pedidos.get(codigo_atend)
            if not pedido_id:
                continue

            tipo = {
                'pedido_id': pedido_id,
                'codigo_atendimento_original': codigo_atend,
                'tipo_processo': limpar_string(tipo_processo)
            }
            tipos_dados.append(tipo)

        if not tipos_dados:
            return {'inseridos': 0, 'mensagem': 'Tipos sem pedidos correspondentes'}

        url = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
        response = requests.post(url, headers=headers, json=tipos_dados, timeout=60)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(tipos_dados),
                'mensagem': f'{len(tipos_dados)} tipos sincronizados'
            }
        else:
            logger.error(f"❌ Erro ao inserir tipos: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_tipos_processo_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/sync', methods=['GET', 'POST'])
def sync():
    """Endpoint principal de sincronização"""
    try:
        logger.info("="*70)
        logger.info("🚀 SINCRONIZAÇÃO INCREMENTAL V2.0")
        logger.info("="*70)

        inicio = datetime.now()

        result_clientes = sync_clientes_novos()
        logger.info(f"📋 Clientes: {result_clientes}")

        result_pedidos = sync_pedidos_novos()
        logger.info(f"📋 Pedidos: {result_pedidos}")

        result_formulas = sync_formulas_novas()
        logger.info(f"📋 Fórmulas: {result_formulas}")

        result_itens = sync_formulas_itens_novos()
        logger.info(f"📋 Itens: {result_itens}")

        result_rastreabilidade = sync_rastreabilidade_nova()
        logger.info(f"📋 Rastreabilidade: {result_rastreabilidade}")

        result_tipos = sync_tipos_processo_novos()
        logger.info(f"📋 Tipos Processo: {result_tipos}")

        tempo_total = (datetime.now() - inicio).total_seconds()

        resultado = {
            'sucesso': True,
            'timestamp': datetime.now().isoformat(),
            'tempo_execucao_segundos': tempo_total,
            'version': '2.0.0',
            'clientes': result_clientes,
            'pedidos': result_pedidos,
            'formulas': result_formulas,
            'formulas_itens': result_itens,
            'rastreabilidade': result_rastreabilidade,
            'tipos_processo': result_tipos,
            'total_inseridos': (
                result_clientes.get('inseridos', 0) +
                result_pedidos.get('inseridos', 0) +
                result_formulas.get('inseridos', 0) +
                result_itens.get('inseridos', 0) +
                result_rastreabilidade.get('inseridos', 0) +
                result_tipos.get('inseridos', 0)
            )
        }

        logger.info(f"✅ CONCLUÍDO - Total: {resultado['total_inseridos']} registros em {tempo_total:.1f}s")
        return jsonify(resultado)

    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}")
        return jsonify({
            'sucesso': False,
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
