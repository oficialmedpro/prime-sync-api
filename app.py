#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask para Sincronização Incremental Firebird -> Supabase
Endpoint: /sync (POST ou GET)
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

# Debug - remover depois
logger.info(f"FIREBIRD_HOST: {FIREBIRD_HOST}")
logger.info(f"FIREBIRD_DB: {FIREBIRD_DB}")
logger.info(f"FIREBIRD_USER: {FIREBIRD_USER}")
logger.info(f"FIREBIRD_PASS: {'***' if FIREBIRD_PASS else 'VAZIO'}")

SUPABASE_URL = os.getenv('SUPABASE_URL') or read_secret('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or read_secret('SUPABASE_KEY')
API_TOKEN = os.getenv('API_TOKEN') or read_secret('API_TOKEN')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api'
}

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
            }
        )

        if response.status_code == 200:
            dados = response.json()
            if dados:
                return dados[0][campo_id]
        return 0
    except Exception as e:
        logger.error(f"Erro ao buscar último ID de {tabela}: {e}")
        return 0

def sync_clientes_novos():
    """Sincroniza apenas clientes novos"""
    try:
        ultimo_codigo = get_ultimo_id_supabase('prime_clientes', 'codigo_cliente_original')
        logger.info(f"Último cliente no Supabase: {ultimo_codigo}")

        # Conectar Firebird
        conn = fdb.connect(
            host=FIREBIRD_HOST,
            database=FIREBIRD_DB,
            user=FIREBIRD_USER,
            password=FIREBIRD_PASS,
            charset='UTF8'
        )

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
            LIMIT 1000
        """)

        novos_clientes = cursor.fetchall()
        conn.close()

        if not novos_clientes:
            return {'inseridos': 0, 'mensagem': 'Nenhum cliente novo'}

        logger.info(f"Encontrados {len(novos_clientes)} clientes novos")

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
                'nome': row[1][:255] if row[1] else None,
                'cpf_cnpj': row[2][:20] if row[2] else None,
                'email': row[3][:255] if row[3] else None,
                'telefone': row[4] or row[5] or row[6],
                'endereco_logradouro': row[7][:255] if row[7] else None,
                'endereco_numero': str(row[8]) if row[8] else None,
                'endereco_complemento': row[9][:100] if row[9] else None,
                'endereco_bairro': row[10][:100] if row[10] else None,
                'endereco_cidade': row[11][:100] if row[11] else None,
                'endereco_estado': row[12][:2] if row[12] else None,
                'endereco_cep': row[13][:10] if row[13] else None,
                'data_nascimento': data_nasc,
                'sexo': row[17][:1] if row[17] else None,
                'data_cadastro': row[18].isoformat() if row[18] else None,
                'ativo': True,
                'updated_at': datetime.now().isoformat()
            }
            clientes_dados.append(cliente)

        # Inserir no Supabase
        url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
        response = requests.post(url, headers=headers, json=clientes_dados)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(clientes_dados),
                'mensagem': f'{len(clientes_dados)} clientes novos sincronizados'
            }
        else:
            logger.error(f"Erro ao inserir clientes: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"Erro em sync_clientes_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_pedidos_novos():
    """Sincroniza apenas pedidos novos"""
    try:
        ultimo_codigo = get_ultimo_id_supabase('prime_pedidos', 'codigo_orcamento_original')
        logger.info(f"Último pedido no Supabase: {ultimo_codigo}")

        conn = fdb.connect(
            host=FIREBIRD_HOST,
            database=FIREBIRD_DB,
            user=FIREBIRD_USER,
            password=FIREBIRD_PASS,
            charset='UTF8'
        )

        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                A.CODIGO,
                A.CODIGO_CLIENTE,
                A.AVIADA_DT,
                A.ENTREGUE_DT,
                A.VALORVENDA
            FROM ATENDIMENTO_A1 A
            WHERE A.CODIGO_CLIENTE IS NOT NULL
            AND A.CODIGO > {ultimo_codigo}
            ORDER BY A.CODIGO
            LIMIT 1000
        """)

        novos_pedidos = cursor.fetchall()
        conn.close()

        if not novos_pedidos:
            return {'inseridos': 0, 'mensagem': 'Nenhum pedido novo'}

        logger.info(f"Encontrados {len(novos_pedidos)} pedidos novos")

        cache_clientes = {}
        pedidos_dados = []

        for row in novos_pedidos:
            codigo_orcamento, codigo_cliente, aviada_dt, entregue_dt, valor_venda = row

            # Buscar cliente_id
            if codigo_cliente not in cache_clientes:
                url_cliente = f"{SUPABASE_URL}/rest/v1/prime_clientes"
                resp = requests.get(
                    url_cliente,
                    headers=headers,
                    params={
                        'select': 'id',
                        'codigo_cliente_original': f'eq.{codigo_cliente}',
                        'limit': 1
                    }
                )

                if resp.status_code == 200:
                    dados = resp.json()
                    if dados:
                        cache_clientes[codigo_cliente] = dados[0]['id']
                    else:
                        continue
                else:
                    continue

            cliente_id = cache_clientes[codigo_cliente]

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
                'status_aprovacao': status_aprovacao,
                'status_entrega': status_entrega,
                'status_geral': status_geral,
                'updated_at': datetime.now().isoformat()
            }
            pedidos_dados.append(pedido)

        if not pedidos_dados:
            return {'inseridos': 0, 'mensagem': 'Pedidos sem clientes correspondentes'}

        url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
        response = requests.post(url, headers=headers, json=pedidos_dados)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(pedidos_dados),
                'mensagem': f'{len(pedidos_dados)} pedidos novos sincronizados'
            }
        else:
            logger.error(f"Erro ao inserir pedidos: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"Erro em sync_pedidos_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/sync', methods=['GET', 'POST'])
def sync():
    """Endpoint principal de sincronização"""
    try:
        logger.info("="*70)
        logger.info("INICIANDO SINCRONIZAÇÃO INCREMENTAL")
        logger.info("="*70)

        inicio = datetime.now()

        result_clientes = sync_clientes_novos()
        logger.info(f"Clientes: {result_clientes}")

        result_pedidos = sync_pedidos_novos()
        logger.info(f"Pedidos: {result_pedidos}")

        tempo_total = (datetime.now() - inicio).total_seconds()

        resultado = {
            'sucesso': True,
            'timestamp': datetime.now().isoformat(),
            'tempo_execucao_segundos': tempo_total,
            'clientes': result_clientes,
            'pedidos': result_pedidos,
            'total_inseridos': result_clientes.get('inseridos', 0) + result_pedidos.get('inseridos', 0)
        }

        logger.info(f"CONCLUÍDO - Total: {resultado['total_inseridos']} registros")
        return jsonify(resultado)

    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        return jsonify({
            'sucesso': False,
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
