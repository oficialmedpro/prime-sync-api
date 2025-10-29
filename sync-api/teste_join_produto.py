#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se o JOIN com PRODUTO está funcionando
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

def testar_join_produto():
    """Testa o JOIN com a tabela PRODUTO"""
    conn = conectar_firebird()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Testar o JOIN que a API usa agora
        logger.info("🔍 Testando JOIN com tabela PRODUTO...")
        cursor.execute("""
            SELECT
                A3.CODIGO_ATEND_A1,
                A3.NUMEROFORMULA,
                A3.NUMEROLINHA,
                A3.CODIGO_PRODUTO,
                P.NOME_PRODUTO,
                A3.QUANTIDADE,
                A3.UNIDADE,
                A3.VALORCUSTO,
                A3.VALORVENDA,
                A3.OBSERVACAO
            FROM ATENDIMENTO_A3 A3
            LEFT JOIN PRODUTO P ON A3.CODIGO_PRODUTO = P.CODIGO
            WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
            ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
            ROWS 10
        """)
        
        registros = cursor.fetchall()
        logger.info(f"📊 Encontrados {len(registros)} registros com JOIN")
        
        for i, row in enumerate(registros, 1):
            logger.info(f"\n📝 Registro {i}:")
            logger.info(f"  - CODIGO_ATEND_A1: {row[0]}")
            logger.info(f"  - NUMEROFORMULA: {row[1]}")
            logger.info(f"  - NUMEROLINHA: {row[2]}")
            logger.info(f"  - CODIGO_PRODUTO: {row[3]}")
            logger.info(f"  - NOME_PRODUTO: '{row[4]}'")
            logger.info(f"  - QUANTIDADE: {row[5]}")
            logger.info(f"  - UNIDADE: {row[6]}")
            logger.info(f"  - VALORCUSTO: {row[7]}")
            logger.info(f"  - VALORVENDA: {row[8]}")
            logger.info(f"  - OBSERVACAO: {row[9]}")
        
        # Contar quantos têm nome de produto
        cursor.execute("""
            SELECT COUNT(*)
            FROM ATENDIMENTO_A3 A3
            LEFT JOIN PRODUTO P ON A3.CODIGO_PRODUTO = P.CODIGO
            WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
            AND P.NOME_PRODUTO IS NOT NULL
        """)
        
        com_nome = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM ATENDIMENTO_A3 A3
            WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
        """)
        
        total = cursor.fetchone()[0]
        
        logger.info(f"\n📊 Estatísticas:")
        logger.info(f"  - Total de itens: {total}")
        logger.info(f"  - Com nome de produto: {com_nome}")
        logger.info(f"  - Sem nome de produto: {total - com_nome}")
        logger.info(f"  - Percentual com nome: {(com_nome/total)*100:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    testar_join_produto()



