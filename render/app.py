#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask para Sincronização Incremental Firebird -> Supabase
Versão para Render.com (plano Hobby - gratuito)
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

# Configurações - Render usa variáveis de ambiente diretamente
FIREBIRD_HOST = os.getenv('FIREBIRD_HOST', 'db.primesoftware.com.br')
FIREBIRD_DB = os.getenv('FIREBIRD_DB', 'oficialmed1250')
FIREBIRD_USER = os.getenv('FIREBIRD_USER', 'OFICIALMED')
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
API_TOKEN = os.getenv('API_TOKEN', 'prime-sync-2025-xY9kL2mP4nQ8wR5t')

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
    """Pega o maior ID já migrado (ignorando códigos especiais > 500000)"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tabela}"
        
        params = {
            'select': campo_id,
            'order': f'{campo_id}.desc',
            'limit': 1
        }
        
        if tabela == 'prime_clientes':
            params[campo_id] = 'lt.500000'
        
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_id = dados[0][campo_id]
                return ultimo_id
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

# Importar todas as funções de sincronização do app.py original
# Por enquanto, vou copiar as principais funções aqui
# (Vou simplificar importando do arquivo original se possível)

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
                C.DIANASCIMENTO,
                C.MESNASCIMENTO,
                C.ANONASCIMENTO,
                C.SEXO,
                C.EMAIL1,
                CE.NOMECIDADE,
                CE.UF,
                C.ATIVO
            FROM CLIENTE C
            LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
            WHERE C.ATIVO = -1
            AND C.CODIGO > {ultimo_codigo}
            AND C.CODIGO < 500000
            ORDER BY C.CODIGO
            ROWS 1000
        """)

        novos_clientes = cursor.fetchall()

        if not novos_clientes:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhum cliente novo'}

        logger.info(f"✅ Encontrados {len(novos_clientes)} clientes novos")
        
        # Buscar telefones
        codigos = [row[0] for row in novos_clientes]
        codigos_str = ','.join(map(str, codigos))
        
        cursor.execute(f"""
            SELECT 
                CT.CODIGO_CADASTRO,
                CT.TELEFONEPREFIXO,
                CT.TELEFONE
            FROM CADASTRO_TELEFONE CT
            WHERE CT.TIPO_CADASTRO = 1
            AND CT.CODIGO_CADASTRO IN ({codigos_str})
        """)
        
        telefones_dict = {}
        for tel_row in cursor.fetchall():
            codigo_cli = tel_row[0]
            prefixo = str(tel_row[1]).strip() if tel_row[1] else ""
            numero = str(tel_row[2]).strip() if tel_row[2] else ""
            telefone_completo = (prefixo + numero).strip() or None
            if telefone_completo and codigo_cli not in telefones_dict:
                telefones_dict[codigo_cli] = telefone_completo
        
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
        
        enderecos_dict = {}
        for end_row in cursor.fetchall():
            codigo_cli = end_row[0]
            if codigo_cli not in enderecos_dict:
                enderecos_dict[codigo_cli] = {
                    'logradouro': end_row[1],
                    'numero': end_row[2],
                    'cep': end_row[3]
                }
        
        # Buscar totalizadores
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
        
        totalizadores_dict = {}
        for tot_row in cursor.fetchall():
            codigo_cli = tot_row[0]
            total = tot_row[1] or 1
            total_aprov = tot_row[2] or 1
            total_entreg = tot_row[3] or 1
            
            totalizadores_dict[codigo_cli] = {
                'total_orcamentos': tot_row[1] or 0,
                'total_orcamentos_aprovados': tot_row[2] or 0,
                'total_orcamentos_entregues': tot_row[3] or 0,
                'valor_total_orcamentos': float(tot_row[4]) if tot_row[4] else 0.0,
                'valor_total_aprovados': float(tot_row[5]) if tot_row[5] else 0.0,
                'valor_total_entregues': float(tot_row[6]) if tot_row[6] else 0.0,
                'valor_medio_orcamento': float(tot_row[4] / total) if tot_row[4] else 0.0,
                'valor_medio_aprovado': float(tot_row[5] / total_aprov) if tot_row[5] else 0.0,
                'valor_medio_entregue': float(tot_row[6] / total_entreg) if tot_row[6] else 0.0,
                'primeira_compra': tot_row[7].date().isoformat() if tot_row[7] else None,
                'ultima_compra': tot_row[8].date().isoformat() if tot_row[8] else None
            }
        
        conn.close()

        # Preparar dados
        clientes_dados = []
        for row in novos_clientes:
            codigo_cliente = row[0]
            
            data_nasc = None
            if row[3] and row[4] and row[5]:
                try:
                    data_nasc = f"{int(row[5])}-{int(row[4]):02d}-{int(row[3]):02d}"
                except:
                    pass

            telefone = telefones_dict.get(codigo_cliente)
            endereco = enderecos_dict.get(codigo_cliente, {})
            totalizadores = totalizadores_dict.get(codigo_cliente, {})

            cliente = {
                'codigo_cliente_original': codigo_cliente,
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
                'total_orcamentos': totalizadores.get('total_orcamentos', 0),
                'total_orcamentos_aprovados': totalizadores.get('total_orcamentos_aprovados', 0),
                'total_orcamentos_entregues': totalizadores.get('total_orcamentos_entregues', 0),
                'valor_total_orcamentos': totalizadores.get('valor_total_orcamentos', 0.0),
                'valor_total_aprovados': totalizadores.get('valor_total_aprovados', 0.0),
                'valor_total_entregues': totalizadores.get('valor_total_entregues', 0.0),
                'valor_medio_orcamento': totalizadores.get('valor_medio_orcamento', 0.0),
                'valor_medio_aprovado': totalizadores.get('valor_medio_aprovado', 0.0),
                'valor_medio_entregue': totalizadores.get('valor_medio_entregue', 0.0),
                'primeira_compra': totalizadores.get('primeira_compra'),
                'ultima_compra': totalizadores.get('ultima_compra')
            }
            clientes_dados.append(cliente)

        # Inserir no Supabase
        url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
        response = requests.post(url, headers=headers, json=clientes_dados, timeout=30)

        if response.status_code in [200, 201]:
            logger.info(f"✅ {len(clientes_dados)} clientes sincronizados")
            return {
                'inseridos': len(clientes_dados),
                'mensagem': f'{len(clientes_dados)} clientes sincronizados'
            }
        else:
            logger.error(f"❌ Erro ao inserir clientes: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_clientes_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

# Por questões de espaço, vou incluir apenas as funções principais
# As outras funções (sync_pedidos_novos, sync_formulas_novas, etc) devem ser copiadas do app.py original

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    API_VERSION = os.getenv('API_VERSION', '3.0.0')
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': API_VERSION,
        'service': 'render.com'
    })

@app.route('/sync', methods=['GET', 'POST'])
def sync():
    """Endpoint principal de sincronização"""
    try:
        logger.info("="*70)
        logger.info("🚀 SINCRONIZAÇÃO INCREMENTAL - RENDER.COM")
        logger.info("="*70)

        inicio = datetime.now()
        
        # Verificar autenticação
        auth_header = request.headers.get('Authorization', '')
        if API_TOKEN and f'Bearer {API_TOKEN}' not in auth_header:
            return jsonify({'erro': 'Não autorizado'}), 401

        # Sincronizar (ordem: clientes, pedidos, fórmulas, etc)
        result_clientes = sync_clientes_novos()
        logger.info(f"📋 Clientes: {result_clientes}")

        # TODO: Adicionar outras funções de sincronização aqui
        # result_pedidos = sync_pedidos_novos()
        # result_formulas = sync_formulas_novas()
        # etc...

        tempo_total = (datetime.now() - inicio).total_seconds()
        
        API_VERSION = os.getenv('API_VERSION', '3.0.0')
        resultado = {
            'sucesso': True,
            'timestamp': datetime.now().isoformat(),
            'tempo_execucao_segundos': tempo_total,
            'version': API_VERSION,
            'clientes': result_clientes,
            'total_inseridos': result_clientes.get('inseridos', 0)
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
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

