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
        try:
            with open(os.environ[file_path_var], 'r') as f:
                value = f.read().strip()
                logger.info(f"✅ Secret {env_var} lida do arquivo: {os.environ[file_path_var]}")
                return value
        except Exception as e:
            logger.error(f"❌ Erro ao ler secret {env_var}: {e}")

    # Tentar ler direto da env var
    value = os.getenv(env_var, '')
    if value:
        logger.info(f"✅ Secret {env_var} lida da variável de ambiente")
    else:
        logger.warning(f"⚠️  Secret {env_var} não encontrada!")
    return value

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
    """Pega o maior ID já migrado (ignorando códigos especiais > 500000)"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tabela}"
        
        # Params base
        params = {
            'select': campo_id,
            'order': f'{campo_id}.desc',
            'limit': 1
        }
        
        # Para clientes, ignorar códigos especiais (> 500000)
        # Exemplo: código 9999999 = "VENDA AO CONSUMIDOR" (cliente especial do Prime)
        if tabela == 'prime_clientes':
            params[campo_id] = 'lt.500000'  # Busca apenas códigos < 500000
        
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_id = dados[0][campo_id]
                if tabela == 'prime_clientes':
                    logger.info(f"   (Ignorando códigos especiais > 500000)")
                return ultimo_id
        return 0
    except Exception as e:
        logger.error(f"Erro ao buscar último ID de {tabela}: {e}")
        return 0

def buscar_todos_codigos_supabase(tabela, campo_id='codigo_cliente_original', filtro_especial=None):
    """Busca TODOS os códigos do Supabase usando paginação completa (corrigido para evitar gaps)"""
    codigos = set()
    offset = 0
    limit = 1000
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tabela}"
        
        while True:
            params = {
                'select': campo_id,
                'order': f'{campo_id}.asc',
                'limit': limit,
                'offset': offset
            }
            
            # Para clientes, ignorar códigos especiais (> 500000)
            if filtro_especial:
                params[campo_id] = filtro_especial
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                dados = response.json()
                if not dados:
                    break
                
                codigos.update([d[campo_id] for d in dados])
                
                if len(dados) < limit:
                    break
                
                offset += limit
            elif response.status_code == 206:  # Partial Content
                # Continuar mesmo com 206
                dados = response.json()
                if not dados:
                    break
                codigos.update([d[campo_id] for d in dados])
                if len(dados) < limit:
                    break
                offset += limit
            else:
                logger.warning(f"Erro ao buscar códigos: {response.status_code}")
                break
        
        logger.info(f"   ✅ Carregados {len(codigos):,} códigos de {tabela}")
        return codigos
    
    except Exception as e:
        logger.error(f"Erro ao buscar todos códigos de {tabela}: {e}")
        return codigos

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
    """Sincroniza clientes novos E verifica gaps para preencher
    
    🚨 IMPORTANTE: Busca dados de 3 tabelas:
    1. CLIENTE (dados básicos)
    2. CADASTRO_TELEFONE (telefones - WHERE TIPO_CADASTRO = 1)
    3. CADASTRO_ENDERECO (endereços - WHERE TIPO_CADASTRO = 1)
    
    CORRIGIDO V2.1: Verifica TODOS os códigos para identificar gaps
    """
    try:
        # Primeiro: buscar TODOS os códigos do Supabase para identificar gaps
        logger.info("   🔍 Verificando gaps em clientes...")
        codigos_supabase = buscar_todos_codigos_supabase('prime_clientes', 'codigo_cliente_original', 'lt.500000')
        max_codigo_sb = max(codigos_supabase) if codigos_supabase else 0
        logger.info(f"   📊 {len(codigos_supabase):,} clientes no Supabase (max: {max_codigo_sb})")
        
        # Buscar TODOS os códigos do Firebird (sem limitação ao máximo do Supabase para identificar todos os gaps)
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CODIGO
            FROM CLIENTE
            WHERE ATIVO = -1
            AND CODIGO < 500000
            ORDER BY CODIGO
        """)
        
        codigos_firebird = {row[0] for row in cursor.fetchall()}
        logger.info(f"   📊 {len(codigos_firebird):,} clientes no Firebird (total)")
        
        # Identificar gaps
        gaps = codigos_firebird - codigos_supabase
        gaps_list = sorted(list(gaps)) if gaps else []
        
        # Buscar novos registros (incremental)
        ultimo_codigo = max_codigo_sb
        logger.info(f"   📊 Buscando clientes novos (código > {ultimo_codigo})")
        
        # Buscar novos registros usando a mesma conexão
        cursor.execute(f"""
            SELECT CODIGO
            FROM CLIENTE
            WHERE ATIVO = -1
            AND CODIGO < 500000
            AND CODIGO > {ultimo_codigo}
            ORDER BY CODIGO
        """)
        novos_codigos = [row[0] for row in cursor.fetchall()]
        
        # Combinar gaps + novos registros
        todos_codigos_para_sincronizar = sorted(list(set(gaps_list + novos_codigos)))
        
        if not todos_codigos_para_sincronizar:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhum cliente novo'}
        
        if gaps:
            logger.info(f"   🔴 {len(gaps):,} GAPS encontrados em clientes! Preenchendo TODOS...")
        if novos_codigos:
            logger.info(f"   📊 {len(novos_codigos)} clientes novos encontrados")
        logger.info(f"   📊 Total a sincronizar: {len(todos_codigos_para_sincronizar):,} clientes")
        
        # Processar TODOS os códigos em lotes de 1000 até completar
        total_inseridos = 0
        lote_size = 1000
        
        for lote_idx in range(0, len(todos_codigos_para_sincronizar), lote_size):
            lote_codigos = todos_codigos_para_sincronizar[lote_idx:lote_idx + lote_size]
            codigos_str = ','.join(map(str, lote_codigos))
            
            logger.info(f"   📦 Processando lote {lote_idx//lote_size + 1} de {(len(todos_codigos_para_sincronizar) + lote_size - 1)//lote_size} ({len(lote_codigos)} clientes)...")
            
            # 1. Buscar clientes básicos deste lote
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
                AND C.CODIGO < 500000
                AND C.CODIGO IN ({codigos_str})
                ORDER BY C.CODIGO
            """)

            novos_clientes = cursor.fetchall()

            if not novos_clientes:
                continue
            
            # 2. Buscar telefones desses clientes (tabela CADASTRO_TELEFONE)
            codigos = [row[0] for row in novos_clientes]
            codigos_str_lote = ','.join(map(str, codigos))
            
            cursor.execute(f"""
                SELECT 
                    CT.CODIGO_CADASTRO,
                    CT.TELEFONEPREFIXO,
                    CT.TELEFONE
                FROM CADASTRO_TELEFONE CT
                WHERE CT.TIPO_CADASTRO = 1
                AND CT.CODIGO_CADASTRO IN ({codigos_str_lote})
            """)
            
            telefones_dict = {}
            for tel_row in cursor.fetchall():
                codigo_cli = tel_row[0]
                prefixo = str(tel_row[1]).strip() if tel_row[1] else ""
                numero = str(tel_row[2]).strip() if tel_row[2] else ""
                telefone_completo = (prefixo + numero).strip() or None
                
                if telefone_completo and codigo_cli not in telefones_dict:
                    telefones_dict[codigo_cli] = telefone_completo
            
            # 3. Buscar endereços desses clientes (tabela CADASTRO_ENDERECO)
            cursor.execute(f"""
                SELECT 
                    CE.CODIGO_CADASTRO,
                    CE.ENDERECO,
                    CE.NUMERO,
                    CE.CEP
                FROM CADASTRO_ENDERECO CE
                WHERE CE.TIPO_CADASTRO = 1
                AND CE.CODIGO_CADASTRO IN ({codigos_str_lote})
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
            
            # 4. Buscar totalizadores de pedidos (para calcular total_orcamentos, etc)
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
                WHERE A.CODIGO_CLIENTE IN ({codigos_str_lote})
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

            # 5. Preparar dados combinando as 3 fontes
            clientes_dados = []
            for row in novos_clientes:
                codigo_cliente = row[0]
                
                # Formatar data de nascimento
                data_nasc = None
                if row[3] and row[4] and row[5]:  # DIANASCIMENTO, MESNASCIMENTO, ANONASCIMENTO
                    try:
                        data_nasc = f"{int(row[5])}-{int(row[4]):02d}-{int(row[3]):02d}"
                    except:
                        pass

                # Buscar telefone da tabela CADASTRO_TELEFONE
                telefone = telefones_dict.get(codigo_cliente)
                
                # Buscar endereço da tabela CADASTRO_ENDERECO
                endereco = enderecos_dict.get(codigo_cliente, {})
                
                # Buscar totalizadores
                totalizadores = totalizadores_dict.get(codigo_cliente, {})

                # Montar cliente com TODOS os campos (mesmo que None)
                # IMPORTANTE: Todos os objetos devem ter as mesmas chaves para evitar erro PGRST102
                cliente = {
                    'codigo_cliente_original': codigo_cliente,
                    'nome': limpar_string(row[1])[:255] if row[1] else None,
                    'cpf_cnpj': limpar_string(row[2])[:20] if row[2] else None,
                    'ativo': bool(row[10]) if row[10] is not None else True,
                    'data_nascimento': data_nasc,  # Sempre presente (pode ser None)
                    'sexo': str(row[6])[:1] if row[6] else None,
                    'email': limpar_string(row[7])[:255] if row[7] else None,
                    'telefone': telefone,  # Da tabela CADASTRO_TELEFONE
                    'endereco_logradouro': limpar_string(endereco.get('logradouro'))[:255] if endereco.get('logradouro') else None,
                    'endereco_numero': str(endereco.get('numero')) if endereco.get('numero') else None,
                    'endereco_cep': limpar_string(endereco.get('cep'))[:10] if endereco.get('cep') else None,
                    'endereco_cidade': limpar_string(row[8])[:100] if row[8] else None,
                    'endereco_estado': limpar_string(row[9])[:2] if row[9] else None,
                    # Totalizadores de pedidos
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

            # 6. Inserir no Supabase usando upsert para evitar duplicatas
            url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
            headers_upsert = headers.copy()
            headers_upsert['Prefer'] = 'resolution=merge-duplicates'  # Upsert para evitar duplicatas
            
            # Inserir em lotes de 500 para evitar timeout
            for i in range(0, len(clientes_dados), 500):
                lote = clientes_dados[i:i+500]
                response = requests.post(url, headers=headers_upsert, json=lote, timeout=60)
                
                if response.status_code in [200, 201]:
                    total_inseridos += len(lote)
                    logger.info(f"   ✅ Lote {i//500 + 1}: {len(lote)} clientes sincronizados")
                else:
                    logger.error(f"   ❌ Erro ao inserir lote {i//500 + 1}: {response.status_code} - {response.text[:200]}")
        
        conn.close()

        if total_inseridos > 0:
            logger.info(f"✅ {total_inseridos:,} clientes sincronizados COM telefones e endereços")
            if gaps:
                logger.info(f"   ✅ TODOS os {len(gaps):,} gaps foram preenchidos!")
            return {
                'inseridos': total_inseridos,
                'gaps_preenchidos': len(gaps) if gaps else 0,
                'novos_registros': len(novos_codigos) if novos_codigos else 0,
                'mensagem': f'{total_inseridos:,} clientes sincronizados (gaps: {len(gaps) if gaps else 0}, novos: {len(novos_codigos) if novos_codigos else 0})'
            }
        else:
            return {'inseridos': 0, 'erro': 'Nenhum cliente inserido'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_clientes_novos: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            conn.close()
        except:
            pass
        return {'inseridos': 0, 'erro': str(e)}

def sync_pedidos_novos():
    """Sincroniza pedidos novos E verifica gaps para preencher"""
    try:
        # Primeiro: buscar TODOS os códigos do Supabase para identificar gaps
        logger.info("   🔍 Verificando gaps em pedidos...")
        codigos_supabase = buscar_todos_codigos_supabase('prime_pedidos', 'codigo_orcamento_original')
        max_codigo_sb = max(codigos_supabase) if codigos_supabase else 0
        logger.info(f"   📊 {len(codigos_supabase):,} pedidos no Supabase (max: {max_codigo_sb})")
        
        # Buscar TODOS os códigos do Firebird (sem limitação ao máximo do Supabase para identificar todos os gaps)
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CODIGO
            FROM ATENDIMENTO_A1
            WHERE CODIGO_CLIENTE IS NOT NULL
            ORDER BY CODIGO
        """)
        
        codigos_firebird = {row[0] for row in cursor.fetchall()}
        logger.info(f"   📊 {len(codigos_firebird):,} pedidos no Firebird (total)")
        
        # Identificar gaps
        gaps = codigos_firebird - codigos_supabase
        gaps_list = sorted(list(gaps)) if gaps else []
        
        # Buscar novos registros (incremental)
        ultimo_codigo = max_codigo_sb
        logger.info(f"   📊 Buscando pedidos novos (código > {ultimo_codigo})")
        
        cursor.execute(f"""
            SELECT CODIGO
            FROM ATENDIMENTO_A1
            WHERE CODIGO_CLIENTE IS NOT NULL
            AND CODIGO > {ultimo_codigo}
            ORDER BY CODIGO
        """)
        novos_codigos = [row[0] for row in cursor.fetchall()]
        
        # Combinar gaps + novos registros
        todos_codigos_para_sincronizar = sorted(list(set(gaps_list + novos_codigos)))
        
        if not todos_codigos_para_sincronizar:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhum pedido novo'}
        
        if gaps:
            logger.info(f"   🔴 {len(gaps):,} GAPS encontrados em pedidos! Preenchendo TODOS...")
        if novos_codigos:
            logger.info(f"   📊 {len(novos_codigos)} pedidos novos encontrados")
        logger.info(f"   📊 Total a sincronizar: {len(todos_codigos_para_sincronizar):,} pedidos")
        
        # Processar TODOS os códigos em lotes de 1000 até completar
        total_inseridos = 0
        lote_size = 1000
        
        for lote_idx in range(0, len(todos_codigos_para_sincronizar), lote_size):
            lote_codigos = todos_codigos_para_sincronizar[lote_idx:lote_idx + lote_size]
            codigos_str = ','.join(map(str, lote_codigos))
            
            logger.info(f"   📦 Processando lote {lote_idx//lote_size + 1} de {(len(todos_codigos_para_sincronizar) + lote_size - 1)//lote_size} ({len(lote_codigos)} pedidos)...")
            
            cursor.execute(f"""
                SELECT
                    A.CODIGO,
                    A.CODIGO_CLIENTE,
                    A.CADASTRO_DT,
                    A.AVIADA_DT,
                    A.ENTREGUE_DT,
                    A.VALORVENDA,
                    A.OBSERVACAO
                FROM ATENDIMENTO_A1 A
                WHERE A.CODIGO_CLIENTE IS NOT NULL
                AND A.CODIGO IN ({codigos_str})
                ORDER BY A.CODIGO
            """)

            novos_pedidos = cursor.fetchall()

            if not novos_pedidos:
                continue

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
                codigo_orcamento, codigo_cliente, cadastro_dt, aviada_dt, entregue_dt, valor_venda, observacao = row

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
                    'data_criacao': cadastro_dt.isoformat() if cadastro_dt else None,
                    'data_aprovacao': aviada_dt.isoformat() if aviada_dt else None,
                    'data_entrega': entregue_dt.isoformat() if entregue_dt else None,
                    'valor_total': float(valor_venda) if valor_venda else 0.0,
                    'observacoes': limpar_string(observacao),
                    'status_aprovacao': status_aprovacao,
                    'status_entrega': status_entrega,
                    'status_geral': status_geral
                }
                pedidos_dados.append(pedido)

            if not pedidos_dados:
                continue

            # Inserir usando upsert para evitar duplicatas
            url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
            headers_upsert = headers.copy()
            headers_upsert['Prefer'] = 'resolution=merge-duplicates'  # Upsert para evitar duplicatas
            
            # Inserir em lotes de 500
            for i in range(0, len(pedidos_dados), 500):
                lote = pedidos_dados[i:i+500]
                response = requests.post(url, headers=headers_upsert, json=lote, timeout=60)
                
                if response.status_code in [200, 201]:
                    total_inseridos += len(lote)
                    logger.info(f"   ✅ Lote {i//500 + 1}: {len(lote)} pedidos sincronizados")
                else:
                    logger.error(f"   ❌ Erro ao inserir lote {i//500 + 1}: {response.status_code}")
        
        conn.close()

        if total_inseridos > 0:
            logger.info(f"✅ {total_inseridos:,} pedidos sincronizados")
            if gaps:
                logger.info(f"   ✅ TODOS os {len(gaps):,} gaps foram preenchidos!")
            return {
                'inseridos': total_inseridos,
                'gaps_preenchidos': len(gaps) if gaps else 0,
                'novos_registros': len(novos_codigos) if novos_codigos else 0,
                'mensagem': f'{total_inseridos:,} pedidos sincronizados (gaps: {len(gaps) if gaps else 0}, novos: {len(novos_codigos) if novos_codigos else 0})'
            }
        else:
            return {'inseridos': 0, 'erro': 'Nenhum pedido inserido'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_pedidos_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_formulas_novas():
    """Sincroniza fórmulas novas com TEXTOROTULO - CORRIGIDO para evitar gaps"""
    try:
        logger.info("📋 Sincronizando fórmulas...")
        
        # Buscar TODAS as fórmulas existentes no Supabase (chave composta)
        logger.info("   Buscando fórmulas existentes no Supabase...")
        formulas_existentes = set()
        offset = 0
        limit = 1000
        
        url_formulas = f"{SUPABASE_URL}/rest/v1/prime_formulas"
        while True:
            response = requests.get(
                url_formulas,
                headers=headers,
                params={
                    'select': 'codigo_orcamento_original,numero_formula',
                    'order': 'codigo_orcamento_original.asc',
                    'limit': limit,
                    'offset': offset
                },
                timeout=30
            )
            
            if response.status_code in [200, 206]:
                dados = response.json()
                if not dados:
                    break
                for f in dados:
                    formulas_existentes.add((f['codigo_orcamento_original'], f['numero_formula']))
                if len(dados) < limit:
                    break
                offset += limit
            else:
                break
        
        logger.info(f"   ✅ {len(formulas_existentes):,} fórmulas já existem no Supabase")

        # Buscar fórmulas do Firebird
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                A2.CODIGO_ATEND_A1,
                A2.NUMEROFORMULA,
                A2.TEXTOROTULO,
                A2.POSOLOGIA,
                A2.VALORFORMULA_VENDA
            FROM ATENDIMENTO_A2 A2
            WHERE A2.CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY A2.CODIGO_ATEND_A1, A2.NUMEROFORMULA
        """)

        todas_formulas_fb = cursor.fetchall()
        conn.close()

        logger.info(f"   ✅ {len(todas_formulas_fb):,} fórmulas no Firebird")

        # Identificar fórmulas faltantes
        formulas_faltantes = []
        for row in todas_formulas_fb:
            codigo_atend, num_formula, texto_rotulo, posologia, valor = row
            chave = (codigo_atend, num_formula)
            if chave not in formulas_existentes:
                formulas_faltantes.append(row)

        if not formulas_faltantes:
            return {'inseridos': 0, 'mensagem': 'Nenhuma fórmula nova ou faltante'}

        logger.info(f"   🔍 {len(formulas_faltantes):,} fórmulas faltantes encontradas")

        # Buscar pedidos em lote
        codigos_orcamento = list(set([row[0] for row in formulas_faltantes]))
        cache_pedidos = {}
        offset_pedidos = 0
        while offset_pedidos < len(codigos_orcamento):
            lote_pedidos = codigos_orcamento[offset_pedidos:offset_pedidos+500]
            url_pedidos = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
            response = requests.get(
                url_pedidos,
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'codigo_orcamento_original': f'in.({",".join(map(str, lote_pedidos))})'
                },
                timeout=30
            )

            if response.status_code == 200:
                for ped in response.json():
                    cache_pedidos[ped['codigo_orcamento_original']] = ped['id']
            offset_pedidos += 500

        formulas_dados = []
        formulas_sem_pedido = []
        
        for row in formulas_faltantes:
            codigo_atend, num_formula, texto_rotulo, posologia, valor = row

            pedido_id = cache_pedidos.get(codigo_atend)
            # FK agora é opcional - permite inserir mesmo sem pedido (será atualizado depois)
            if not pedido_id:
                formulas_sem_pedido.append((codigo_atend, num_formula))

            formula = {
                'pedido_id': pedido_id,  # Pode ser NULL agora
                'codigo_orcamento_original': codigo_atend,
                'numero_formula': num_formula,
                'descricao': limpar_string(texto_rotulo),
                'posologia': limpar_string(posologia),
                'valor_formula': float(valor) if valor else 0.0,
                'updated_at': datetime.now().isoformat()
            }
            formulas_dados.append(formula)

        if formulas_sem_pedido:
            logger.info(f"   ⚠️ {len(formulas_sem_pedido)} fórmulas sem pedido (serão inseridas mesmo assim, FK será preenchida depois)")

        if not formulas_dados:
            return {'inseridos': 0, 'mensagem': 'Nenhuma fórmula para inserir'}

        # Inserir em lotes de 500
        total_inseridos = 0
        for i in range(0, len(formulas_dados), 500):
            lote = formulas_dados[i:i+500]
            url = f"{SUPABASE_URL}/rest/v1/prime_formulas"
            headers_insert = headers.copy()
            headers_insert['Prefer'] = 'resolution=ignore-duplicates'  # Evitar duplicatas
            response = requests.post(url, headers=headers_insert, json=lote, timeout=60)

            if response.status_code in [200, 201]:
                total_inseridos += len(lote)
                logger.info(f"   ✅ Lote {i//500 + 1}: {len(lote)} fórmulas inseridas")
            else:
                logger.error(f"   ❌ Erro ao inserir lote: {response.status_code}")

        return {
            'inseridos': total_inseridos,
            'mensagem': f'{total_inseridos} fórmulas sincronizadas'
        }

    except Exception as e:
        logger.error(f"❌ Erro em sync_formulas_novas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {'inseridos': 0, 'erro': str(e)}

def sync_formulas_itens_novos():
    """Sincroniza itens das fórmulas (ATENDIMENTO_A3) COM GAP FILLING COMPLETO - V2.2.4
    
    CORREÇÃO CRÍTICA: Agora busca TODOS os itens do Firebird (não apenas os de fórmulas existentes)
    e cria fórmulas automaticamente se não existirem no Supabase.
    """
    try:
        logger.info("📋 Sincronizando itens de fórmulas (com gap filling)...")
        
        # 1. Buscar TODAS as chaves (codigo_atend, numero_formula, numero_linha) do Supabase
        logger.info("   🔍 Verificando gaps em itens de fórmulas...")
        chaves_supabase = set()
        offset = 0
        limit = 1000
        
        url_itens = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
        while True:
            response = requests.get(
                url_itens,
                headers=headers,
                params={
                    'select': 'codigo_atendimento_original,numero_formula,numero_linha',
                    'limit': limit,
                    'offset': offset
                },
                timeout=30
            )
            
            if response.status_code == 200:
                dados = response.json()
                if not dados:
                    break
                for item in dados:
                    chave = (item['codigo_atendimento_original'], item['numero_formula'], item['numero_linha'])
                    chaves_supabase.add(chave)
                if len(dados) < limit:
                    break
                offset += limit
            else:
                break
        
        logger.info(f"   📊 {len(chaves_supabase):,} itens no Supabase")
        
        # 2. Buscar TODOS os itens do Firebird que têm fórmulas correspondentes no Supabase
        conn = conectar_firebird()
        cursor = conn.cursor()
        
        # Primeiro, buscar todas as fórmulas do Supabase para filtrar
        cache_formulas = {}
        offset = 0
        while offset < 50000:  # Max 50k fórmulas
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_formulas",
                headers=headers,
                params={
                    'select': 'id,pedido_id,codigo_orcamento_original,numero_formula',
                    'limit': 1000,
                    'offset': offset
                },
                timeout=10
            )
            if response.status_code == 200:
                dados = response.json()
                if not dados:
                    break
                for formula in dados:
                    chave = (formula['codigo_orcamento_original'], formula['numero_formula'])
                    cache_formulas[chave] = {'id': formula['id'], 'pedido_id': formula['pedido_id']}
                offset += 1000
            else:
                break
        
        logger.info(f"   📊 {len(cache_formulas):,} fórmulas no Supabase")
        
        # Buscar TODOS os itens do Firebird (não apenas os de fórmulas existentes no Supabase)
        # Isso garante que gaps de itens sejam identificados mesmo se a fórmula ainda não existir
        logger.info("   📊 Buscando TODOS os itens do Firebird...")
        todos_itens_firebird = []
        
        # Buscar em lotes para evitar timeout
        max_codigo_atend = max([chave[0] for chave in cache_formulas.keys()]) if cache_formulas else 0
        
        # Buscar itens em lotes de 5000 códigos de atendimento
        cursor.execute("""
            SELECT DISTINCT CODIGO_ATEND_A1
            FROM ATENDIMENTO_A3
            WHERE CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY CODIGO_ATEND_A1
        """)
        todos_codigos_atend = [row[0] for row in cursor.fetchall()]
        logger.info(f"   📊 {len(todos_codigos_atend):,} códigos de atendimento com itens no Firebird")
        
        lote_size = 1000
        for i in range(0, len(todos_codigos_atend), lote_size):
            lote_codigos = todos_codigos_atend[i:i+lote_size]
            codigos_str = ','.join(map(str, lote_codigos))
            
            cursor.execute(f"""
                SELECT
                    A3.CODIGO_ATEND_A1,
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
                LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
                WHERE A3.CODIGO_ATEND_A1 IN ({codigos_str})
                AND A3.CODIGO_ATEND_A1 IS NOT NULL
                ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
            """)
            
            todos_itens_firebird.extend(cursor.fetchall())
            
            if (i // lote_size + 1) % 10 == 0:
                logger.info(f"   📊 Processados {min(i + lote_size, len(todos_codigos_atend)):,}/{len(todos_codigos_atend):,} códigos de atendimento...")
        
        conn.close()
        logger.info(f"   ✅ {len(todos_itens_firebird):,} itens carregados do Firebird")
        
        # Identificar gaps
        chaves_firebird = set()
        itens_dict = {}
        for row in todos_itens_firebird:
            chave = (row[0], row[1], row[2])  # (codigo_atend, num_formula, num_linha)
            chaves_firebird.add(chave)
            itens_dict[chave] = row
        
        gaps = chaves_firebird - chaves_supabase
        gaps_list = sorted(list(gaps))
        
        if gaps:
            logger.info(f"   🔴 {len(gaps):,} GAPS encontrados em itens! Preenchendo...")
        
        # Buscar novos itens (incremental - código atendimento maior que o máximo)
        max_codigo = max([chave[0] for chave in chaves_supabase]) if chaves_supabase else 0
        logger.info(f"   📊 Buscando itens novos (código atendimento > {max_codigo})")
        
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                A3.CODIGO_ATEND_A1,
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
            LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
            WHERE A3.CODIGO_ATEND_A1 > {max_codigo}
            AND A3.CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
            ROWS 5000
        """)

        novos_itens = cursor.fetchall()
        conn.close()
        
        # Combinar gaps + novos itens
        todos_itens_para_sincronizar = []
        for chave in gaps_list:
            if chave in itens_dict:
                todos_itens_para_sincronizar.append(itens_dict[chave])
        todos_itens_para_sincronizar.extend(novos_itens)
        
        if not todos_itens_para_sincronizar:
            return {'inseridos': 0, 'mensagem': 'Nenhum item novo ou faltante'}
        
        logger.info(f"   📊 Total a sincronizar: {len(todos_itens_para_sincronizar):,} itens (gaps: {len(gaps)}, novos: {len(novos_itens)})")

        # 3. Preparar dados para inserção
        itens_dados = []
        itens_sem_formula = []
        
        for row in todos_itens_para_sincronizar:
            (codigo_atend, num_formula, num_linha, codigo_produto, nome_produto,
             quantidade, unidade, valor_custo, valor_venda, observacao) = row

            chave = (codigo_atend, num_formula)
            formula_info = cache_formulas.get(chave)

            # Se fórmula não existe no cache, tentar buscar no Supabase novamente
            if not formula_info:
                try:
                    response = requests.get(
                        f"{SUPABASE_URL}/rest/v1/prime_formulas",
                        headers=headers,
                        params={
                            'select': 'id,pedido_id,codigo_orcamento_original,numero_formula',
                            'codigo_orcamento_original': f'eq.{codigo_atend}',
                            'numero_formula': f'eq.{num_formula}'
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        dados = response.json()
                        if dados:
                            formula_info = {
                                'id': dados[0]['id'],
                                'pedido_id': dados[0]['pedido_id']
                            }
                            # Adicionar ao cache para próximas iterações
                            cache_formulas[chave] = formula_info
                except:
                    pass

            # Se ainda não encontrou, tentar criar a fórmula buscando dados do Firebird
            if not formula_info:
                try:
                    # Buscar dados da fórmula no Firebird
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
                        WHERE A2.CODIGO_ATEND_A1 = {codigo_atend}
                        AND A2.NUMEROFORMULA = {num_formula}
                    """)
                    formula_fb = cursor.fetchone()
                    conn.close()
                    
                    if formula_fb:
                        # Buscar pedido no Supabase
                        response = requests.get(
                            f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                            headers=headers,
                            params={
                                'select': 'id',
                                'codigo_orcamento_original': f'eq.{codigo_atend}'
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            pedidos = response.json()
                            if pedidos:
                                pedido_id = pedidos[0]['id']
                                # Criar fórmula no Supabase
                                formula_data = {
                                    'pedido_id': pedido_id,
                                    'codigo_orcamento_original': codigo_atend,
                                    'numero_formula': num_formula,
                                    'descricao': limpar_string(formula_fb[2]) if len(formula_fb) > 2 else '',
                                    'posologia': limpar_string(formula_fb[3]) if len(formula_fb) > 3 else '',
                                    'valor_formula': float(formula_fb[4]) if len(formula_fb) > 4 and formula_fb[4] else 0.0,
                                    'updated_at': datetime.now().isoformat()
                                }
                                
                                response_create = requests.post(
                                    f"{SUPABASE_URL}/rest/v1/prime_formulas",
                                    headers={**headers, 'Prefer': 'resolution=ignore-duplicates'},
                                    json=[formula_data],
                                    timeout=30
                                )
                                
                                if response_create.status_code in [200, 201]:
                                    created = response_create.json()
                                    if created and len(created) > 0:
                                        formula_info = {
                                            'id': created[0]['id'],
                                            'pedido_id': pedido_id
                                        }
                                        cache_formulas[chave] = formula_info
                                        logger.info(f"   ✅ Fórmula criada automaticamente: {codigo_atend}/{num_formula}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Não foi possível criar fórmula {codigo_atend}/{num_formula}: {e}")

            # FK agora são opcionais - permite inserir mesmo sem fórmula/pedido (serão atualizados depois)
            if not formula_info:
                itens_sem_formula.append((codigo_atend, num_formula))
                # Tentar buscar pedido_id diretamente se fórmula não existir
                pedido_id_direto = None
                try:
                    response = requests.get(
                        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                        headers=headers,
                        params={
                            'select': 'id',
                            'codigo_orcamento_original': f'eq.{codigo_atend}'
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        pedidos = response.json()
                        if pedidos:
                            pedido_id_direto = pedidos[0]['id']
                except:
                    pass

            item = {
                'formula_id': formula_info['id'] if formula_info else None,  # Pode ser NULL agora
                'pedido_id': formula_info['pedido_id'] if formula_info else pedido_id_direto,  # Pode ser NULL agora
                'codigo_atendimento_original': codigo_atend,
                'numero_formula': num_formula,
                'numero_linha': num_linha,
                'codigo_produto': codigo_produto,
                'nome_produto': limpar_string(nome_produto) or 'PRODUTO NÃO IDENTIFICADO',
                'quantidade': float(quantidade) if quantidade else None,
                'unidade': limpar_string(unidade),
                'quantidade_calculo': float(quantidade) if quantidade else None,
                'valor_custo': float(valor_custo) if valor_custo else 0.0,
                'valor_venda': float(valor_venda) if valor_venda else 0.0,
                'valor_venda_desconto': 0.0,
                'inclusao_sistema': True,
                'visualizar_produto': True,
                'observacao': limpar_string(observacao),
                'updated_at': datetime.now().isoformat()
            }
            itens_dados.append(item)

        if itens_sem_formula:
            logger.info(f"   ⚠️ {len(itens_sem_formula)} itens sem fórmulas correspondentes (serão inseridos mesmo assim, FK será preenchida depois)")

        if not itens_dados:
            return {'inseridos': 0, 'mensagem': 'Nenhum item para inserir'}

        # Headers com ignore-duplicates (corrigido para inserir em lotes)
        headers_insert = headers.copy()
        headers_insert['Prefer'] = 'resolution=ignore-duplicates'
        
        # Inserir em lotes de 500 para evitar timeout e HTTP 409
        url = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
        total_inseridos = 0
        total_erros = 0
        
        for i in range(0, len(itens_dados), 500):
            lote = itens_dados[i:i+500]
            try:
                response = requests.post(url, headers=headers_insert, json=lote, timeout=60)
                
                if response.status_code in [200, 201]:
                    total_inseridos += len(lote)
                    logger.info(f"   ✅ Lote {i//500 + 1}: {len(lote)} itens sincronizados")
                elif response.status_code == 409:
                    # HTTP 409 = conflito (duplicatas) - tentar inserir item por item ou pular
                    logger.warning(f"   ⚠️ Lote {i//500 + 1}: HTTP 409 (duplicatas) - tentando inserir individualmente...")
                    # Tentar inserir item por item para identificar quais já existem
                    inseridos_lote = 0
                    for item in lote:
                        try:
                            resp_item = requests.post(url, headers=headers_insert, json=[item], timeout=30)
                            if resp_item.status_code in [200, 201]:
                                inseridos_lote += 1
                        except:
                            pass
                    total_inseridos += inseridos_lote
                    if inseridos_lote < len(lote):
                        logger.info(f"   ⚠️ Lote {i//500 + 1}: {inseridos_lote}/{len(lote)} itens inseridos (alguns já existiam)")
                else:
                    total_erros += len(lote)
                    logger.error(f"   ❌ Erro ao inserir lote {i//500 + 1}: {response.status_code} - {response.text[:200]}")
            except Exception as e:
                total_erros += len(lote)
                logger.error(f"   ❌ Exceção ao inserir lote {i//500 + 1}: {e}")

        if total_inseridos > 0:
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} itens sincronizados'
            }
        else:
            return {'inseridos': 0, 'erro': f'HTTP 409 ou erro na inserção (tentados {len(itens_dados)} itens)'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_formulas_itens_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

def sync_rastreabilidade_nova():
    """Sincroniza rastreabilidade com gap filling (PROCESSO_MANIPULACAO)"""
    try:
        logger.info("📋 Sincronizando rastreabilidade (com gap filling)...")

        headers = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Accept-Profile': 'api',
            'Content-Profile': 'api'
        }

        # Buscar TODOS os códigos existentes no Supabase (gap filling)
        logger.info("   🔍 Buscando códigos existentes no Supabase...")
        codigos_existentes = set()
        offset = 0
        limit = 1000
        while True:
            url_existentes = f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade"
            response = requests.get(
                url_existentes,
                headers=headers,
                params={
                    'select': 'codigo_processo_original',
                    'order': 'codigo_processo_original.asc',
                    'limit': limit,
                    'offset': offset
                },
                timeout=30
            )
            if response.status_code == 200:
                dados = response.json()
                if not dados:
                    break
                codigos_existentes.update([r['codigo_processo_original'] for r in dados])
                if len(dados) < limit:
                    break
                offset += limit
                if offset % 10000 == 0:
                    logger.info(f"      Carregados {len(codigos_existentes):,} códigos...")
            else:
                break

        logger.info(f"   📊 {len(codigos_existentes):,} registros já existem no Supabase")

        # Buscar TODOS os registros do Firebird
        logger.info("   🔍 Buscando todos os registros do Firebird...")
        conn = conectar_firebird()
        cursor = conn.cursor()
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
            WHERE PM.CODIGO_MOV IS NOT NULL
            ORDER BY PM.CODIGO
        """)
        todas_rastreabilidade_fb = cursor.fetchall()
        conn.close()

        logger.info(f"   ✅ {len(todas_rastreabilidade_fb):,} registros no Firebird")

        # Identificar registros faltantes
        rastreabilidade_faltantes = []
        for row in todas_rastreabilidade_fb:
            codigo_processo = row[0]
            if codigo_processo not in codigos_existentes:
                rastreabilidade_faltantes.append(row)

        if not rastreabilidade_faltantes:
            return {'inseridos': 0, 'mensagem': 'Nenhum registro faltante'}

        logger.info(f"   🔍 {len(rastreabilidade_faltantes):,} registros faltantes encontrados")

        # Buscar pedidos e tipos em lote (cache)
        codigos_orcamento = list(set([row[2] for row in rastreabilidade_faltantes if row[2]]))
        codigos_tipos = list(set([row[3] for row in rastreabilidade_faltantes if row[3]]))

        cache_pedidos = {}
        cache_tipos = {}

        # Cache de pedidos
        for i in range(0, len(codigos_orcamento), 500):
            lote = codigos_orcamento[i:i+500]
            url_pedidos = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
            response = requests.get(
                url_pedidos,
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'codigo_orcamento_original': f'in.({",".join(map(str, lote))})'
                },
                timeout=30
            )
            if response.status_code == 200:
                for ped in response.json():
                    cache_pedidos[ped['codigo_orcamento_original']] = ped['id']

        # Cache de tipos
        for i in range(0, len(codigos_tipos), 500):
            lote = codigos_tipos[i:i+500]
            url_tipos = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
            response = requests.get(
                url_tipos,
                headers=headers,
                params={
                    'select': 'id,codigo_tipo_original',
                    'codigo_tipo_original': f'in.({",".join(map(str, lote))})'
                },
                timeout=30
            )
            if response.status_code == 200:
                for tipo in response.json():
                    cache_tipos[tipo['codigo_tipo_original']] = tipo['id']

        # Preparar dados
        rastreabilidade_dados = []
        registros_sem_fk = []
        
        for row in rastreabilidade_faltantes:
            codigo_orcamento = row[2]
            codigo_tipo = row[3]

            pedido_id = cache_pedidos.get(codigo_orcamento)
            tipo_processo_id = cache_tipos.get(codigo_tipo)

            # FK agora são opcionais - permite inserir mesmo sem pedido/tipo (serão atualizados depois)
            if not pedido_id or not tipo_processo_id:
                registros_sem_fk.append((codigo_orcamento, codigo_tipo))

            rastro = {
                'codigo_processo_original': row[0],
                'pedido_id': pedido_id,  # Pode ser NULL agora
                'codigo_orcamento_original': codigo_orcamento,
                'tipo_processo_id': tipo_processo_id,  # Pode ser NULL agora
                'codigo_tipo_original': codigo_tipo,
                'tipo_movimento': row[1],
                'codigo_funcionario': row[4],
                'data_processo': row[5].isoformat() if row[5] else None,
                'hora_processo': str(row[6]) if row[6] else None,
                'sequencia': row[7],
                'status_processo': 'CONCLUIDO',
                'updated_at': datetime.now().isoformat()
            }
            rastreabilidade_dados.append(rastro)

        if registros_sem_fk:
            logger.info(f"   ⚠️ {len(registros_sem_fk)} registros sem FK (serão inseridos mesmo assim, FK será preenchida depois)")

        if not rastreabilidade_dados:
            return {'inseridos': 0, 'mensagem': 'Nenhum registro para inserir'}

        # Inserir em lotes de 500
        total_inseridos = 0
        for i in range(0, len(rastreabilidade_dados), 500):
            lote = rastreabilidade_dados[i:i+500]
            url = f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade"
            headers_insert = headers.copy()
            headers_insert['Prefer'] = 'resolution=ignore-duplicates'
            response = requests.post(url, headers=headers_insert, json=lote, timeout=60)

            if response.status_code in [200, 201]:
                total_inseridos += len(lote)
                logger.info(f"   ✅ Lote {i//500 + 1}: {len(lote)} registros inseridos")
            else:
                logger.error(f"   ❌ Erro ao inserir lote: {response.status_code} - {response.text[:200]}")

        return {
            'inseridos': total_inseridos,
            'mensagem': f'{total_inseridos} registros sincronizados'
        }

    except Exception as e:
        logger.error(f"❌ Erro em sync_rastreabilidade_nova: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
                FPT.CODIGO,
                FPT.NOMETIPO,
                FPT.NOMEFICHA,
                FPT.TIPO_PRODUCAO,
                FPT.SEQUENCIA,
                FPT.ATIVO,
                FPT.PROCESSO_OPCIONAL,
                FPT.PAGARCOMISSAO,
                FPT.REGISTRAR_BAIXA,
                FPT.BLOQUEAR_CALCULO,
                FPT.LIBERAR_ENTREGA,
                FPT.BLOQUEAR_RECEITA,
                FPT.OBSERVACAO
            FROM FORMAFARMACEUTICA_PROCESSO_TIPO FPT
            WHERE FPT.CODIGO > {ultimo_codigo}
            ORDER BY FPT.CODIGO
            ROWS 1000
        """)

        novos_tipos = cursor.fetchall()
        conn.close()

        if not novos_tipos:
            return {'inseridos': 0, 'mensagem': 'Nenhum tipo novo'}

        logger.info(f"✅ Encontrados {len(novos_tipos)} tipos novos")

        # Preparar dados
        tipos_dados = []
        for row in novos_tipos:
            tipo = {
                'codigo_tipo_original': row[0],
                'nome_processo': limpar_string(row[1])[:100] if row[1] else None,
                'nome_ficha': limpar_string(row[2])[:100] if row[2] else None,
                'tipo_producao': row[3],
                'sequencia': row[4],
                'ativo': bool(row[5]) if row[5] is not None else True,
                'processo_opcional': bool(row[6]) if row[6] is not None else False,
                'pagar_comissao': bool(row[7]) if row[7] is not None else False,
                'registrar_baixa': bool(row[8]) if row[8] is not None else False,
                'bloquear_calculo': bool(row[9]) if row[9] is not None else False,
                'liberar_entrega': bool(row[10]) if row[10] is not None else False,
                'bloquear_receita': bool(row[11]) if row[11] is not None else False,
                'observacao': limpar_string(row[12]) if row[12] else None,
                'updated_at': datetime.now().isoformat()
            }
            tipos_dados.append(tipo)

        if not tipos_dados:
            return {'inseridos': 0, 'mensagem': 'Nenhum tipo válido'}

        # Headers com UPSERT (merge duplicates)
        headers_upsert = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Accept-Profile': 'api',
            'Content-Profile': 'api',
            'Prefer': 'resolution=merge-duplicates,return=representation'
        }

        url = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
        response = requests.post(url, headers=headers_upsert, json=tipos_dados, timeout=60)

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
        'version': '2.2.6'
    })

def sync_missing_pedidos():
    """Sincroniza pedidos faltantes (buracos)"""
    try:
        logger.info("🔍 Buscando pedidos faltantes...")

        # Pegar todos códigos de pedidos já no Supabase
        todos_pedidos_sb = []
        offset = 0
        limit = 1000

        while True:
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                headers=headers,
                params={
                    'select': 'codigo_orcamento_original',
                    'limit': limit,
                    'offset': offset,
                    'order': 'codigo_orcamento_original.asc'
                },
                timeout=30
            )

            if resp.status_code == 200:
                dados = resp.json()
                if not dados:
                    break
                todos_pedidos_sb.extend([d['codigo_orcamento_original'] for d in dados])
                offset += limit
            else:
                break

        codigos_sb = set(todos_pedidos_sb)
        max_codigo_sb = max(codigos_sb) if codigos_sb else 0

        logger.info(f"   {len(codigos_sb)} pedidos já sincronizados (max: {max_codigo_sb})")

        # Buscar todos pedidos do Firebird até o max_codigo_sb
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT CODIGO
            FROM ATENDIMENTO_A1
            WHERE CODIGO_CLIENTE IS NOT NULL
            AND CODIGO <= {max_codigo_sb}
            ORDER BY CODIGO
        """)

        todos_pedidos_fb = [row[0] for row in cursor.fetchall()]
        codigos_fb = set(todos_pedidos_fb)

        logger.info(f"   {len(codigos_fb)} pedidos no Firebird (até código {max_codigo_sb})")

        # Encontrar buracos
        faltantes = codigos_fb - codigos_sb

        if not faltantes:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhum pedido faltante'}

        logger.info(f"   🔴 {len(faltantes)} pedidos FALTANTES identificados!")

        # Buscar dados dos pedidos faltantes (em lotes de 1000)
        faltantes_list = sorted(list(faltantes))
        total_inseridos = 0

        for i in range(0, len(faltantes_list), 1000):
            lote = faltantes_list[i:i+1000]
            codigos_str = ','.join(map(str, lote))

            cursor.execute(f"""
                SELECT
                    A.CODIGO,
                    A.CODIGO_CLIENTE,
                    A.CADASTRO_DT,
                    A.AVIADA_DT,
                    A.ENTREGUE_DT,
                    A.VALORVENDA,
                    A.OBSERVACAO
                FROM ATENDIMENTO_A1 A
                WHERE A.CODIGO IN ({codigos_str})
            """)

            pedidos_faltantes = cursor.fetchall()

            # Buscar clientes
            codigos_cliente = list(set([row[1] for row in pedidos_faltantes]))
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_clientes",
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

            # Preparar dados
            pedidos_dados = []
            for row in pedidos_faltantes:
                codigo_cli = row[1]
                if codigo_cli not in cache_clientes:
                    continue

                pedidos_dados.append({
                    'codigo_orcamento_original': row[0],
                    'cliente_id': cache_clientes[codigo_cli],
                    'codigo_cliente_original': codigo_cli,
                    'data_criacao': row[2].isoformat() if row[2] else None,
                    'data_aprovacao': row[3].isoformat() if row[3] else None,
                    'data_entrega': row[4].isoformat() if row[4] else None,
                    'valor_total': float(row[5]) if row[5] else 0.0,
                    'observacoes': limpar_string(row[6]),
                    'status': 'aprovado' if row[3] else 'pendente'
                })

            if pedidos_dados:
                # Usar ignore-duplicates para evitar erro
                headers_insert = headers.copy()
                headers_insert['Prefer'] = 'resolution=ignore-duplicates'

                resp_insert = requests.post(
                    f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                    headers=headers_insert,
                    json=pedidos_dados,
                    timeout=60
                )

                if resp_insert.status_code in [200, 201]:
                    total_inseridos += len(pedidos_dados)
                    logger.info(f"   ✅ Lote {i//1000 + 1}: {len(pedidos_dados)} pedidos inseridos")

        conn.close()
        return {
            'inseridos': total_inseridos,
            'mensagem': f'{total_inseridos} pedidos faltantes sincronizados'
        }

    except Exception as e:
        logger.error(f"❌ Erro em sync_missing_pedidos: {e}")
        return {'inseridos': 0, 'erro': str(e)}

@app.route('/sync-missing', methods=['POST'])
def sync_missing():
    """Endpoint para sincronizar registros faltantes"""
    try:
        logger.info("="*70)
        logger.info("🔧 SINCRONIZAÇÃO DE REGISTROS FALTANTES")
        logger.info("="*70)

        inicio = datetime.now()

        result_pedidos = sync_missing_pedidos()
        logger.info(f"📋 Pedidos Faltantes: {result_pedidos}")

        tempo_total = (datetime.now() - inicio).total_seconds()

        resultado = {
            'sucesso': True,
            'timestamp': datetime.now().isoformat(),
            'tempo_execucao_segundos': tempo_total,
            'pedidos_faltantes': result_pedidos,
            'total_inseridos': result_pedidos.get('inseridos', 0)
        }

        logger.info(f"✅ CONCLUÍDO - Total: {resultado['total_inseridos']} registros em {tempo_total:.1f}s")
        return jsonify(resultado)

    except Exception as e:
        logger.error(f"❌ Erro na sincronização de faltantes: {e}")
        return jsonify({
            'sucesso': False,
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def atualizar_fk_automaticamente():
    """Preenche automaticamente campos FK que estão NULL (executado após cada etapa de sincronização)"""
    try:
        logger.info("\n" + "="*70)
        logger.info("🔗 ATUALIZANDO FOREIGN KEYS AUTOMATICAMENTE...")
        logger.info("="*70)
        
        total_atualizados = 0
        
        # 1. Atualizar pedidos.cliente_id (após sincronizar clientes)
        logger.info("   1️⃣ Atualizando pedidos.cliente_id...")
        url = f"{SUPABASE_URL}/rest/v1/rpc/atualizar_pedidos_cliente_id"
        response = requests.post(url, headers=headers, json={}, timeout=30)
        if response.status_code == 200:
            count = response.json() if isinstance(response.json(), int) else 0
            total_atualizados += count
            logger.info(f"      ✅ {count} pedidos atualizados")
        else:
            # Se não existe a função RPC, fazer via UPDATE direto em lotes
            offset = 0
            limit = 1000
            count = 0
            while True:
                # Buscar pedidos sem cliente_id
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                    headers=headers,
                    params={
                        'select': 'id,codigo_cliente_original',
                        'cliente_id': 'is.null',
                        'limit': limit,
                        'offset': offset
                    },
                    timeout=30
                )
                if response.status_code != 200:
                    break
                pedidos = response.json()
                if not pedidos:
                    break
                
                # Buscar clientes correspondentes
                codigos_cliente = [p['codigo_cliente_original'] for p in pedidos]
                response_clientes = requests.get(
                    f"{SUPABASE_URL}/rest/v1/prime_clientes",
                    headers=headers,
                    params={
                        'select': 'id,codigo_cliente_original',
                        'codigo_cliente_original': f'in.({",".join(map(str, codigos_cliente))})'
                    },
                    timeout=30
                )
                
                if response_clientes.status_code == 200:
                    clientes = {c['codigo_cliente_original']: c['id'] for c in response_clientes.json()}
                    
                    # Atualizar pedidos em lote
                    for pedido in pedidos:
                        cliente_id = clientes.get(pedido['codigo_cliente_original'])
                        if cliente_id:
                            response_update = requests.patch(
                                f"{SUPABASE_URL}/rest/v1/prime_pedidos?id=eq.{pedido['id']}",
                                headers=headers,
                                json={'cliente_id': cliente_id},
                                timeout=10
                            )
                            if response_update.status_code in [200, 204]:
                                count += 1
                
                offset += limit
                if len(pedidos) < limit:
                    break
            
            total_atualizados += count
            if count > 0:
                logger.info(f"      ✅ {count} pedidos atualizados")
        
        # 2. Atualizar formulas.pedido_id (após sincronizar pedidos)
        logger.info("   2️⃣ Atualizando formulas.pedido_id...")
        offset = 0
        count = 0
        while True:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_formulas",
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'pedido_id': 'is.null',
                    'limit': 1000,
                    'offset': offset
                },
                timeout=30
            )
            if response.status_code != 200:
                break
            formulas = response.json()
            if not formulas:
                break
            
            codigos_pedido = [f['codigo_orcamento_original'] for f in formulas]
            response_pedidos = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'codigo_orcamento_original': f'in.({",".join(map(str, codigos_pedido))})'
                },
                timeout=30
            )
            
            if response_pedidos.status_code == 200:
                pedidos_dict = {p['codigo_orcamento_original']: p['id'] for p in response_pedidos.json()}
                for formula in formulas:
                    pedido_id = pedidos_dict.get(formula['codigo_orcamento_original'])
                    if pedido_id:
                        response_update = requests.patch(
                            f"{SUPABASE_URL}/rest/v1/prime_formulas?id=eq.{formula['id']}",
                            headers=headers,
                            json={'pedido_id': pedido_id},
                            timeout=10
                        )
                        if response_update.status_code in [200, 204]:
                            count += 1
            
            offset += 1000
            if len(formulas) < 1000:
                break
        
        total_atualizados += count
        if count > 0:
            logger.info(f"      ✅ {count} fórmulas atualizadas")
        
        # 3. Atualizar formulas_itens.formula_id e pedido_id (após sincronizar formulas)
        logger.info("   3️⃣ Atualizando formulas_itens.formula_id e pedido_id...")
        offset = 0
        count = 0
        while True:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
                headers=headers,
                params={
                    'select': 'id,codigo_atendimento_original,numero_formula',
                    'or': '(formula_id.is.null,pedido_id.is.null)',
                    'limit': 1000,
                    'offset': offset
                },
                timeout=30
            )
            if response.status_code != 200:
                break
            itens = response.json()
            if not itens:
                break
            
            # Buscar fórmulas e pedidos
            chaves_formula = [(item['codigo_atendimento_original'], item['numero_formula']) for item in itens]
            codigos_pedido = list(set([item['codigo_atendimento_original'] for item in itens]))
            
            # Cache de fórmulas
            cache_formulas = {}
            for chave in chaves_formula:
                response_formula = requests.get(
                    f"{SUPABASE_URL}/rest/v1/prime_formulas",
                    headers=headers,
                    params={
                        'select': 'id,pedido_id,codigo_orcamento_original,numero_formula',
                        'codigo_orcamento_original': f'eq.{chave[0]}',
                        'numero_formula': f'eq.{chave[1]}'
                    },
                    timeout=10
                )
                if response_formula.status_code == 200:
                    formulas_list = response_formula.json()
                    if formulas_list:
                        cache_formulas[chave] = formulas_list[0]
            
            # Cache de pedidos
            response_pedidos = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'codigo_orcamento_original': f'in.({",".join(map(str, codigos_pedido))})'
                },
                timeout=30
            )
            cache_pedidos = {}
            if response_pedidos.status_code == 200:
                cache_pedidos = {p['codigo_orcamento_original']: p['id'] for p in response_pedidos.json()}
            
            # Atualizar itens
            for item in itens:
                chave = (item['codigo_atendimento_original'], item['numero_formula'])
                formula_info = cache_formulas.get(chave)
                pedido_id = cache_pedidos.get(item['codigo_atendimento_original'])
                
                update_data = {}
                if not item.get('formula_id') and formula_info:
                    update_data['formula_id'] = formula_info['id']
                if not item.get('pedido_id') and pedido_id:
                    update_data['pedido_id'] = pedido_id
                
                if update_data:
                    response_update = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/prime_formulas_itens?id=eq.{item['id']}",
                        headers=headers,
                        json=update_data,
                        timeout=10
                    )
                    if response_update.status_code in [200, 204]:
                        count += 1
            
            offset += 1000
            if len(itens) < 1000:
                break
        
        total_atualizados += count
        if count > 0:
            logger.info(f"      ✅ {count} itens atualizados")
        
        # 4. Atualizar rastreabilidade.pedido_id e tipo_processo_id (após sincronizar tudo)
        logger.info("   4️⃣ Atualizando rastreabilidade.pedido_id e tipo_processo_id...")
        offset = 0
        count = 0
        while True:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade",
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original,codigo_tipo_original',
                    'or': '(pedido_id.is.null,tipo_processo_id.is.null)',
                    'limit': 1000,
                    'offset': offset
                },
                timeout=30
            )
            if response.status_code != 200:
                break
            rastreabilidade = response.json()
            if not rastreabilidade:
                break
            
            codigos_pedido = list(set([r['codigo_orcamento_original'] for r in rastreabilidade]))
            codigos_tipo = list(set([r['codigo_tipo_original'] for r in rastreabilidade]))
            
            # Cache de pedidos
            response_pedidos = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'codigo_orcamento_original': f'in.({",".join(map(str, codigos_pedido))})'
                },
                timeout=30
            )
            cache_pedidos = {}
            if response_pedidos.status_code == 200:
                cache_pedidos = {p['codigo_orcamento_original']: p['id'] for p in response_pedidos.json()}
            
            # Cache de tipos
            response_tipos = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_tipos_processo",
                headers=headers,
                params={
                    'select': 'id,codigo_tipo_original',
                    'codigo_tipo_original': f'in.({",".join(map(str, codigos_tipo))})'
                },
                timeout=30
            )
            cache_tipos = {}
            if response_tipos.status_code == 200:
                cache_tipos = {t['codigo_tipo_original']: t['id'] for t in response_tipos.json()}
            
            # Atualizar rastreabilidade
            for rastro in rastreabilidade:
                update_data = {}
                if not rastro.get('pedido_id'):
                    pedido_id = cache_pedidos.get(rastro['codigo_orcamento_original'])
                    if pedido_id:
                        update_data['pedido_id'] = pedido_id
                if not rastro.get('tipo_processo_id'):
                    tipo_id = cache_tipos.get(rastro['codigo_tipo_original'])
                    if tipo_id:
                        update_data['tipo_processo_id'] = tipo_id
                
                if update_data:
                    response_update = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade?id=eq.{rastro['id']}",
                        headers=headers,
                        json=update_data,
                        timeout=10
                    )
                    if response_update.status_code in [200, 204]:
                        count += 1
            
            offset += 1000
            if len(rastreabilidade) < 1000:
                break
        
        total_atualizados += count
        if count > 0:
            logger.info(f"      ✅ {count} registros de rastreabilidade atualizados")
        
        if total_atualizados > 0:
            logger.info(f"\n   ✅ Total de FK atualizadas: {total_atualizados}")
        else:
            logger.info(f"\n   ℹ️ Nenhuma FK precisou ser atualizada (todas já preenchidas)")
        
        return total_atualizados
    
    except Exception as e:
        logger.warning(f"   ⚠️ Erro ao atualizar FK automaticamente: {e}")
        return 0

def sync_completo_com_gaps():
    """Sincronização completa que verifica gaps e preenche, respeitando ordem de dependências"""
    logger.info("="*70)
    logger.info("🚀 SINCRONIZAÇÃO COMPLETA COM GAP FILLING V2.2.6 - FK AUTOMÁTICO - PROCESSAMENTO 100%")
    logger.info("="*70)
    
    inicio = datetime.now()
    total_inseridos = 0
    
    # ORDEM DE SINCRONIZAÇÃO (respeitando dependências):
    # 1. TIPOS_PROCESSO (independente)
    # 2. CLIENTES (independente)
    # 3. PEDIDOS (depende de CLIENTES)
    # 4. FORMULAS (depende de PEDIDOS)
    # 5. FORMULAS_ITENS (depende de FORMULAS e PEDIDOS)
    # 6. RASTREABILIDADE (depende de PEDIDOS e TIPOS_PROCESSO)
    
    resultados = {}
    
    try:
        # 1. TIPOS_PROCESSO (independente - primeiro)
        logger.info("\n" + "="*70)
        logger.info("1️⃣ SINCRONIZANDO TIPOS DE PROCESSO (independente)")
        logger.info("="*70)
        result_tipos = sync_tipos_processo_novos()
        resultados['tipos_processo'] = result_tipos
        total_inseridos += result_tipos.get('inseridos', 0)
        logger.info(f"✅ Tipos Processo: {result_tipos}")
        
        # 2. CLIENTES (independente - pode rodar junto com tipos)
        logger.info("\n" + "="*70)
        logger.info("2️⃣ SINCRONIZANDO CLIENTES (independente)")
        logger.info("="*70)
        result_clientes = sync_clientes_novos()
        resultados['clientes'] = result_clientes
        total_inseridos += result_clientes.get('inseridos', 0)
        logger.info(f"✅ Clientes: {result_clientes}")
        
        # Atualizar FK após sincronizar clientes
        atualizar_fk_automaticamente()
        
        # 3. PEDIDOS (depende de CLIENTES - depois de clientes)
        logger.info("\n" + "="*70)
        logger.info("3️⃣ SINCRONIZANDO PEDIDOS (depende de CLIENTES)")
        logger.info("="*70)
        result_pedidos = sync_pedidos_novos()
        resultados['pedidos'] = result_pedidos
        total_inseridos += result_pedidos.get('inseridos', 0)
        logger.info(f"✅ Pedidos: {result_pedidos}")
        
        # Atualizar FK após sincronizar pedidos
        atualizar_fk_automaticamente()
        
        # 4. FORMULAS (depende de PEDIDOS - depois de pedidos)
        logger.info("\n" + "="*70)
        logger.info("4️⃣ SINCRONIZANDO FÓRMULAS (depende de PEDIDOS)")
        logger.info("="*70)
        result_formulas = sync_formulas_novas()
        resultados['formulas'] = result_formulas
        total_inseridos += result_formulas.get('inseridos', 0)
        logger.info(f"✅ Fórmulas: {result_formulas}")
        
        # Atualizar FK após sincronizar fórmulas
        atualizar_fk_automaticamente()
        
        # 5. FORMULAS_ITENS (depende de FORMULAS e PEDIDOS - depois de formulas)
        logger.info("\n" + "="*70)
        logger.info("5️⃣ SINCRONIZANDO FORMULAS ITENS (depende de FORMULAS)")
        logger.info("="*70)
        result_itens = sync_formulas_itens_novos()
        resultados['formulas_itens'] = result_itens
        total_inseridos += result_itens.get('inseridos', 0)
        logger.info(f"✅ Itens: {result_itens}")
        
        # 6. RASTREABILIDADE (depende de PEDIDOS e TIPOS_PROCESSO - depois de pedidos e tipos)
        logger.info("\n" + "="*70)
        logger.info("6️⃣ SINCRONIZANDO RASTREABILIDADE (depende de PEDIDOS e TIPOS_PROCESSO)")
        logger.info("="*70)
        result_rastreabilidade = sync_rastreabilidade_nova()
        resultados['rastreabilidade'] = result_rastreabilidade
        total_inseridos += result_rastreabilidade.get('inseridos', 0)
        logger.info(f"✅ Rastreabilidade: {result_rastreabilidade}")
        
        # Atualizar FK final (após sincronizar tudo)
        fk_atualizadas = atualizar_fk_automaticamente()
        resultados['fk_atualizadas'] = fk_atualizadas
        
        tempo_total = (datetime.now() - inicio).total_seconds()
        
        logger.info("\n" + "="*70)
        logger.info(f"✅ SINCRONIZAÇÃO COMPLETA CONCLUÍDA!")
        logger.info(f"   Total inseridos: {total_inseridos}")
        logger.info(f"   Tempo: {tempo_total:.1f}s")
        logger.info("="*70)
        
        return {
            'sucesso': True,
            'timestamp': datetime.now().isoformat(),
            'tempo_execucao_segundos': tempo_total,
            'version': '2.2.6',
            'resultados': resultados,
            'total_inseridos': total_inseridos
        }
    
    except Exception as e:
        logger.error(f"❌ Erro na sincronização completa: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'sucesso': False,
            'erro': str(e),
            'timestamp': datetime.now().isoformat(),
            'resultados_parciais': resultados
        }

@app.route('/sync', methods=['GET', 'POST'])
def sync():
    """Endpoint principal de sincronização - VERSÃO COMPLETA COM GAP FILLING"""
    try:
        resultado = sync_completo_com_gaps()
        
        if resultado.get('sucesso'):
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 500

    except Exception as e:
        logger.error(f"❌ Erro no endpoint /sync: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'sucesso': False,
            'erro': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
