#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask para Sincronização Incremental Firebird -> Supabase
Endpoint: /sync (POST ou GET)
Versão: 2.0.1 - Melhorias no tratamento de erros e logging
"""

from flask import Flask, jsonify, request
import fdb
import requests
import os
from datetime import datetime
import logging
import time
import re
from threading import Lock, Thread
from auditoria import iniciar_auditoria, finalizar_auditoria, verificar_integridade, listar_ultimas_sincronizacoes

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

# Estado global da sincronização (controlado pelo endpoint /sync)
sync_lock = Lock()
sync_state = {
    'running': False,
    'started_at': None,
    'finished_at': None,
    'last_duration_seconds': None,
    'last_error': None,
    'last_result': None,
    'trigger': None
}


def _atualizar_estado_sync(**kwargs):
    """Atualiza o dicionário de estado da sincronização com lock."""
    with sync_lock:
        sync_state.update(kwargs)

def limpar_string(texto):
    """Limpa strings removendo caracteres inválidos"""
    if not texto:
        return None
    return str(texto).replace('\x00', '').replace('\u0000', '').strip() or None

def sanitizar_data(data):
    """Sanitiza e valida datas - converte datas inválidas para None"""
    if not data:
        return None
    
    # Se já é string ISO, validar formato
    if isinstance(data, str):
        # Tentar parsear ISO format
        try:
            datetime.fromisoformat(data.replace('Z', '+00:00'))
            return data
        except:
            pass
        
        # Tentar parsear formato brasileiro (DD/MM/YYYY)
        try:
            partes = data.split('/')
            if len(partes) == 3:
                dia, mes, ano = int(partes[0]), int(partes[1]), int(partes[2])
                if 1 <= dia <= 31 and 1 <= mes <= 12 and 1900 <= ano <= 2100:
                    return f"{ano}-{mes:02d}-{dia:02d}"
        except:
            pass
        
        # Se não conseguiu parsear, retornar None
        return None
    
    # Se é datetime object, converter para ISO
    if isinstance(data, datetime):
        try:
            return data.isoformat()
        except:
            return None
    
    # Se é date object, converter para ISO
    if hasattr(data, 'isoformat'):
        try:
            return data.isoformat()
        except:
            return None
    
    return None

def sanitizar_string(texto, max_length=None):
    """Sanitiza strings - remove caracteres inválidos e trunca se necessário"""
    if not texto:
        return None
    
    # Converter para string
    texto = str(texto)
    
    # Remover caracteres nulos e inválidos
    texto = texto.replace('\x00', '').replace('\u0000', '').replace('\r\n', ' ').replace('\n', ' ')
    
    # Remover caracteres de controle (exceto espaços e tabs)
    texto = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', texto)
    
    # Limpar espaços extras
    texto = texto.strip()
    
    # Truncar se necessário
    if max_length and len(texto) > max_length:
        texto = texto[:max_length]
        logger.debug(f"   ⚠️  String truncada para {max_length} caracteres")
    
    return texto if texto else None

def sanitizar_cpf_cnpj(cpf_cnpj):
    """Sanitiza CPF/CNPJ - remove caracteres não numéricos"""
    if not cpf_cnpj:
        return None
    
    # Remover caracteres não numéricos
    cpf_cnpj = re.sub(r'[^0-9]', '', str(cpf_cnpj))
    
    # Validar tamanho (CPF: 11, CNPJ: 14)
    if len(cpf_cnpj) not in [11, 14]:
        logger.debug(f"   ⚠️  CPF/CNPJ inválido (tamanho {len(cpf_cnpj)}): {cpf_cnpj[:10]}...")
        return None
    
    return cpf_cnpj

def sanitizar_cep(cep):
    """Sanitiza CEP - remove caracteres não numéricos"""
    if not cep:
        return None
    
    # Remover caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', str(cep))
    
    # Validar tamanho (CEP: 8 dígitos)
    if len(cep) != 8:
        logger.debug(f"   ⚠️  CEP inválido (tamanho {len(cep)}): {cep}")
        return None
    
    return cep

def inserir_com_retry(url, headers, json_data, max_tentativas=3, timeout=60):
    """Insere dados no Supabase com retry e backoff exponencial"""
    for tentativa in range(max_tentativas):
        try:
            response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            
            # Sucesso
            if response.status_code in [200, 201]:
                return response
            
            # Rate limiting - aguardar e tentar novamente
            if response.status_code == 429:
                wait_time = 2 ** tentativa  # Backoff exponencial: 1s, 2s, 4s
                logger.warning(f"   ⚠️  Rate limiting (429) - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
                time.sleep(wait_time)
                continue
            
            # Erro de servidor (5xx) - tentar novamente
            if 500 <= response.status_code < 600:
                wait_time = 2 ** tentativa
                logger.warning(f"   ⚠️  Erro de servidor ({response.status_code}) - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
                time.sleep(wait_time)
                continue
            
            # Outros erros (4xx) - não tentar novamente
            logger.error(f"   ❌ Erro HTTP {response.status_code}: {response.text[:200]}")
            return response
            
        except requests.exceptions.Timeout:
            wait_time = 2 ** tentativa
            logger.warning(f"   ⚠️  Timeout - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
            if tentativa < max_tentativas - 1:
                time.sleep(wait_time)
                continue
            raise
            
        except requests.exceptions.ConnectionError:
            wait_time = 2 ** tentativa
            logger.warning(f"   ⚠️  Erro de conexão - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
            if tentativa < max_tentativas - 1:
                time.sleep(wait_time)
                continue
            raise
            
        except Exception as e:
            if tentativa == max_tentativas - 1:
                logger.error(f"   ❌ Erro após {max_tentativas} tentativas: {e}")
                raise
            wait_time = 2 ** tentativa
            logger.warning(f"   ⚠️  Erro inesperado - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas}): {e}")
            time.sleep(wait_time)
            continue
    
    # Se chegou aqui, todas as tentativas falharam
    raise Exception(f"Falha após {max_tentativas} tentativas")

def buscar_com_retry(url, headers, params=None, max_tentativas=3, timeout=30):
    """Busca dados do Supabase com retry e backoff exponencial"""
    for tentativa in range(max_tentativas):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            
            # Sucesso
            if response.status_code == 200:
                return response
            
            # Rate limiting - aguardar e tentar novamente
            if response.status_code == 429:
                wait_time = 2 ** tentativa
                logger.warning(f"   ⚠️  Rate limiting (429) - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
                time.sleep(wait_time)
                continue
            
            # Erro de servidor (5xx) - tentar novamente
            if 500 <= response.status_code < 600:
                wait_time = 2 ** tentativa
                logger.warning(f"   ⚠️  Erro de servidor ({response.status_code}) - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
                time.sleep(wait_time)
                continue
            
            # Outros erros (4xx) - não tentar novamente
            logger.error(f"   ❌ Erro HTTP {response.status_code}: {response.text[:200]}")
            return response
            
        except requests.exceptions.Timeout:
            wait_time = 2 ** tentativa
            logger.warning(f"   ⚠️  Timeout - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
            if tentativa < max_tentativas - 1:
                time.sleep(wait_time)
                continue
            raise
            
        except requests.exceptions.ConnectionError:
            wait_time = 2 ** tentativa
            logger.warning(f"   ⚠️  Erro de conexão - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas})")
            if tentativa < max_tentativas - 1:
                time.sleep(wait_time)
                continue
            raise
            
        except Exception as e:
            if tentativa == max_tentativas - 1:
                logger.error(f"   ❌ Erro após {max_tentativas} tentativas: {e}")
                raise
            wait_time = 2 ** tentativa
            logger.warning(f"   ⚠️  Erro inesperado - aguardando {wait_time}s antes de tentar novamente (tentativa {tentativa + 1}/{max_tentativas}): {e}")
            time.sleep(wait_time)
            continue
    
    # Se chegou aqui, todas as tentativas falharam
    raise Exception(f"Falha após {max_tentativas} tentativas")

def verificar_integridade_referencial_firebird(cursor, tipo, codigos):
    """Verifica integridade referencial no Firebird antes de inserir"""
    try:
        if tipo == 'pedidos':
            # Verificar se todos os pedidos têm clientes válidos
            codigos_str = ','.join(map(str, codigos))
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM ATENDIMENTO_A1 A
                WHERE A.CODIGO IN ({codigos_str})
                AND A.CODIGO_CLIENTE IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM CLIENTE C
                    WHERE C.CODIGO = A.CODIGO_CLIENTE
                    AND C.ATIVO = -1
                )
            """)
            validos = cursor.fetchone()[0]
            return validos == len(codigos)
        
        elif tipo == 'formulas':
            # Verificar se todas as fórmulas têm pedidos válidos
            codigos_str = ','.join(map(str, codigos))
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM ATENDIMENTO_A2 A2
                WHERE A2.CODIGO_ATEND_A1 IN ({codigos_str})
                AND EXISTS (
                    SELECT 1 FROM ATENDIMENTO_A1 A1
                    WHERE A1.CODIGO = A2.CODIGO_ATEND_A1
                    AND A1.CODIGO_CLIENTE IS NOT NULL
                )
            """)
            validos = cursor.fetchone()[0]
            return validos == len(codigos)
        
        elif tipo == 'rastreabilidade':
            # Verificar se todos os registros têm pedidos e tipos válidos
            codigos_str = ','.join(map(str, codigos))
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM PROCESSO_MANIPULACAO PM
                WHERE PM.CODIGO IN ({codigos_str})
                AND PM.CODIGO_MOV IS NOT NULL
                AND PM.CODIGO_PROCESSO_TIPO IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM ATENDIMENTO_A1 A1
                    WHERE A1.CODIGO = PM.CODIGO_MOV
                )
                AND EXISTS (
                    SELECT 1 FROM FORMAFARMACEUTICA_PROCESSO_TIPO FPT
                    WHERE FPT.CODIGO = PM.CODIGO_PROCESSO_TIPO
                    AND FPT.ATIVO = -1
                )
            """)
            validos = cursor.fetchone()[0]
            return validos == len(codigos)
        
        return True  # Para outros tipos, assumir válido
        
    except Exception as e:
        logger.warning(f"   ⚠️  Erro ao verificar integridade referencial ({tipo}): {e}")
        return True  # Em caso de erro, assumir válido para não bloquear sincronização

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

def conectar_firebird():
    """Conecta ao Firebird"""
    return fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )


def contar_supabase_registros(tabela_supabase):
    """Retorna a contagem total de registros em uma tabela do Supabase."""
    headers_count = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Accept-Profile': 'api',
        'Prefer': 'count=exact'
    }
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{tabela_supabase}",
        headers=headers_count,
        params={'select': 'id', 'limit': 0},
        timeout=30
    )
    if resp.status_code != 200:
        raise Exception(f"Falha ao contar registros em {tabela_supabase}: {resp.status_code} - {resp.text[:200]}")
    content_range = resp.headers.get('Content-Range', '0/0')
    try:
        total = int(content_range.split('/')[-1])
    except (ValueError, IndexError):
        total = 0
    return total

def sync_clientes_novos():
    """Sincroniza TODOS os clientes novos (SEM limitação)
    
    🚨 IMPORTANTE: Busca dados de 3 tabelas:
    1. CLIENTE (dados básicos)
    2. CADASTRO_TELEFONE (telefones - WHERE TIPO_CADASTRO = 1)
    3. CADASTRO_ENDERECO (endereços - WHERE TIPO_CADASTRO = 1)
    
    Processa em lotes de 1000 para evitar timeout
    """
    try:
        ultimo_codigo = get_ultimo_id_supabase('prime_clientes', 'codigo_cliente_original')
        logger.info(f"📊 Clientes - Último código no Supabase: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        
        # Processar em lotes de 1000 (sem limitação total)
        batch_size = 1000
        total_inseridos = 0
        offset_codigo = ultimo_codigo
        
        while True:
            logger.info(f"   🔄 Processando lote: códigos > {offset_codigo} (máximo {batch_size} por vez)")
            
            # 1. Buscar clientes básicos (lote)
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
                AND C.CODIGO > {offset_codigo}
                AND C.CODIGO < 500000
                ORDER BY C.CODIGO
                ROWS {batch_size}
            """)

            novos_clientes = cursor.fetchall()
            
            if not novos_clientes:
                logger.info(f"   ✅ Nenhum cliente novo encontrado (lote completo)")
                break
            
            logger.info(f"   📦 Lote atual: {len(novos_clientes)} clientes encontrados")

            # Atualizar offset para próximo lote
            offset_codigo = novos_clientes[-1][0]  # Último código do lote atual
            logger.info(f"   📊 Último código do lote: {offset_codigo}")
            
            # 2. Buscar telefones desses clientes (tabela CADASTRO_TELEFONE)
            codigos = [row[0] for row in novos_clientes]
            codigos_str = ','.join(map(str, codigos))
            
            try:
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
            except Exception as e:
                logger.error(f"❌ Erro ao buscar telefones (lote {offset_codigo}): {e}", exc_info=True)
                telefones_dict = {}
            
            # 3. Buscar endereços desses clientes (tabela CADASTRO_ENDERECO)
            try:
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
            except Exception as e:
                logger.error(f"❌ Erro ao buscar endereços (lote {offset_codigo}): {e}", exc_info=True)
                enderecos_dict = {}
            
            # 4. Buscar totalizadores de pedidos (para calcular total_orcamentos, etc)
            try:
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
            except Exception as e:
                logger.error(f"❌ Erro ao buscar totalizadores (lote {offset_codigo}): {e}", exc_info=True)
                totalizadores_dict = {}

            # 5. Preparar dados combinando as 3 fontes
            clientes_dados = []
            for row in novos_clientes:
                codigo_cliente = row[0]
                
                # Formatar data de nascimento
                data_nasc = None
                if row[3] and row[4] and row[5]:  # DIANASCIMENTO, MESNASCIMENTO, ANONASCIMENTO
                    try:
                        data_nasc = f"{int(row[5])}-{int(row[4]):02d}-{int(row[3]):02d}"
                    except Exception as e:
                        logger.debug(f"   ⚠️  Erro ao formatar data nascimento cliente {codigo_cliente}: {e}")

                # Buscar telefone da tabela CADASTRO_TELEFONE
                telefone = telefones_dict.get(codigo_cliente)
                
                # Buscar endereço da tabela CADASTRO_ENDERECO
                endereco = enderecos_dict.get(codigo_cliente, {})
                
                # Buscar totalizadores
                totalizadores = totalizadores_dict.get(codigo_cliente, {})

                # Montar cliente com TODOS os campos (mesmo que None)
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

            # 6. Inserir lote no Supabase
            if clientes_dados:
                try:
                    url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
                    # Usar retry com backoff exponencial
                    response = inserir_com_retry(url, headers, clientes_dados, max_tentativas=3, timeout=60)
                    
                    if response.status_code in [200, 201]:
                        lote_inseridos = len(clientes_dados)
                        total_inseridos += lote_inseridos
                        logger.info(f"   ✅ Lote inserido: {lote_inseridos} clientes (Total: {total_inseridos})")
                    else:
                        logger.error(f"❌ Erro ao inserir lote de clientes: {response.status_code}")
                        logger.error(f"   Resposta: {response.text[:500]}")
                        logger.error(f"   Códigos do lote: {codigos[:10]}...")
                        # Continuar mesmo com erro neste lote
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir lote de clientes (lote {offset_codigo}): {e}", exc_info=True)
                    # Continuar mesmo com erro neste lote
        
        conn.close()
        
        if total_inseridos > 0:
            logger.info(f"✅ TOTAL: {total_inseridos} clientes sincronizados (processados em lotes)")
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} clientes sincronizados'
            }
        else:
            return {'inseridos': 0, 'mensagem': 'Nenhum cliente novo sincronizado'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_clientes_novos: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

def sync_pedidos_novos():
    """Sincroniza TODOS os pedidos novos (SEM limitação - processa em lotes)"""
    try:
        ultimo_codigo = get_ultimo_id_supabase('prime_pedidos', 'codigo_orcamento_original')
        logger.info(f"📊 Pedidos - Último código no Supabase: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        
        # Processar em lotes de 2000 (sem limitação total)
        batch_size = 2000
        total_inseridos = 0
        offset_codigo = ultimo_codigo
        
        while True:
            logger.info(f"   🔄 Processando lote de pedidos: códigos > {offset_codigo} (máximo {batch_size} por vez)")
            
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
                AND A.CODIGO > {offset_codigo}
                ORDER BY A.CODIGO
                ROWS {batch_size}
            """)

            novos_pedidos = cursor.fetchall()
            
            if not novos_pedidos:
                logger.info(f"   ✅ Nenhum pedido novo encontrado (lote completo)")
                break
            
            logger.info(f"   📦 Lote atual: {len(novos_pedidos)} pedidos encontrados")
            
            # Atualizar offset para próximo lote
            offset_codigo = novos_pedidos[-1][0]
            logger.info(f"   📊 Último código do lote: {offset_codigo}")

                # Buscar clientes em lote (com retry)
            try:
                codigos_cliente = list(set([row[1] for row in novos_pedidos]))
                url_clientes = f"{SUPABASE_URL}/rest/v1/prime_clientes"
                response = buscar_com_retry(
                    url_clientes,
                    headers,
                    params={
                        'select': 'id,codigo_cliente_original',
                        'codigo_cliente_original': f'in.({",".join(map(str, codigos_cliente))})'
                    },
                    max_tentativas=3,
                    timeout=30
                )

                cache_clientes = {}
                if response.status_code == 200:
                    for cli in response.json():
                        cache_clientes[cli['codigo_cliente_original']] = cli['id']
                else:
                    logger.error(f"❌ Erro ao buscar clientes: {response.status_code} - {response.text[:200]}")
                    cache_clientes = {}
            except Exception as e:
                logger.error(f"❌ Erro ao buscar clientes (lote {offset_codigo}): {e}", exc_info=True)
                cache_clientes = {}

            pedidos_dados = []
            pedidos_sem_cliente = []
            for row in novos_pedidos:
                codigo_orcamento, codigo_cliente, cadastro_dt, aviada_dt, entregue_dt, valor_venda, observacao = row

                cliente_id = cache_clientes.get(codigo_cliente)
                if not cliente_id:
                    pedidos_sem_cliente.append(codigo_orcamento)
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

            if pedidos_sem_cliente:
                logger.warning(f"   ⚠️  {len(pedidos_sem_cliente)} pedidos sem cliente no Supabase (pulados): {pedidos_sem_cliente[:10]}{'...' if len(pedidos_sem_cliente) > 10 else ''}")

            # Inserir lote no Supabase
            if pedidos_dados:
                try:
                    url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
                    # Usar retry com backoff exponencial
                    response = inserir_com_retry(url, headers, pedidos_dados, max_tentativas=3, timeout=60)
                    
                    if response.status_code in [200, 201]:
                        lote_inseridos = len(pedidos_dados)
                        total_inseridos += lote_inseridos
                        logger.info(f"   ✅ Lote inserido: {lote_inseridos} pedidos (Total: {total_inseridos})")
                        if pedidos_sem_cliente:
                            logger.warning(f"   ⚠️  {len(pedidos_sem_cliente)} pedidos NÃO inseridos neste lote (sem cliente)")
                    else:
                        logger.error(f"❌ Erro ao inserir lote de pedidos: {response.status_code}")
                        logger.error(f"   Resposta: {response.text[:500]}")
                        logger.error(f"   Códigos do lote: {[row[0] for row in novos_pedidos[:10]]}...")
                        # Continuar mesmo com erro neste lote
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir lote de pedidos (lote {offset_codigo}): {e}", exc_info=True)
                    # Continuar mesmo com erro neste lote
        
        conn.close()
        
        if total_inseridos > 0:
            logger.info(f"✅ TOTAL: {total_inseridos} pedidos sincronizados (processados em lotes)")
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} pedidos sincronizados'
            }
        else:
            return {'inseridos': 0, 'mensagem': 'Nenhum pedido novo sincronizado'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_pedidos_novos: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

def sync_formulas_novas():
    """Sincroniza TODAS as fórmulas novas (SEM limitação - processa em lotes)"""
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

        logger.info(f"📊 Fórmulas - Último código atendimento no Supabase: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        
        # Processar em lotes de 2000 (sem limitação total)
        batch_size = 2000
        total_inseridos = 0
        offset_codigo = ultimo_codigo
        
        while True:
            logger.info(f"   🔄 Processando lote de fórmulas: códigos > {offset_codigo} (máximo {batch_size} por vez)")
            
            cursor.execute(f"""
                SELECT
                    A2.CODIGO_ATEND_A1,
                    A2.NUMEROFORMULA,
                    A2.TEXTOROTULO,
                    A2.POSOLOGIA,
                    A2.VALORFORMULA_VENDA
                FROM ATENDIMENTO_A2 A2
                WHERE A2.CODIGO_ATEND_A1 > {offset_codigo}
                AND A2.CODIGO_ATEND_A1 IS NOT NULL
                ORDER BY A2.CODIGO_ATEND_A1, A2.NUMEROFORMULA
                ROWS {batch_size}
            """)

            novas_formulas = cursor.fetchall()
            
            if not novas_formulas:
                logger.info(f"   ✅ Nenhuma fórmula nova encontrada (lote completo)")
                break
            
            logger.info(f"   📦 Lote atual: {len(novas_formulas)} fórmulas encontradas")
            
            # Atualizar offset para próximo lote
            offset_codigo = novas_formulas[-1][0]  # Último CODIGO_ATEND_A1 do lote
            logger.info(f"   📊 Último código do lote: {offset_codigo}")

            # Buscar pedidos em lote
            try:
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
                else:
                    logger.error(f"❌ Erro ao buscar pedidos: {response.status_code} - {response.text[:200]}")
                    cache_pedidos = {}
            except Exception as e:
                logger.error(f"❌ Erro ao buscar pedidos (lote {offset_codigo}): {e}", exc_info=True)
                cache_pedidos = {}

            formulas_dados = []
            formulas_sem_pedido = []
            for row in novas_formulas:
                codigo_atend, num_formula, texto_rotulo, posologia, valor = row

                pedido_id = cache_pedidos.get(codigo_atend)
                if not pedido_id:
                    formulas_sem_pedido.append(codigo_atend)
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

            if formulas_sem_pedido:
                logger.warning(f"   ⚠️  {len(set(formulas_sem_pedido))} pedidos não encontrados no Supabase (fórmulas puladas): {list(set(formulas_sem_pedido))[:10]}{'...' if len(set(formulas_sem_pedido)) > 10 else ''}")

            # Inserir lote no Supabase
            if formulas_dados:
                try:
                    url = f"{SUPABASE_URL}/rest/v1/prime_formulas"
                    # Usar retry com backoff exponencial
                    response = inserir_com_retry(url, headers, formulas_dados, max_tentativas=3, timeout=60)
                    
                    if response.status_code in [200, 201]:
                        lote_inseridos = len(formulas_dados)
                        total_inseridos += lote_inseridos
                        logger.info(f"   ✅ Lote inserido: {lote_inseridos} fórmulas (Total: {total_inseridos})")
                        if formulas_sem_pedido:
                            logger.warning(f"   ⚠️  {len(set(formulas_sem_pedido))} fórmulas NÃO inseridas neste lote (sem pedido)")
                    else:
                        logger.error(f"❌ Erro ao inserir lote de fórmulas: {response.status_code}")
                        logger.error(f"   Resposta: {response.text[:500]}")
                        logger.error(f"   Códigos do lote: {codigos_orcamento[:10]}...")
                        # Continuar mesmo com erro neste lote
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir lote de fórmulas (lote {offset_codigo}): {e}", exc_info=True)
                    # Continuar mesmo com erro neste lote
        
        conn.close()
        
        if total_inseridos > 0:
            logger.info(f"✅ TOTAL: {total_inseridos} fórmulas sincronizadas (processadas em lotes)")
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} fórmulas sincronizadas'
            }
        else:
            return {'inseridos': 0, 'mensagem': 'Nenhuma fórmula nova sincronizada'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_formulas_novas: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

def sync_formulas_itens_novos():
    """Sincroniza itens das fórmulas (ATENDIMENTO_A3) - NOVA FUNCIONALIDADE"""
    try:
        # Buscar último código de item
        url_itens = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
        response = requests.get(
            url_itens,
            headers=headers,
            params={
                'select': 'id',
                'order': 'id.desc',
                'limit': 1
            },
            timeout=10
        )

        ultimo_id_supabase = 0
        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_id_supabase = dados[0]['id']

        logger.info(f"📊 Fórmulas Itens - Último ID Supabase: {ultimo_id_supabase}")

        # Buscar também o último codigo_atendimento para sincronização incremental
        response2 = requests.get(
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
        if response2.status_code == 200:
            dados2 = response2.json()
            if dados2:
                ultimo_codigo = dados2[0]['codigo_atendimento_original']
        
        logger.info(f"📊 Fórmulas Itens - Último código atendimento: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        # Processar em lotes de 2000 (sem limitação total)
        batch_size = 2000
        total_inseridos = 0
        offset_codigo = ultimo_codigo
        
        while True:
            logger.info(f"   🔄 Processando lote de itens: códigos > {offset_codigo} (máximo {batch_size} por vez)")
            
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
                WHERE A3.CODIGO_ATEND_A1 > {offset_codigo}
                AND A3.CODIGO_ATEND_A1 IS NOT NULL
                ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
                ROWS {batch_size}
            """)

            novos_itens = cursor.fetchall()
            
            if not novos_itens:
                logger.info(f"   ✅ Nenhum item novo encontrado (lote completo)")
                break
            
            logger.info(f"   📦 Lote atual: {len(novos_itens)} itens encontrados")
            
            # Atualizar offset para próximo lote
            offset_codigo = novos_itens[-1][0]  # Último CODIGO_ATEND_A1 do lote
            logger.info(f"   📊 Último código do lote: {offset_codigo}")

            # Montar cache COMPLETO de fórmulas com paginação (sem limitação)
            logger.info("      Montando cache de fórmulas...")
            cache_formulas = {}
            offset = 0
            while True:  # Sem limitação - processa TODAS as fórmulas
                try:
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
                        if len(dados) < 1000:
                            break
                    else:
                        logger.error(f"❌ Erro ao buscar fórmulas (offset {offset}): {response.status_code}")
                        break
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar fórmulas (offset {offset}): {e}", exc_info=True)
                    break
            
            logger.info(f"      Cache fórmulas: {len(cache_formulas)} carregadas")

            itens_dados = []
            itens_sem_formula = []
            for row in novos_itens:
                (codigo_atend, num_formula, num_linha, codigo_produto, nome_produto,
                 quantidade, unidade, valor_custo, valor_venda, observacao) = row

                chave = (codigo_atend, num_formula)
                formula_info = cache_formulas.get(chave)

                if not formula_info:
                    itens_sem_formula.append(chave)
                    continue

                item = {
                    'formula_id': formula_info['id'],
                    'pedido_id': formula_info['pedido_id'],
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
                logger.warning(f"      ⚠️  {len(set(itens_sem_formula))} itens sem fórmula no Supabase (pulados)")

            # Inserir lote no Supabase
            if itens_dados:
                try:
                    headers_insert = headers.copy()
                    headers_insert['Prefer'] = 'resolution=ignore-duplicates'
                    
                    url = f"{SUPABASE_URL}/rest/v1/prime_formulas_itens"
                    # Usar retry com backoff exponencial
                    response = inserir_com_retry(url, headers_insert, itens_dados, max_tentativas=3, timeout=60)
                    
                    if response.status_code in [200, 201]:
                        lote_inseridos = len(itens_dados)
                        total_inseridos += lote_inseridos
                        logger.info(f"      ✅ Lote inserido: {lote_inseridos} itens (Total: {total_inseridos})")
                        if itens_sem_formula:
                            logger.warning(f"      ⚠️  {len(set(itens_sem_formula))} itens NÃO inseridos neste lote (sem fórmula)")
                    else:
                        logger.error(f"❌ Erro ao inserir lote de itens: {response.status_code}")
                        logger.error(f"   Resposta: {response.text[:500]}")
                        # Continuar mesmo com erro neste lote
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir lote de itens (lote {offset_codigo}): {e}", exc_info=True)
                    # Continuar mesmo com erro neste lote
        
        conn.close()
        
        if total_inseridos > 0:
            logger.info(f"✅ TOTAL: {total_inseridos} itens sincronizados (processados em lotes)")
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} itens sincronizados'
            }
        else:
            return {'inseridos': 0, 'mensagem': 'Nenhum item novo sincronizado'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_formulas_itens_novos: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

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
                'select': 'codigo_processo_original',
                'order': 'codigo_processo_original.desc',
                'limit': 1
            },
            timeout=10
        )

        ultimo_codigo = 0
        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_codigo = dados[0]['codigo_processo_original']

        logger.info(f"📊 Rastreabilidade - Último código: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        
        # Processar em lotes de 2000 (sem limitação total)
        batch_size = 2000
        total_inseridos = 0
        offset_codigo = ultimo_codigo
        
        while True:
            logger.info(f"   🔄 Processando lote de rastreabilidade: códigos > {offset_codigo} (máximo {batch_size} por vez)")
            
            cursor.execute(f"""
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
                WHERE PM.CODIGO > {offset_codigo}
                ORDER BY PM.CODIGO
                ROWS {batch_size}
            """)

            novos_registros = cursor.fetchall()
            
            if not novos_registros:
                logger.info(f"   ✅ Nenhum registro novo encontrado (lote completo)")
                break
            
            logger.info(f"   📦 Lote atual: {len(novos_registros)} registros encontrados")
            
            # Atualizar offset para próximo lote
            offset_codigo = novos_registros[-1][0]  # Último CODIGO do lote
            logger.info(f"   📊 Último código do lote: {offset_codigo}")

            # Preparar dados com lookup de IDs
            rastreabilidade_dados = []
            pedidos_nao_encontrados = []
            tipos_nao_encontrados = []
            
            # Buscar pedidos e tipos em lote (mais eficiente)
            codigos_orcamento = list(set([row[2] for row in novos_registros if row[2]]))
            codigos_tipo = list(set([row[3] for row in novos_registros if row[3]]))
            
            # Cache de pedidos
            cache_pedidos = {}
            try:
                if codigos_orcamento:
                    url_pedido = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
                    resp_pedido = requests.get(
                        url_pedido,
                        headers=headers,
                        params={
                            'select': 'id,codigo_orcamento_original',
                            'codigo_orcamento_original': f'in.({",".join(map(str, codigos_orcamento))})'
                        },
                        timeout=30
                    )
                    
                    if resp_pedido.status_code == 200:
                        for ped in resp_pedido.json():
                            cache_pedidos[ped['codigo_orcamento_original']] = ped['id']
                    else:
                        logger.error(f"❌ Erro ao buscar pedidos em lote: {resp_pedido.status_code} - {resp_pedido.text[:200]}")
            except Exception as e:
                logger.error(f"❌ Erro ao buscar pedidos em lote (lote {offset_codigo}): {e}", exc_info=True)
            
            # Cache de tipos de processo
            cache_tipos = {}
            try:
                if codigos_tipo:
                    url_tipo = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
                    resp_tipo = requests.get(
                        url_tipo,
                        headers=headers,
                        params={
                            'select': 'id,codigo_tipo_original',
                            'codigo_tipo_original': f'in.({",".join(map(str, codigos_tipo))})'
                        },
                        timeout=30
                    )
                    
                    if resp_tipo.status_code == 200:
                        for tipo in resp_tipo.json():
                            cache_tipos[tipo['codigo_tipo_original']] = tipo['id']
                    else:
                        logger.error(f"❌ Erro ao buscar tipos em lote: {resp_tipo.status_code} - {resp_tipo.text[:200]}")
            except Exception as e:
                logger.error(f"❌ Erro ao buscar tipos em lote (lote {offset_codigo}): {e}", exc_info=True)
            
            # Processar registros do lote
            for row in novos_registros:
                codigo_orcamento = row[2]
                codigo_tipo = row[3]

                pedido_id = cache_pedidos.get(codigo_orcamento)
                if not pedido_id:
                    if codigo_orcamento not in pedidos_nao_encontrados:
                        pedidos_nao_encontrados.append(codigo_orcamento)
                    continue

                tipo_processo_id = cache_tipos.get(codigo_tipo)
                if not tipo_processo_id:
                    if codigo_tipo not in tipos_nao_encontrados:
                        tipos_nao_encontrados.append(codigo_tipo)
                    continue

                rastro = {
                    'codigo_processo_original': row[0],
                    'pedido_id': pedido_id,
                    'codigo_orcamento_original': codigo_orcamento,
                    'tipo_processo_id': tipo_processo_id,
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

            # Logging detalhado sobre pedidos/tipos não encontrados
            if pedidos_nao_encontrados:
                logger.warning(f"   ⚠️  {len(set(pedidos_nao_encontrados))} pedidos NÃO encontrados no Supabase (rastreabilidade pulada)")
                logger.warning(f"      Pedidos: {list(set(pedidos_nao_encontrados))[:10]}{'...' if len(set(pedidos_nao_encontrados)) > 10 else ''}")
            
            if tipos_nao_encontrados:
                logger.warning(f"   ⚠️  {len(set(tipos_nao_encontrados))} tipos de processo NÃO encontrados no Supabase (rastreabilidade pulada)")
                logger.warning(f"      Tipos: {list(set(tipos_nao_encontrados))[:10]}{'...' if len(set(tipos_nao_encontrados)) > 10 else ''}")

            # Inserir lote no Supabase
            if rastreabilidade_dados:
                try:
                    url = f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade"
                    # Usar retry com backoff exponencial
                    response = inserir_com_retry(url, headers, rastreabilidade_dados, max_tentativas=3, timeout=60)
                    
                    if response.status_code in [200, 201]:
                        lote_inseridos = len(rastreabilidade_dados)
                        total_inseridos += lote_inseridos
                        logger.info(f"   ✅ Lote inserido: {lote_inseridos} registros (Total: {total_inseridos})")
                        if pedidos_nao_encontrados or tipos_nao_encontrados:
                            logger.warning(f"   ⚠️  {len(set(pedidos_nao_encontrados))} pedidos + {len(set(tipos_nao_encontrados))} tipos NÃO encontrados neste lote")
                    else:
                        logger.error(f"❌ Erro ao inserir lote de rastreabilidade: {response.status_code}")
                        logger.error(f"   Resposta: {response.text[:500]}")
                        logger.error(f"   Códigos do lote: {[row[0] for row in novos_registros[:10]]}...")
                        # Continuar mesmo com erro neste lote
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir lote de rastreabilidade (lote {offset_codigo}): {e}", exc_info=True)
                    # Continuar mesmo com erro neste lote
        
        conn.close()
        
        if total_inseridos > 0:
            logger.info(f"✅ TOTAL: {total_inseridos} registros de rastreabilidade sincronizados (processados em lotes)")
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} registros sincronizados'
            }
        else:
            return {'inseridos': 0, 'mensagem': 'Nenhum registro novo sincronizado'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_rastreabilidade_nova: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

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
        
        # Processar em lotes de 1000 (sem limitação total)
        batch_size = 1000
        total_inseridos = 0
        offset_codigo = ultimo_codigo
        
        while True:
            logger.info(f"   🔄 Processando lote de tipos: códigos > {offset_codigo} (máximo {batch_size} por vez)")
            
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
                WHERE FPT.CODIGO > {offset_codigo}
                ORDER BY FPT.CODIGO
                ROWS {batch_size}
            """)

            novos_tipos = cursor.fetchall()
            
            if not novos_tipos:
                logger.info(f"   ✅ Nenhum tipo novo encontrado (lote completo)")
                break
            
            logger.info(f"   📦 Lote atual: {len(novos_tipos)} tipos encontrados")
            
            # Atualizar offset para próximo lote
            offset_codigo = novos_tipos[-1][0]  # Último CODIGO do lote
            logger.info(f"   📊 Último código do lote: {offset_codigo}")

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

            # Inserir lote no Supabase
            if tipos_dados:
                try:
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
                        lote_inseridos = len(tipos_dados)
                        total_inseridos += lote_inseridos
                        logger.info(f"   ✅ Lote inserido: {lote_inseridos} tipos (Total: {total_inseridos})")
                    elif response.status_code == 409:
                        # 409 = conflito (registro já existe) - isso é OK, significa que já está sincronizado
                        logger.info(f"   ✅ Lote já sincronizado (409): {len(tipos_dados)} tipos já existem no Supabase")
                        # Não contar como inseridos, mas não é um erro
                    else:
                        logger.error(f"❌ Erro ao inserir lote de tipos: {response.status_code}")
                        logger.error(f"   Resposta: {response.text[:500]}")
                        # Continuar mesmo com erro neste lote
                except Exception as e:
                    logger.error(f"❌ Erro ao inserir lote de tipos (lote {offset_codigo}): {e}", exc_info=True)
                    # Continuar mesmo com erro neste lote
        
        conn.close()
        
        if total_inseridos > 0:
            logger.info(f"✅ TOTAL: {total_inseridos} tipos sincronizados (processados em lotes)")
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} tipos sincronizados'
            }
        else:
            # Se não inseriu nenhum mas encontrou tipos, pode ser que todos já existam (409)
            logger.info(f"ℹ️  Nenhum tipo novo inserido (todos já podem estar sincronizados)")
            return {'inseridos': 0, 'mensagem': 'Nenhum tipo novo sincronizado (todos já existem)'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_tipos_processo_novos: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    # Versão fixa no código - garante que atualiza quando o código atualiza
    # Commit: 6fff877 - Fix: Versao 2.1.0 fixa no codigo (nao depende de variavel de ambiente)
    # FORÇA REBUILD - Timestamp: 2025-01-28 17:00:00
    # Se você está vendo 2.0.0, o EasyPanel NÃO está buildando do Git!
    # Esta versão DEVE aparecer: 3.6.0-AUTO-BG
    # Melhorias: Execução assíncrona, status de sincronização em /sync/status, laços reforçados contra buracos
    API_VERSION = '3.6.0-AUTO-BG'
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': API_VERSION
    })

@app.route('/auditoria/historico', methods=['GET'])
def historico_auditoria():
    """Lista histórico de sincronizações"""
    limite = request.args.get('limite', 10, type=int)
    sincronizacoes = listar_ultimas_sincronizacoes(limite)
    
    return jsonify({
        'sucesso': True,
        'total': len(sincronizacoes),
        'historico': sincronizacoes
    })

@app.route('/auditoria/verificar', methods=['GET'])
def verificar_dados():
    """Verifica integridade dos dados"""
    resultado = verificar_integridade()
    
    return jsonify({
        'sucesso': True,
        'timestamp': datetime.now().isoformat(),
        'integridade': resultado
    })

def sync_missing_clientes():
    """Sincroniza clientes faltantes (buracos) - AUTO-CORREÇÃO"""
    try:
        logger.info("🔍 Buscando clientes faltantes...")

        # Pegar todos códigos de clientes já no Supabase
        todos_clientes_sb = []
        offset = 0
        limit = 1000

        while True:
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_clientes",
                headers=headers,
                params={
                    'select': 'codigo_cliente_original',
                    'codigo_cliente_original': 'lt.500000',  # Ignorar códigos especiais
                    'limit': limit,
                    'offset': offset,
                    'order': 'codigo_cliente_original.asc'
                },
                timeout=30
            )

            if resp.status_code == 200:
                dados = resp.json()
                if not dados:
                    break
                todos_clientes_sb.extend([d['codigo_cliente_original'] for d in dados])
                offset += limit
                if len(dados) < limit:
                    break
            else:
                break

        codigos_sb = set(todos_clientes_sb)

        logger.info(f"   {len(codigos_sb)} clientes já sincronizados")

        # Buscar TODOS os clientes do Firebird (sem limitação de max_codigo)
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CODIGO
            FROM CLIENTE
            WHERE ATIVO = -1
            AND CODIGO < 500000
            ORDER BY CODIGO
        """)

        todos_clientes_fb = [row[0] for row in cursor.fetchall()]
        codigos_fb = set(todos_clientes_fb)

        logger.info(f"   {len(codigos_fb)} clientes no Firebird")

        # Encontrar buracos
        faltantes = codigos_fb - codigos_sb

        if not faltantes:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhum cliente faltante'}

        logger.info(f"   🔴 {len(faltantes)} clientes FALTANTES identificados!")

        # Processar faltantes em lotes de 1000 para evitar timeout
        faltantes_list = sorted(list(faltantes))
        total_inseridos = 0
        total_lotes = (len(faltantes_list) + 999) // 1000  # Arredondar para cima
        
        # Processar em lotes
        for lote_idx in range(0, len(faltantes_list), 1000):
            lote = faltantes_list[lote_idx:lote_idx + 1000]
            codigos_str = ','.join(map(str, lote))
            
            logger.info(f"   📦 Processando lote {lote_idx // 1000 + 1} de {total_lotes} ({len(lote)} clientes)")

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
                    CE.UF,
                    C.ATIVO
                FROM CLIENTE C
                LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
                WHERE C.CODIGO IN ({codigos_str})
            """)

            clientes_faltantes = cursor.fetchall()

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

            # Preparar dados
            clientes_dados = []
            for row in clientes_faltantes:
                codigo_cliente = row[0]
                
                # Formatar data de nascimento
                data_nasc = None
                if row[3] and row[4] and row[5]:
                    try:
                        data_nasc = f"{int(row[5])}-{int(row[4]):02d}-{int(row[3]):02d}"
                    except:
                        pass

                telefone = telefones_dict.get(codigo_cliente)
                endereco = enderecos_dict.get(codigo_cliente, {})

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
                    # Campos obrigatórios com valores padrão
                    'total_orcamentos': 0,
                    'total_orcamentos_aprovados': 0,
                    'total_orcamentos_entregues': 0,
                    'valor_total_orcamentos': 0.0,
                    'valor_total_aprovados': 0.0,
                    'valor_total_entregues': 0.0,
                    'valor_medio_orcamento': 0.0,
                    'valor_medio_aprovado': 0.0,
                    'valor_medio_entregue': 0.0,
                }
                clientes_dados.append(cliente)

            if clientes_dados:
                # Usar ignore-duplicates para evitar erro
                headers_insert = headers.copy()
                headers_insert['Prefer'] = 'resolution=ignore-duplicates'

                # Usar retry com backoff exponencial
                resp_insert = inserir_com_retry(
                    f"{SUPABASE_URL}/rest/v1/prime_clientes",
                    headers_insert,
                    clientes_dados,
                    max_tentativas=3,
                    timeout=60
                )

                if resp_insert.status_code in [200, 201]:
                    lote_inseridos = len(clientes_dados)
                    total_inseridos += lote_inseridos
                    logger.info(f"   ✅ Lote {lote_idx // 1000 + 1}: {lote_inseridos} clientes sincronizados")
                else:
                    logger.error(f"❌ Erro ao inserir lote {lote_idx // 1000 + 1}: {resp_insert.status_code}")
                    logger.error(f"   Resposta: {resp_insert.text[:200]}")
        
        conn.close()
        
        if total_inseridos > 0:
            logger.info(f"   ✅ Total: {total_inseridos} clientes faltantes sincronizados")
            return {
                'inseridos': total_inseridos,
                'mensagem': f'{total_inseridos} clientes faltantes sincronizados'
            }
        else:
            return {'inseridos': 0, 'mensagem': 'Nenhum cliente faltante sincronizado'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_missing_clientes: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

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

        logger.info(f"   {len(codigos_sb)} pedidos já sincronizados")

        # Buscar TODOS os pedidos do Firebird (sem limitação de max_codigo)
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CODIGO
            FROM ATENDIMENTO_A1
            WHERE CODIGO_CLIENTE IS NOT NULL
            ORDER BY CODIGO
        """)

        todos_pedidos_fb = [row[0] for row in cursor.fetchall()]
        codigos_fb = set(todos_pedidos_fb)

        logger.info(f"   {len(codigos_fb)} pedidos no Firebird")

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
            pedidos_sem_cliente = 0
            for row in pedidos_faltantes:
                codigo_cli = row[1]
                if codigo_cli not in cache_clientes:
                    pedidos_sem_cliente += 1
                    logger.warning(f"   ⚠️  Pedido {row[0]} sem cliente {codigo_cli} no Supabase (pulando)")
                    continue

                # Calcular status corretamente (mesmo padrão de sync_pedidos_novos)
                aviada_dt = row[3]
                entregue_dt = row[4]
                
                status_aprovacao = 'APROVADO' if aviada_dt else 'NAO_APROVADO'
                status_entrega = 'ENTREGUE' if entregue_dt else 'NAO_ENTREGUE'
                
                if entregue_dt:
                    status_geral = 'ENTREGUE'
                elif aviada_dt:
                    status_geral = 'APROVADO'
                else:
                    status_geral = 'PENDENTE'
                
                pedidos_dados.append({
                    'codigo_orcamento_original': row[0],
                    'cliente_id': cache_clientes[codigo_cli],
                    'codigo_cliente_original': codigo_cli,
                    'data_criacao': sanitizar_data(row[2]),
                    'data_aprovacao': sanitizar_data(aviada_dt),
                    'data_entrega': sanitizar_data(entregue_dt),
                    'valor_total': float(row[5]) if row[5] else 0.0,
                    'observacoes': sanitizar_string(row[6], max_length=1000),
                    'status_aprovacao': status_aprovacao,
                    'status_entrega': status_entrega,
                    'status_geral': status_geral
                })

            if pedidos_sem_cliente > 0:
                logger.warning(f"   ⚠️  Lote {i//1000 + 1}: {pedidos_sem_cliente} pedidos sem cliente (não inseridos)")
            
            if pedidos_dados:
                # Usar ignore-duplicates para evitar erro
                headers_insert = headers.copy()
                headers_insert['Prefer'] = 'resolution=ignore-duplicates'

                # Usar retry com backoff exponencial
                resp_insert = inserir_com_retry(
                    f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                    headers_insert,
                    pedidos_dados,
                    max_tentativas=3,
                    timeout=60
                )

                if resp_insert.status_code in [200, 201]:
                    total_inseridos += len(pedidos_dados)
                    logger.info(f"   ✅ Lote {i//1000 + 1}: {len(pedidos_dados)} pedidos inseridos")
                else:
                    logger.error(f"   ❌ Erro ao inserir lote {i//1000 + 1}: Status {resp_insert.status_code}")
                    logger.error(f"   Resposta: {resp_insert.text[:500]}")

        conn.close()
        
        if len(faltantes) > total_inseridos:
            faltaram = len(faltantes) - total_inseridos
            logger.warning(f"   ⚠️  {faltaram} pedidos não foram inseridos (provavelmente faltam dependências)")
        
        return {
            'inseridos': total_inseridos,
            'total_faltantes': len(faltantes),
            'mensagem': f'{total_inseridos} de {len(faltantes)} pedidos faltantes sincronizados'
        }

    except Exception as e:
        logger.error(f"❌ Erro em sync_missing_pedidos: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

def sync_missing_formulas():
    """Sincroniza fórmulas faltantes (buracos)"""
    try:
        logger.info("🔍 Buscando fórmulas faltantes...")

        # Pegar todos códigos de fórmulas já no Supabase (comparando por codigo_orcamento_original + numero_formula)
        todas_formulas_sb = []
        offset = 0
        limit = 1000

        while True:
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_formulas",
                headers=headers,
                params={
                    'select': 'codigo_orcamento_original,numero_formula',
                    'limit': limit,
                    'offset': offset,
                    'order': 'codigo_orcamento_original.asc,numero_formula.asc'
                },
                timeout=30
            )

            if resp.status_code == 200:
                dados = resp.json()
                if not dados:
                    break
                todas_formulas_sb.extend([(d['codigo_orcamento_original'], d['numero_formula']) for d in dados])
                offset += limit
            else:
                break

        formulas_sb = set(todas_formulas_sb)

        logger.info(f"   {len(formulas_sb)} fórmulas já sincronizadas")

        # Buscar TODAS as fórmulas do Firebird (sem limitação de max_codigo)
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CODIGO_ATEND_A1, NUMEROFORMULA
            FROM ATENDIMENTO_A2
            WHERE CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY CODIGO_ATEND_A1, NUMEROFORMULA
        """)

        todas_formulas_fb = [(row[0], row[1]) for row in cursor.fetchall()]
        formulas_fb = set(todas_formulas_fb)

        logger.info(f"   {len(formulas_fb)} fórmulas no Firebird")

        # Encontrar buracos
        faltantes = formulas_fb - formulas_sb

        if not faltantes:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhuma fórmula faltante'}

        logger.info(f"   🔴 {len(faltantes)} fórmulas FALTANTES identificadas!")

        # Buscar dados das fórmulas faltantes (em lotes de 1000)
        faltantes_list = sorted(list(faltantes))
        total_inseridos = 0

        for i in range(0, len(faltantes_list), 1000):
            lote = faltantes_list[i:i+1000]
            
            # Construir query com múltiplos OR (lote pequeno)
            condicoes = []
            for codigo, num in lote:
                condicoes.append(f"(CODIGO_ATEND_A1 = {codigo} AND NUMEROFORMULA = {num})")
            
            cursor.execute(f"""
                SELECT
                    A2.CODIGO_ATEND_A1,
                    A2.NUMEROFORMULA,
                    A2.TEXTOROTULO,
                    A2.POSOLOGIA,
                    A2.VALORFORMULA_VENDA
                FROM ATENDIMENTO_A2 A2
                WHERE ({' OR '.join(condicoes)})
            """)

            formulas_faltantes = cursor.fetchall()

            # Buscar pedidos
            codigos_pedidos = list(set([row[0] for row in formulas_faltantes]))
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                headers=headers,
                params={
                    'select': 'id,codigo_orcamento_original',
                    'codigo_orcamento_original': f'in.({",".join(map(str, codigos_pedidos))})'
                },
                timeout=30
            )

            cache_pedidos = {}
            if response.status_code == 200:
                for ped in response.json():
                    cache_pedidos[ped['codigo_orcamento_original']] = ped['id']

            # Preparar dados
            formulas_dados = []
            formulas_sem_pedido = 0
            for row in formulas_faltantes:
                codigo_atend, num_formula = row[0], row[1]
                pedido_id = cache_pedidos.get(codigo_atend)
                if not pedido_id:
                    formulas_sem_pedido += 1
                    logger.warning(f"   ⚠️  Fórmula ({codigo_atend}, {num_formula}) sem pedido no Supabase (pulando)")
                    continue

                formulas_dados.append({
                    'pedido_id': pedido_id,
                    'codigo_orcamento_original': codigo_atend,
                    'numero_formula': num_formula,
                    'descricao': limpar_string(row[2]),
                    'posologia': limpar_string(row[3]),
                    'valor_formula': float(row[4]) if row[4] else 0.0,
                    'updated_at': datetime.now().isoformat()
                })

            if formulas_sem_pedido > 0:
                logger.warning(f"   ⚠️  Lote {i//1000 + 1}: {formulas_sem_pedido} fórmulas sem pedido (não inseridas)")
            
            if formulas_dados:
                headers_insert = headers.copy()
                headers_insert['Prefer'] = 'resolution=ignore-duplicates'

                # Usar retry com backoff exponencial
                resp_insert = inserir_com_retry(
                    f"{SUPABASE_URL}/rest/v1/prime_formulas",
                    headers_insert,
                    formulas_dados,
                    max_tentativas=3,
                    timeout=60
                )

                if resp_insert.status_code in [200, 201]:
                    total_inseridos += len(formulas_dados)
                    logger.info(f"   ✅ Lote {i//1000 + 1}: {len(formulas_dados)} fórmulas inseridas")
                else:
                    logger.error(f"   ❌ Erro ao inserir lote {i//1000 + 1}: Status {resp_insert.status_code}")
                    logger.error(f"   Resposta: {resp_insert.text[:500]}")

        conn.close()
        
        if len(faltantes) > total_inseridos:
            faltaram = len(faltantes) - total_inseridos
            logger.warning(f"   ⚠️  {faltaram} fórmulas não foram inseridas (provavelmente faltam dependências)")
        
        return {
            'inseridos': total_inseridos,
            'total_faltantes': len(faltantes),
            'mensagem': f'{total_inseridos} de {len(faltantes)} fórmulas faltantes sincronizadas'
        }

    except Exception as e:
        logger.error(f"❌ Erro em sync_missing_formulas: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

def sync_missing_rastreabilidade():
    """Sincroniza rastreabilidade faltante (buracos)"""
    try:
        logger.info("🔍 Buscando rastreabilidade faltante...")

        # Pegar todos códigos de rastreabilidade já no Supabase
        todos_rastros_sb = []
        offset = 0
        limit = 1000

        while True:
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade",
                headers=headers,
                params={
                    'select': 'codigo_processo_original',
                    'limit': limit,
                    'offset': offset,
                    'order': 'codigo_processo_original.asc'
                },
                timeout=30
            )

            if resp.status_code == 200:
                dados = resp.json()
                if not dados:
                    break
                todos_rastros_sb.extend([d['codigo_processo_original'] for d in dados])
                offset += limit
            else:
                break

        codigos_sb = set(todos_rastros_sb)

        logger.info(f"   {len(codigos_sb)} registros já sincronizados")

        # Buscar TODOS os registros do Firebird (sem limitação de max_codigo)
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CODIGO
            FROM PROCESSO_MANIPULACAO
            ORDER BY CODIGO
        """)

        todos_rastros_fb = [row[0] for row in cursor.fetchall()]
        codigos_fb = set(todos_rastros_fb)

        logger.info(f"   {len(codigos_fb)} registros no Firebird")

        # Encontrar buracos
        faltantes = codigos_fb - codigos_sb

        if not faltantes:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhum registro faltante'}

        logger.info(f"   🔴 {len(faltantes)} registros FALTANTES identificados!")

        # Buscar dados dos registros faltantes (em lotes de 1000)
        faltantes_list = sorted(list(faltantes))
        total_inseridos = 0

        for i in range(0, len(faltantes_list), 1000):
            lote = faltantes_list[i:i+1000]
            codigos_str = ','.join(map(str, lote))

            cursor.execute(f"""
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
                WHERE PM.CODIGO IN ({codigos_str})
            """)

            rastros_faltantes = cursor.fetchall()

            # Buscar pedidos e tipos em lote
            codigos_orcamento = list(set([row[2] for row in rastros_faltantes if row[2]]))
            codigos_tipo = list(set([row[3] for row in rastros_faltantes if row[3]]))

            cache_pedidos = {}
            if codigos_orcamento:
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                    headers=headers,
                    params={
                        'select': 'id,codigo_orcamento_original',
                        'codigo_orcamento_original': f'in.({",".join(map(str, codigos_orcamento))})'
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    for ped in response.json():
                        cache_pedidos[ped['codigo_orcamento_original']] = ped['id']

            cache_tipos = {}
            if codigos_tipo:
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/prime_tipos_processo",
                    headers=headers,
                    params={
                        'select': 'id,codigo_tipo_original',
                        'codigo_tipo_original': f'in.({",".join(map(str, codigos_tipo))})'
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    for tipo in response.json():
                        cache_tipos[tipo['codigo_tipo_original']] = tipo['id']

            # Preparar dados
            rastros_dados = []
            rastros_sem_dependencias = 0
            for row in rastros_faltantes:
                codigo_orcamento = row[2]
                codigo_tipo = row[3]

                pedido_id = cache_pedidos.get(codigo_orcamento)
                tipo_processo_id = cache_tipos.get(codigo_tipo)

                if not pedido_id or not tipo_processo_id:
                    rastros_sem_dependencias += 1
                    if rastros_sem_dependencias <= 5:  # Logar apenas os primeiros 5 para não poluir
                        logger.warning(f"   ⚠️  Rastreabilidade {row[0]} sem pedido {codigo_orcamento} ou tipo {codigo_tipo} (pulando)")
                    continue

                rastros_dados.append({
                    'codigo_processo_original': row[0],
                    'pedido_id': pedido_id,
                    'codigo_orcamento_original': codigo_orcamento,
                    'tipo_processo_id': tipo_processo_id,
                    'codigo_tipo_original': codigo_tipo,
                    'tipo_movimento': row[1],
                    'codigo_funcionario': row[4],
                    'data_processo': row[5].isoformat() if row[5] else None,
                    'hora_processo': str(row[6]) if row[6] else None,
                    'sequencia': row[7],
                    'status_processo': 'CONCLUIDO',
                    'updated_at': datetime.now().isoformat()
                })

            if rastros_sem_dependencias > 0:
                logger.warning(f"   ⚠️  Lote {i//1000 + 1}: {rastros_sem_dependencias} registros sem dependências (não inseridos)")
            
            if rastros_dados:
                headers_insert = headers.copy()
                headers_insert['Prefer'] = 'resolution=ignore-duplicates'

                # Usar retry com backoff exponencial
                resp_insert = inserir_com_retry(
                    f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade",
                    headers_insert,
                    rastros_dados,
                    max_tentativas=3,
                    timeout=60
                )

                if resp_insert.status_code in [200, 201]:
                    total_inseridos += len(rastros_dados)
                    logger.info(f"   ✅ Lote {i//1000 + 1}: {len(rastros_dados)} registros inseridos")
                else:
                    logger.error(f"   ❌ Erro ao inserir lote {i//1000 + 1}: Status {resp_insert.status_code}")
                    logger.error(f"   Resposta: {resp_insert.text[:500]}")

        conn.close()
        
        if len(faltantes) > total_inseridos:
            faltaram = len(faltantes) - total_inseridos
            logger.warning(f"   ⚠️  {faltaram} registros não foram inseridos (provavelmente faltam dependências)")
        
        return {
            'inseridos': total_inseridos,
            'total_faltantes': len(faltantes),
            'mensagem': f'{total_inseridos} de {len(faltantes)} registros faltantes sincronizados'
        }

    except Exception as e:
        logger.error(f"❌ Erro em sync_missing_rastreabilidade: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

def sync_missing_formulas_itens():
    """Sincroniza itens de fórmulas faltantes (buracos)"""
    try:
        logger.info("🔍 Buscando itens de fórmulas faltantes...")

        # Pegar todos itens já no Supabase (codigo_atendimento + numero_formula + numero_linha)
        todos_itens_sb = []
        offset = 0
        limit = 1000

        while True:
            try:
                resp = buscar_com_retry(
                    f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
                    headers,
                    params={
                        'select': 'codigo_atendimento_original,numero_formula,numero_linha',
                        'limit': limit,
                        'offset': offset,
                        'order': 'codigo_atendimento_original.asc,numero_formula.asc,numero_linha.asc'
                    },
                    max_tentativas=3,
                    timeout=30
                )
            except Exception as e:
                logger.error(f"   ❌ Erro ao buscar itens no Supabase (offset {offset}): {e}", exc_info=True)
                break

            if resp.status_code != 200:
                logger.error(f"   ❌ Erro ao buscar itens no Supabase (offset {offset}): {resp.status_code} - {resp.text[:200]}")
                break

            dados = resp.json()
            if not dados:
                break

            todos_itens_sb.extend([(d['codigo_atendimento_original'], d['numero_formula'], d['numero_linha']) for d in dados])
            offset += len(dados)
            if len(dados) < limit:
                break

        itens_sb = set(todos_itens_sb)

        logger.info(f"   {len(itens_sb)} itens já sincronizados")

        # Buscar TODOS os itens do Firebird (sem limitação)
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CODIGO_ATEND_A1, NUMEROFORMULA, NUMEROLINHA
            FROM ATENDIMENTO_A3
            WHERE CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY CODIGO_ATEND_A1, NUMEROFORMULA, NUMEROLINHA
        """)

        todos_itens_fb = [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        itens_fb = set(todos_itens_fb)

        logger.info(f"   {len(itens_fb)} itens no Firebird")

        # Encontrar buracos
        faltantes = itens_fb - itens_sb

        if not faltantes:
            conn.close()
            return {'inseridos': 0, 'mensagem': 'Nenhum item faltante'}

        logger.info(f"   🔴 {len(faltantes)} itens FALTANTES identificados!")

        # Buscar cache de fórmulas (uma vez só)
        logger.info("   Carregando cache de fórmulas...")
        cache_formulas = {}
        offset = 0
        while True:
            try:
                resp = buscar_com_retry(
                    f"{SUPABASE_URL}/rest/v1/prime_formulas",
                    headers,
                    params={
                        'select': 'id,pedido_id,codigo_orcamento_original,numero_formula',
                        'limit': limit,
                        'offset': offset,
                        'order': 'codigo_orcamento_original.asc,numero_formula.asc'
                    },
                    max_tentativas=3,
                    timeout=30
                )
            except Exception as e:
                logger.error(f"   ❌ Erro ao carregar cache de fórmulas (offset {offset}): {e}", exc_info=True)
                break

            if resp.status_code != 200:
                logger.error(f"   ❌ Erro ao carregar cache de fórmulas (offset {offset}): {resp.status_code} - {resp.text[:200]}")
                break

            dados = resp.json()
            if not dados:
                break

            for f in dados:
                cache_formulas[(f['codigo_orcamento_original'], f['numero_formula'])] = {
                    'id': f['id'],
                    'pedido_id': f['pedido_id']
                }
            offset += len(dados)
            if len(dados) < limit:
                break
        logger.info(f"   Cache fórmulas: {len(cache_formulas)} fórmulas")

        # Buscar dados dos itens faltantes (em lotes de 100)
        faltantes_list = sorted(list(faltantes))
        total_inseridos = 0

        for i in range(0, len(faltantes_list), 100):
            lote = faltantes_list[i:i+100]
            codigos_str = ','.join(map(str, [cod for cod, _, _ in lote]))
            
            # Buscar todos itens desses códigos
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
            """)

            itens_fb_dados = cursor.fetchall()
            faltantes_set = set(lote)
            batch_insert = []
            itens_sem_formula = 0

            for row in itens_fb_dados:
                cod, num, lin, cod_prod, nome, qtd, unid, custo, venda, obs = row
                # Verificar se este item está na lista de faltantes
                if (cod, num, lin) not in faltantes_set:
                    continue

                formula_info = cache_formulas.get((cod, num))
                if not formula_info:
                    itens_sem_formula += 1
                    if itens_sem_formula <= 5:  # Logar apenas os primeiros 5
                        logger.warning(f"   ⚠️  Item ({cod}, {num}, {lin}) sem fórmula no Supabase (pulando)")
                    continue

                batch_insert.append({
                    'formula_id': formula_info['id'],
                    'pedido_id': formula_info['pedido_id'],
                    'codigo_atendimento_original': cod,
                    'numero_formula': num,
                    'numero_linha': lin,
                    'codigo_produto': cod_prod,
                    'nome_produto': limpar_string(nome) or 'PRODUTO NAO IDENTIFICADO',
                    'quantidade': float(qtd) if qtd else None,
                    'unidade': limpar_string(unid),
                    'quantidade_calculo': float(qtd) if qtd else None,
                    'valor_custo': float(custo) if custo else 0.0,
                    'valor_venda': float(venda) if venda else 0.0,
                    'valor_venda_desconto': 0.0,
                    'inclusao_sistema': True,
                    'visualizar_produto': True,
                    'observacao': limpar_string(obs),
                    'updated_at': datetime.now().isoformat()
                })

            if batch_insert:
                headers_insert = headers.copy()
                headers_insert['Prefer'] = 'resolution=ignore-duplicates'

                # Usar retry com backoff exponencial
                resp_insert = inserir_com_retry(
                    f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
                    headers_insert,
                    batch_insert,
                    max_tentativas=3,
                    timeout=60
                )

                if resp_insert.status_code in [200, 201]:
                    total_inseridos += len(batch_insert)
                    logger.info(f"   ✅ Lote {i//100 + 1}: {len(batch_insert)} itens inseridos")
                else:
                    logger.error(f"   ❌ Erro ao inserir lote {i//100 + 1}: Status {resp_insert.status_code}")
                    logger.error(f"   Resposta: {resp_insert.text[:500]}")
            
            if itens_sem_formula > 0:
                logger.warning(f"   ⚠️  Lote {i//100 + 1}: {itens_sem_formula} itens sem fórmula (não inseridos)")

        conn.close()
        
        if len(faltantes) > total_inseridos:
            faltaram = len(faltantes) - total_inseridos
            logger.warning(f"   ⚠️  {faltaram} itens não foram inseridos (provavelmente faltam dependências)")
        
        return {
            'inseridos': total_inseridos,
            'total_faltantes': len(faltantes),
            'mensagem': f'{total_inseridos} de {len(faltantes)} itens faltantes sincronizados'
        }

    except Exception as e:
        logger.error(f"❌ Erro em sync_missing_formulas_itens: {e}", exc_info=True)
        import traceback
        logger.error(f"   Stack trace: {traceback.format_exc()}")
        return {'inseridos': 0, 'erro': str(e), 'traceback': traceback.format_exc()}

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

def executar_sync_completa(trigger='manual'):
    """Executa a sincronização completa de forma síncrona (utilizada em threads de background)."""
    auditoria_id = None
    inicio = datetime.now()
    try:
        logger.info("=" * 70)
        logger.info("🚀 SINCRONIZAÇÃO INCREMENTAL V2.0 - COM AUDITORIA")
        logger.info("=" * 70)
        logger.info(f"🎯 Disparo: {trigger}")

        # Registrar início na auditoria
        auditoria_id = iniciar_auditoria(
            tabela_origem='firebird',
            tabela_destino='supabase',
            total_firebird=0  # Será atualizado se necessário
        )

        # Sincronizar na ordem correta (respeitando dependências)
        # 1. Clientes primeiro (não depende de nada)
        logger.info("\n" + "=" * 70)
        logger.info("1️⃣ SINCRONIZANDO CLIENTES (ordem: 1/6)")
        logger.info("=" * 70)
        try:
            result_clientes = sync_clientes_novos()
            logger.info(f"📋 Clientes: {result_clientes}")
            if result_clientes.get('erro'):
                logger.warning(f"⚠️ Erro em clientes (continuando): {result_clientes['erro']}")

            # AUTOMATICAMENTE sincronizar clientes faltantes após sincronização incremental
            logger.info("\n" + "=" * 70)
            logger.info("1️⃣.1 SINCRONIZANDO CLIENTES FALTANTES (auto-correção)")
            logger.info("=" * 70)
            try:
                result_clientes_missing = sync_missing_clientes()
                # SEMPRE adicionar ao total, mesmo se for 0 (para logar que foi executado)
                logger.info(f"✅ Clientes faltantes: {result_clientes_missing.get('inseridos', 0)} sincronizados")
                result_clientes['inseridos'] = result_clientes.get('inseridos', 0) + result_clientes_missing.get('inseridos', 0)
                result_clientes['faltantes_sincronizados'] = result_clientes_missing.get('inseridos', 0)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao sincronizar clientes faltantes (continuando): {e}")

        except Exception as e:
            logger.error(f"❌ Erro crítico em clientes: {e}", exc_info=True)
            result_clientes = {'inseridos': 0, 'erro': str(e)}

        # 2. Pedidos (depende de clientes)
        logger.info("\n" + "=" * 70)
        logger.info("2️⃣ SINCRONIZANDO PEDIDOS (ordem: 2/6)")
        logger.info("=" * 70)
        try:
            result_pedidos = sync_pedidos_novos()
            logger.info(f"📋 Pedidos: {result_pedidos}")
            if result_pedidos.get('erro'):
                logger.warning(f"⚠️ Erro em pedidos (continuando): {result_pedidos['erro']}")

            # AUTOMATICAMENTE sincronizar pedidos faltantes após sincronização incremental
            # EXECUTAR EM LOOP até preencher TODOS os buracos (sem limite de iterações)
            logger.info("\n" + "=" * 70)
            logger.info("2️⃣.1 SINCRONIZANDO PEDIDOS FALTANTES (auto-correção)")
            logger.info("=" * 70)
            max_iteracoes = 200  # Limite de segurança alto
            iteracao = 0
            total_pedidos_missing = 0
            iteracoes_sem_progresso = 0
            max_iteracoes_sem_progresso = 10  # Permite mais tentativas antes de desistir
            ultimo_total_faltantes = None

            while iteracao < max_iteracoes:
                iteracao += 1
                try:
                    logger.info(f"   Iteração {iteracao}...")
                    result_pedidos_missing = sync_missing_pedidos()
                    inseridos_iteracao = result_pedidos_missing.get('inseridos', 0)
                    total_faltantes = result_pedidos_missing.get('total_faltantes', 0)
                    total_pedidos_missing += inseridos_iteracao

                    logger.info(f"   ✅ Iteração {iteracao}: {inseridos_iteracao} pedidos sincronizados (faltantes: {total_faltantes})")

                    if total_faltantes == 0:
                        logger.info("   ✅ Todos os buracos preenchidos - parando loop")
                        break

                    if inseridos_iteracao > 0 or (ultimo_total_faltantes is not None and total_faltantes < ultimo_total_faltantes):
                        iteracoes_sem_progresso = 0
                    else:
                        iteracoes_sem_progresso += 1
                        logger.warning(f"   ⚠️  {total_faltantes} pedidos ainda faltam (iterações sem progresso: {iteracoes_sem_progresso}/{max_iteracoes_sem_progresso})")
                        if iteracoes_sem_progresso >= max_iteracoes_sem_progresso:
                            logger.warning("   ⚠️  Parando loop: iterações consecutivas sem progresso (provavelmente faltam dependências)")
                            break

                    ultimo_total_faltantes = total_faltantes
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao sincronizar pedidos faltantes na iteração {iteracao} (continuando): {e}")
                    break

            result_pedidos['inseridos'] = result_pedidos.get('inseridos', 0) + total_pedidos_missing
            result_pedidos['faltantes_restantes'] = ultimo_total_faltantes or 0
            result_pedidos['iteracoes_missing'] = iteracao
            result_pedidos['faltantes_sincronizados'] = total_pedidos_missing

        except Exception as e:
            logger.error(f"❌ Erro crítico em pedidos: {e}", exc_info=True)
            result_pedidos = {'inseridos': 0, 'erro': str(e)}

        # 3. Fórmulas (depende de pedidos)
        logger.info("\n" + "=" * 70)
        logger.info("3️⃣ SINCRONIZANDO FÓRMULAS (ordem: 3/6)")
        logger.info("=" * 70)
        try:
            result_formulas = sync_formulas_novas()
            logger.info(f"📋 Fórmulas: {result_formulas}")
            if result_formulas.get('erro'):
                logger.warning(f"⚠️ Erro em fórmulas (continuando): {result_formulas['erro']}")

            logger.info("\n" + "=" * 70)
            logger.info("3️⃣.1 SINCRONIZANDO FÓRMULAS FALTANTES (auto-correção)")
            logger.info("=" * 70)
            max_iteracoes = 200
            iteracao = 0
            total_formulas_missing = 0
            iteracoes_sem_progresso = 0
            max_iteracoes_sem_progresso = 10
            ultimo_total_faltantes = None

            while iteracao < max_iteracoes:
                iteracao += 1
                try:
                    logger.info(f"   Iteração {iteracao}...")
                    result_formulas_missing = sync_missing_formulas()
                    inseridos_iteracao = result_formulas_missing.get('inseridos', 0)
                    total_faltantes = result_formulas_missing.get('total_faltantes', 0)
                    total_formulas_missing += inseridos_iteracao

                    logger.info(f"   ✅ Iteração {iteracao}: {inseridos_iteracao} fórmulas sincronizadas (faltantes: {total_faltantes})")

                    if total_faltantes == 0:
                        logger.info("   ✅ Todos os buracos preenchidos - parando loop")
                        break

                    if inseridos_iteracao > 0 or (ultimo_total_faltantes is not None and total_faltantes < ultimo_total_faltantes):
                        iteracoes_sem_progresso = 0
                    else:
                        iteracoes_sem_progresso += 1
                        logger.warning(f"   ⚠️  {total_faltantes} fórmulas ainda faltam (iterações sem progresso: {iteracoes_sem_progresso}/{max_iteracoes_sem_progresso})")
                        if iteracoes_sem_progresso >= max_iteracoes_sem_progresso:
                            logger.warning("   ⚠️  Parando loop: iterações consecutivas sem progresso (provavelmente faltam dependências)")
                            break

                    ultimo_total_faltantes = total_faltantes
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao sincronizar fórmulas faltantes na iteração {iteracao} (continuando): {e}")
                    break

            result_formulas['inseridos'] = result_formulas.get('inseridos', 0) + total_formulas_missing
            result_formulas['faltantes_restantes'] = ultimo_total_faltantes or 0
            result_formulas['iteracoes_missing'] = iteracao
            result_formulas['faltantes_sincronizados'] = total_formulas_missing
        except Exception as e:
            logger.error(f"❌ Erro crítico em fórmulas: {e}", exc_info=True)
            result_formulas = {'inseridos': 0, 'erro': str(e)}

        # 4. Itens de Fórmulas (depende de fórmulas)
        logger.info("\n" + "=" * 70)
        logger.info("4️⃣ SINCRONIZANDO ITENS DE FÓRMULAS (ordem: 4/6)")
        logger.info("=" * 70)
        try:
            result_itens = sync_formulas_itens_novos()
            logger.info(f"📋 Itens: {result_itens}")
            if result_itens.get('erro'):
                logger.warning(f"⚠️ Erro em itens (continuando): {result_itens['erro']}")

            logger.info("\n" + "=" * 70)
            logger.info("4️⃣.1 SINCRONIZANDO ITENS FALTANTES (auto-correção)")
            logger.info("=" * 70)
            max_iteracoes = 200
            iteracao = 0
            total_itens_missing = 0
            iteracoes_sem_progresso = 0
            max_iteracoes_sem_progresso = 10
            ultimo_total_faltantes = None

            while iteracao < max_iteracoes:
                iteracao += 1
                try:
                    logger.info(f"   Iteração {iteracao}...")
                    result_itens_missing = sync_missing_formulas_itens()
                    inseridos_iteracao = result_itens_missing.get('inseridos', 0)
                    total_faltantes = result_itens_missing.get('total_faltantes', 0)
                    total_itens_missing += inseridos_iteracao

                    logger.info(f"   ✅ Iteração {iteracao}: {inseridos_iteracao} itens sincronizados (faltantes: {total_faltantes})")

                    if total_faltantes == 0:
                        logger.info("   ✅ Todos os buracos preenchidos - parando loop")
                        break

                    if inseridos_iteracao > 0 or (ultimo_total_faltantes is not None and total_faltantes < ultimo_total_faltantes):
                        iteracoes_sem_progresso = 0
                    else:
                        iteracoes_sem_progresso += 1
                        logger.warning(f"   ⚠️  {total_faltantes} itens ainda faltam (iterações sem progresso: {iteracoes_sem_progresso}/{max_iteracoes_sem_progresso})")
                        if iteracoes_sem_progresso >= max_iteracoes_sem_progresso:
                            logger.warning("   ⚠️  Parando loop: iterações consecutivas sem progresso (provavelmente faltam dependências)")
                            break

                    ultimo_total_faltantes = total_faltantes
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao sincronizar itens faltantes na iteração {iteracao} (continuando): {e}")
                    break

            result_itens['inseridos'] = result_itens.get('inseridos', 0) + total_itens_missing
            result_itens['faltantes_restantes'] = ultimo_total_faltantes or 0
            result_itens['iteracoes_missing'] = iteracao
            result_itens['faltantes_sincronizados'] = total_itens_missing
        except Exception as e:
            logger.error(f"❌ Erro crítico em itens: {e}", exc_info=True)
            result_itens = {'inseridos': 0, 'erro': str(e)}

        # 5. Tipos Processo (FASE 1 - tabela de referência, SEM dependências)
        logger.info("\n" + "=" * 70)
        logger.info("5️⃣ SINCRONIZANDO TIPOS PROCESSO (ordem: 5/6 - FASE 1)")
        logger.info("=" * 70)
        try:
            result_tipos = sync_tipos_processo_novos()
            logger.info(f"📋 Tipos Processo: {result_tipos}")
            if result_tipos.get('erro'):
                logger.warning(f"⚠️ Erro em tipos processo (continuando): {result_tipos['erro']}")
        except Exception as e:
            logger.error(f"❌ Erro crítico em tipos processo: {e}", exc_info=True)
            result_tipos = {'inseridos': 0, 'erro': str(e)}

        # 6. Rastreabilidade (FASE 3 - depende de pedidos + tipos_processo)
        logger.info("\n" + "=" * 70)
        logger.info("6️⃣ SINCRONIZANDO RASTREABILIDADE (ordem: 6/6 - FASE 3)")
        logger.info("=" * 70)
        logger.info("   ⚠️  Dependências: prime_pedidos ✅ + prime_tipos_processo ✅")
        try:
            result_rastreabilidade = sync_rastreabilidade_nova()
            logger.info(f"📋 Rastreabilidade: {result_rastreabilidade}")
            if result_rastreabilidade.get('erro'):
                logger.warning(f"⚠️ Erro em rastreabilidade (continuando): {result_rastreabilidade['erro']}")

            logger.info("\n" + "=" * 70)
            logger.info("6️⃣.1 SINCRONIZANDO RASTREABILIDADE FALTANTE (auto-correção)")
            logger.info("=" * 70)
            max_iteracoes = 200
            iteracao = 0
            total_rastreabilidade_missing = 0
            iteracoes_sem_progresso = 0
            max_iteracoes_sem_progresso = 15  # rastreabilidade depende de múltiplas tabelas
            ultimo_total_faltantes = None

            while iteracao < max_iteracoes:
                iteracao += 1
                try:
                    logger.info(f"   Iteração {iteracao}...")
                    result_rastreabilidade_missing = sync_missing_rastreabilidade()
                    inseridos_iteracao = result_rastreabilidade_missing.get('inseridos', 0)
                    total_faltantes = result_rastreabilidade_missing.get('total_faltantes', 0)
                    total_rastreabilidade_missing += inseridos_iteracao

                    logger.info(f"   ✅ Iteração {iteracao}: {inseridos_iteracao} registros sincronizados (faltantes: {total_faltantes})")

                    if total_faltantes == 0:
                        logger.info("   ✅ Todos os buracos preenchidos - parando loop")
                        break

                    if inseridos_iteracao > 0 or (ultimo_total_faltantes is not None and total_faltantes < ultimo_total_faltantes):
                        iteracoes_sem_progresso = 0
                    else:
                        iteracoes_sem_progresso += 1
                        logger.warning(f"   ⚠️  {total_faltantes} registros ainda faltam (iterações sem progresso: {iteracoes_sem_progresso}/{max_iteracoes_sem_progresso})")
                        if iteracoes_sem_progresso >= max_iteracoes_sem_progresso:
                            logger.warning("   ⚠️  Parando loop: iterações consecutivas sem progresso (provavelmente faltam dependências)")
                            break

                    ultimo_total_faltantes = total_faltantes
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao sincronizar rastreabilidade faltante na iteração {iteracao} (continuando): {e}")
                    break

            result_rastreabilidade['inseridos'] = result_rastreabilidade.get('inseridos', 0) + total_rastreabilidade_missing
            result_rastreabilidade['faltantes_restantes'] = ultimo_total_faltantes or 0
            result_rastreabilidade['iteracoes_missing'] = iteracao
            result_rastreabilidade['faltantes_sincronizados'] = total_rastreabilidade_missing
        except Exception as e:
            logger.error(f"❌ Erro crítico em rastreabilidade: {e}", exc_info=True)
            result_rastreabilidade = {'inseridos': 0, 'erro': str(e)}

        tempo_total = (datetime.now() - inicio).total_seconds()

        total_inseridos = (
            result_clientes.get('inseridos', 0) +
            result_pedidos.get('inseridos', 0) +
            result_formulas.get('inseridos', 0) +
            result_itens.get('inseridos', 0) +
            result_rastreabilidade.get('inseridos', 0) +
            result_tipos.get('inseridos', 0)
        )

        # Verificar se houve erros
        erros = []
        if result_clientes.get('erro'):
            erros.append(f"clientes: {result_clientes['erro']}")
        if result_pedidos.get('erro'):
            erros.append(f"pedidos: {result_pedidos['erro']}")
        if result_formulas.get('erro'):
            erros.append(f"formulas: {result_formulas['erro']}")
        if result_itens.get('erro'):
            erros.append(f"itens: {result_itens['erro']}")
        if result_rastreabilidade.get('erro'):
            erros.append(f"rastreabilidade: {result_rastreabilidade['erro']}")
        if result_tipos.get('erro'):
            erros.append(f"tipos_processo: {result_tipos['erro']}")

        # Verificar integridade
        try:
            integridade = verificar_integridade()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar integridade: {e}")
            integridade = {'status': 'erro', 'mensagem': str(e)}

        # Finalizar auditoria
        status_final = 'sucesso' if len(erros) == 0 else 'sucesso_com_avisos'
        mensagem_final = f'Total sincronizado: {total_inseridos} registros'
        if erros:
            mensagem_final += f'. Avisos: {"; ".join(erros)}'

        finalizar_auditoria(
            auditoria_id=auditoria_id,
            total_supabase=total_inseridos,
            registros_novos=total_inseridos,
            registros_atualizados=0,
            status=status_final,
            mensagem=mensagem_final,
            detalhes={
                'clientes': result_clientes,
                'pedidos': result_pedidos,
                'formulas': result_formulas,
                'formulas_itens': result_itens,
                'rastreabilidade': result_rastreabilidade,
                'tipos_processo': result_tipos,
                'integridade': integridade,
                'avisos': erros if erros else None
            }
        )

        # Versão fixa no código - garante que atualiza quando o código atualiza
        API_VERSION = '3.6.0-AUTO-BG'
        resultado = {
            'sucesso': True,
            'timestamp': datetime.now().isoformat(),
            'tempo_execucao_segundos': tempo_total,
            'version': API_VERSION,
            'auditoria_id': auditoria_id,
            'clientes': result_clientes,
            'pedidos': result_pedidos,
            'formulas': result_formulas,
            'formulas_itens': result_itens,
            'rastreabilidade': result_rastreabilidade,
            'tipos_processo': result_tipos,
            'total_inseridos': total_inseridos,
            'integridade': integridade,
            'trigger': trigger
        }

        if erros:
            resultado['avisos'] = erros
            logger.warning(f"⚠️ CONCLUÍDO COM AVISOS - Total: {total_inseridos} registros em {tempo_total:.1f}s")
            logger.warning(f"   Avisos: {len(erros)} tabela(s) com problemas")
        else:
            logger.info(f"✅ CONCLUÍDO COM SUCESSO - Total: {total_inseridos} registros em {tempo_total:.1f}s")

        return resultado

    except Exception as e:
        logger.error(f"❌ Erro na sincronização: {e}")

        if auditoria_id:
            finalizar_auditoria(
                auditoria_id=auditoria_id,
                status='erro',
                mensagem=str(e)
            )

        raise


def _executar_sync_background(trigger):
    """Executa a sincronização em uma thread dedicada atualizando o estado global."""
    inicio_thread = datetime.now()
    try:
        resultado = executar_sync_completa(trigger=trigger)
        fim_thread = datetime.now()
        _atualizar_estado_sync(
            running=False,
            finished_at=fim_thread.isoformat(),
            last_duration_seconds=(fim_thread - inicio_thread).total_seconds(),
            last_error=None,
            last_result=resultado
        )
    except Exception as exc:
        fim_thread = datetime.now()
        logger.exception("❌ Falha na execução em background: %s", exc)
        _atualizar_estado_sync(
            running=False,
            finished_at=fim_thread.isoformat(),
            last_duration_seconds=(fim_thread - inicio_thread).total_seconds(),
            last_error=str(exc),
            last_result=None
        )


@app.route('/sync', methods=['GET', 'POST'])
def sync():
    """Endpoint principal: dispara a sincronização em background."""
    trigger = (
        request.args.get('trigger')
        or request.headers.get('X-Sync-Trigger')
        or ('cron' if request.headers.get('User-Agent', '').lower().startswith('supabase') else 'manual')
    )

    with sync_lock:
        if sync_state['running']:
            estado_atual = dict(sync_state)
            logger.info("🔁 Sincronização já em andamento - disparo ignorado")
            return jsonify({
                'sucesso': True,
                'mensagem': 'Sincronização já está em execução',
                'status': estado_atual
            }), 202

        agora = datetime.now()
        _atualizar_estado_sync(
            running=True,
            started_at=agora.isoformat(),
            finished_at=None,
            last_error=None,
            trigger=trigger
        )

    worker = Thread(target=_executar_sync_background, args=(trigger,), daemon=True)
    worker.start()

    with sync_lock:
        estado_inicial = dict(sync_state)

    return jsonify({
        'sucesso': True,
        'mensagem': 'Sincronização iniciada em background',
        'status': estado_inicial
    }), 202


@app.route('/sync/status', methods=['GET'])
def sync_status():
    """Retorna o estado atual/recente da sincronização."""
    with sync_lock:
        estado = dict(sync_state)
    return jsonify({
        'sucesso': True,
        'status': estado
    })


@app.route('/sync/summary', methods=['GET'])
def sync_summary():
    """Compara totais Firebird x Supabase para monitoramento rápido."""
    conn = None
    try:
        conn = conectar_firebird()
        cursor = conn.cursor()

        tabelas = [
            {
                'nome': 'prime_clientes',
                'firebird': 'SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1 AND CODIGO < 500000',
                'supabase': 'prime_clientes'
            },
            {
                'nome': 'prime_pedidos',
                'firebird': 'SELECT COUNT(*) FROM ATENDIMENTO_A1 WHERE CODIGO_CLIENTE IS NOT NULL',
                'supabase': 'prime_pedidos'
            },
            {
                'nome': 'prime_formulas',
                'firebird': 'SELECT COUNT(*) FROM ATENDIMENTO_A2',
                'supabase': 'prime_formulas'
            },
            {
                'nome': 'prime_formulas_itens',
                'firebird': 'SELECT COUNT(*) FROM ATENDIMENTO_A3 WHERE CODIGO_ATEND_A1 IS NOT NULL',
                'supabase': 'prime_formulas_itens'
            },
            {
                'nome': 'prime_rastreabilidade',
                'firebird': 'SELECT COUNT(*) FROM PROCESSO_MANIPULACAO',
                'supabase': 'prime_rastreabilidade'
            },
            {
                'nome': 'prime_tipos_processo',
                'firebird': 'SELECT COUNT(*) FROM FORMAFARMACEUTICA_PROCESSO_TIPO',
                'supabase': 'prime_tipos_processo'
            }
        ]

        resultado_tabelas = []
        total_firebird = 0
        total_supabase = 0

        for tab in tabelas:
            cursor.execute(tab['firebird'])
            total_fb = cursor.fetchone()[0]
            total_sb = contar_supabase_registros(tab['supabase'])

            resultado_tabelas.append({
                'tabela': tab['nome'],
                'firebird': total_fb,
                'supabase': total_sb,
                'faltantes': total_fb - total_sb,
                'percentual': round((total_sb / total_fb * 100), 2) if total_fb else 100.0
            })

            total_firebird += total_fb
            total_supabase += total_sb

        return jsonify({
            'sucesso': True,
            'atualizado_em': datetime.now().isoformat(),
            'total_firebird': total_firebird,
            'total_supabase': total_supabase,
            'faltantes_totais': total_firebird - total_supabase,
            'percentual_geral': round((total_supabase / total_firebird * 100), 2) if total_firebird else 100.0,
            'tabelas': resultado_tabelas
        })

    except Exception as e:
        logger.error(f"❌ Erro ao gerar resumo de sincronização: {e}")
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

