#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se COTACAO_PRODUTO tem nomes
"""

import fdb
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações do Firebird
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}

def conectar_firebird():
    """Conecta ao Firebird"""
    try:
        conn = fdb.connect(**FIREBIRD_CONFIG)
        logger.info("✅ Conexão com Firebird estabelecida!")
        return conn
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Firebird: {e}")
        return None

def testar_cotacao_produto():
    """Testa COTACAO_PRODUTO"""
    conn = conectar_firebird()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Ver estrutura da tabela
        logger.info("🔍 Verificando estrutura de COTACAO_PRODUTO...")
        cursor.execute("""
            SELECT RDB$FIELD_NAME
            FROM RDB$RELATION_FIELDS 
            WHERE RDB$RELATION_NAME = 'COTACAO_PRODUTO'
            ORDER BY RDB$FIELD_POSITION
        """)
        
        campos = cursor.fetchall()
        logger.info("📋 Campos encontrados:")
        for campo in campos:
            logger.info(f"  - {campo[0]}")
        
        # Testar alguns registros
        logger.info("\n🔍 Testando alguns registros...")
        cursor.execute("""
            SELECT *
            FROM COTACAO_PRODUTO
            WHERE CODIGO_PRODUTO IN (1000998, 1000314, 1000508, 1000187, 1000897)
            ORDER BY CODIGO_PRODUTO
        """)
        
        registros = cursor.fetchall()
        logger.info(f"📊 Encontrados {len(registros)} registros")
        
        for i, row in enumerate(registros, 1):
            logger.info(f"\n📝 Registro {i}:")
            for j, campo in enumerate(campos):
                logger.info(f"  - {campo[0]}: {row[j]}")
        
        # Testar JOIN com ATENDIMENTO_A3
        logger.info("\n🔍 Testando JOIN com ATENDIMENTO_A3...")
        cursor.execute("""
            SELECT
                A3.CODIGO_ATEND_A1,
                A3.NUMEROFORMULA,
                A3.NUMEROLINHA,
                A3.CODIGO_PRODUTO,
                CP.DESCRICAO_PRODUTO,
                A3.QUANTIDADE,
                A3.UNIDADE
            FROM ATENDIMENTO_A3 A3
            LEFT JOIN COTACAO_PRODUTO CP ON A3.CODIGO_PRODUTO = CP.CODIGO_PRODUTO
            WHERE A3.CODIGO_ATEND_A1 = 250400001
            ORDER BY A3.NUMEROLINHA
            ROWS 5
        """)
        
        registros_join = cursor.fetchall()
        logger.info(f"📊 Encontrados {len(registros_join)} registros com JOIN")
        
        for i, row in enumerate(registros_join, 1):
            logger.info(f"\n📝 Registro com JOIN {i}:")
            logger.info(f"  - CODIGO_ATEND_A1: {row[0]}")
            logger.info(f"  - NUMEROFORMULA: {row[1]}")
            logger.info(f"  - NUMEROLINHA: {row[2]}")
            logger.info(f"  - CODIGO_PRODUTO: {row[3]}")
            logger.info(f"  - DESCRICAO_PRODUTO: '{row[4]}'")
            logger.info(f"  - QUANTIDADE: {row[5]}")
            logger.info(f"  - UNIDADE: {row[6]}")
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    testar_cotacao_produto()



