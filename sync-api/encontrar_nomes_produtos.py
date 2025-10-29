#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para encontrar onde estão os nomes dos produtos
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

def encontrar_nomes_produtos():
    """Encontra onde estão os nomes dos produtos"""
    conn = conectar_firebird()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Vamos ver se existe alguma tabela com DESCRICAO
        logger.info("🔍 Buscando tabelas com campo DESCRICAO...")
        cursor.execute("""
            SELECT DISTINCT RDB$RELATION_NAME
            FROM RDB$RELATION_FIELDS 
            WHERE RDB$FIELD_NAME = 'DESCRICAO'
            AND RDB$RELATION_NAME NOT LIKE 'RDB$%'
            ORDER BY RDB$RELATION_NAME
        """)
        
        tabelas_descricao = cursor.fetchall()
        logger.info("📋 Tabelas com campo DESCRICAO:")
        for tabela in tabelas_descricao:
            logger.info(f"  - {tabela[0]}")
        
        # Vamos ver se existe alguma tabela com NOME
        logger.info("\n🔍 Buscando tabelas com campo NOME...")
        cursor.execute("""
            SELECT DISTINCT RDB$RELATION_NAME
            FROM RDB$RELATION_FIELDS 
            WHERE RDB$FIELD_NAME = 'NOME'
            AND RDB$RELATION_NAME NOT LIKE 'RDB$%'
            ORDER BY RDB$RELATION_NAME
        """)
        
        tabelas_nome = cursor.fetchall()
        logger.info("📋 Tabelas com campo NOME:")
        for tabela in tabelas_nome:
            logger.info(f"  - {tabela[0]}")
        
        # Vamos ver se existe alguma tabela com CODIGO e DESCRICAO
        logger.info("\n🔍 Buscando tabelas com CODIGO e DESCRICAO...")
        cursor.execute("""
            SELECT DISTINCT RF1.RDB$RELATION_NAME
            FROM RDB$RELATION_FIELDS RF1
            INNER JOIN RDB$RELATION_FIELDS RF2 ON RF1.RDB$RELATION_NAME = RF2.RDB$RELATION_NAME
            WHERE RF1.RDB$FIELD_NAME = 'CODIGO'
            AND RF2.RDB$FIELD_NAME = 'DESCRICAO'
            AND RF1.RDB$RELATION_NAME NOT LIKE 'RDB$%'
            ORDER BY RF1.RDB$RELATION_NAME
        """)
        
        tabelas_codigo_descricao = cursor.fetchall()
        logger.info("📋 Tabelas com CODIGO e DESCRICAO:")
        for tabela in tabelas_codigo_descricao:
            logger.info(f"  - {tabela[0]}")
        
        # Vamos testar algumas tabelas que podem ter produtos
        tabelas_teste = ['MATERIA_PRIMA', 'INGREDIENTE', 'ITEM', 'PRODUTO', 'PRODUTOS']
        
        for tabela in tabelas_teste:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Tabela {tabela} existe com {count} registros")
                
                # Ver estrutura
                cursor.execute(f"SELECT FIRST 1 * FROM {tabela}")
                row = cursor.fetchone()
                if row:
                    logger.info(f"📋 Primeiro registro: {row}")
            except:
                logger.info(f"❌ Tabela {tabela} não existe")
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    encontrar_nomes_produtos()


