#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar dados da tabela ATENDIMENTO_A3
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

def testar_atendimento_a3():
    """Testa consulta na tabela ATENDIMENTO_A3"""
    conn = conectar_firebird()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Testar a consulta que a API usa
        logger.info("🔍 Testando consulta da API...")
        cursor.execute("""
            SELECT
                A3.CODIGO_ATEND_A1,
                A3.NUMEROFORMULA,
                A3.NUMEROLINHA,
                A3.QUANTIDADE,
                A3.UNIDADE,
                A3.VALORCUSTO,
                A3.VALORVENDA,
                A3.OBSERVACAO
            FROM ATENDIMENTO_A3 A3
            WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
            ROWS 10
        """)
        
        registros = cursor.fetchall()
        logger.info(f"📊 Encontrados {len(registros)} registros de teste")
        
        for i, row in enumerate(registros, 1):
            logger.info(f"\n📝 Registro {i}:")
            logger.info(f"  - CODIGO_ATEND_A1: {row[0]}")
            logger.info(f"  - NUMEROFORMULA: {row[1]}")
            logger.info(f"  - NUMEROLINHA: {row[2]}")
            logger.info(f"  - QUANTIDADE: {row[3]}")
            logger.info(f"  - UNIDADE: {row[4]}")
            logger.info(f"  - VALORCUSTO: {row[5]}")
            logger.info(f"  - VALORVENDA: {row[6]}")
            logger.info(f"  - OBSERVACAO: {row[7]}")
        
        # Vamos verificar se existem campos de produto
        logger.info("\n🔍 Verificando se existem campos de produto...")
        try:
            cursor.execute("""
                SELECT
                    A3.CODIGO_ATEND_A1,
                    A3.NUMEROFORMULA,
                    A3.NUMEROLINHA,
                    A3.CODIGO_PRODUTO,
                    A3.NOME_PRODUTO,
                    A3.QUANTIDADE,
                    A3.UNIDADE
                FROM ATENDIMENTO_A3 A3
                WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
                ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
                ROWS 5
            """)
            
            registros_produto = cursor.fetchall()
            logger.info(f"📊 Encontrados {len(registros_produto)} registros com campos de produto")
            
            for i, row in enumerate(registros_produto, 1):
                logger.info(f"\n📝 Registro com produto {i}:")
                logger.info(f"  - CODIGO_ATEND_A1: {row[0]}")
                logger.info(f"  - NUMEROFORMULA: {row[1]}")
                logger.info(f"  - NUMEROLINHA: {row[2]}")
                logger.info(f"  - CODIGO_PRODUTO: {row[3]}")
                logger.info(f"  - NOME_PRODUTO: {row[4]}")
                logger.info(f"  - QUANTIDADE: {row[5]}")
                logger.info(f"  - UNIDADE: {row[6]}")
                
        except Exception as e:
            logger.warning(f"⚠️ Campos de produto não existem: {e}")
        
        # Contar total de registros
        cursor.execute("SELECT COUNT(*) FROM ATENDIMENTO_A3 WHERE CODIGO_ATEND_A1 IS NOT NULL")
        total = cursor.fetchone()[0]
        logger.info(f"\n📊 Total de registros em ATENDIMENTO_A3: {total}")
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    testar_atendimento_a3()
