#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se alguma tabela tem nomes de produtos
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

def testar_tabelas_produto():
    """Testa tabelas que podem ter produtos"""
    conn = conectar_firebird()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Testar BI_PRODUTOS
        logger.info("🔍 Testando BI_PRODUTOS...")
        try:
            cursor.execute("SELECT COUNT(*) FROM BI_PRODUTOS")
            count = cursor.fetchone()[0]
            logger.info(f"✅ BI_PRODUTOS tem {count} registros")
            
            # Ver estrutura
            cursor.execute("SELECT FIRST 1 * FROM BI_PRODUTOS")
            row = cursor.fetchone()
            if row:
                logger.info(f"📋 Primeiro registro: {row}")
        except Exception as e:
            logger.error(f"❌ Erro em BI_PRODUTOS: {e}")
        
        # Testar COTACAO_PRODUTO
        logger.info("\n🔍 Testando COTACAO_PRODUTO...")
        try:
            cursor.execute("SELECT COUNT(*) FROM COTACAO_PRODUTO")
            count = cursor.fetchone()[0]
            logger.info(f"✅ COTACAO_PRODUTO tem {count} registros")
            
            # Ver estrutura
            cursor.execute("SELECT FIRST 1 * FROM COTACAO_PRODUTO")
            row = cursor.fetchone()
            if row:
                logger.info(f"📋 Primeiro registro: {row}")
        except Exception as e:
            logger.error(f"❌ Erro em COTACAO_PRODUTO: {e}")
        
        # Vamos ver se existe alguma tabela com CODIGO e NOME
        logger.info("\n🔍 Buscando tabelas com campos CODIGO e NOME...")
        cursor.execute("""
            SELECT RDB$RELATION_NAME, RDB$FIELD_NAME
            FROM RDB$RELATION_FIELDS RF1
            INNER JOIN RDB$RELATION_FIELDS RF2 ON RF1.RDB$RELATION_NAME = RF2.RDB$RELATION_NAME
            WHERE RF1.RDB$FIELD_NAME = 'CODIGO'
            AND RF2.RDB$FIELD_NAME = 'NOME'
            AND RF1.RDB$RELATION_NAME NOT LIKE 'RDB$%'
            ORDER BY RF1.RDB$RELATION_NAME
        """)
        
        tabelas_codigo_nome = cursor.fetchall()
        logger.info("📋 Tabelas com CODIGO e NOME:")
        for tabela in tabelas_codigo_nome[:10]:  # Mostrar só as primeiras 10
            logger.info(f"  - {tabela[0]}")
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    testar_tabelas_produto()
