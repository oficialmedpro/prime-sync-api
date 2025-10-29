#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para encontrar tabelas de estoque com nomes de produtos
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

def encontrar_estoques():
    """Encontra tabelas de estoque com nomes de produtos"""
    conn = conectar_firebird()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Buscar tabelas com ESTOQUE
        logger.info("🔍 Buscando tabelas com ESTOQUE...")
        cursor.execute("""
            SELECT RDB$RELATION_NAME
            FROM RDB$RELATIONS
            WHERE RDB$RELATION_TYPE = 0
            AND RDB$RELATION_NAME LIKE '%ESTOQUE%'
            ORDER BY RDB$RELATION_NAME
        """)
        
        tabelas_estoque = cursor.fetchall()
        logger.info("📋 Tabelas encontradas com ESTOQUE:")
        for tabela in tabelas_estoque:
            logger.info(f"  - {tabela[0]}")
        
        # Testar algumas tabelas de estoque importantes
        tabelas_teste = ['ESTOQUE_GERAL', 'ESTOQUE_GERAL_NUTR', 'ESTOQUE_GERAL_PRECOS']
        
        for tabela in tabelas_teste:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Tabela {tabela} existe com {count} registros")
                
                # Ver estrutura
                cursor.execute(f"""
                    SELECT RDB$FIELD_NAME
                    FROM RDB$RELATION_FIELDS 
                    WHERE RDB$RELATION_NAME = '{tabela}'
                    ORDER BY RDB$FIELD_POSITION
                """)
                
                campos = cursor.fetchall()
                logger.info(f"📋 Campos de {tabela}:")
                for campo in campos:
                    logger.info(f"  - {campo[0]}")
                
                # Ver alguns registros
                cursor.execute(f"SELECT FIRST 3 * FROM {tabela}")
                registros = cursor.fetchall()
                logger.info(f"📋 Primeiros registros de {tabela}:")
                for i, row in enumerate(registros, 1):
                    logger.info(f"  Registro {i}: {row}")
                
            except Exception as e:
                logger.error(f"❌ Erro em {tabela}: {e}")
        
        # Buscar tabelas que podem ter CODIGO e DESCRICAO/NOME
        logger.info("\n🔍 Buscando tabelas que podem ter produtos...")
        cursor.execute("""
            SELECT DISTINCT RF1.RDB$RELATION_NAME
            FROM RDB$RELATION_FIELDS RF1
            INNER JOIN RDB$RELATION_FIELDS RF2 ON RF1.RDB$RELATION_NAME = RF2.RDB$RELATION_NAME
            WHERE RF1.RDB$FIELD_NAME = 'CODIGO'
            AND (RF2.RDB$FIELD_NAME = 'DESCRICAO' OR RF2.RDB$FIELD_NAME = 'NOME')
            AND RF1.RDB$RELATION_NAME NOT LIKE 'RDB$%'
            AND RF1.RDB$RELATION_NAME NOT LIKE 'APP_%'
            AND RF1.RDB$RELATION_NAME NOT LIKE 'OC_%'
            AND RF1.RDB$RELATION_NAME NOT LIKE 'ISO_%'
            AND RF1.RDB$RELATION_NAME NOT LIKE 'SPS_%'
            AND RF1.RDB$RELATION_NAME NOT LIKE 'WEB_%'
            ORDER BY RF1.RDB$RELATION_NAME
        """)
        
        tabelas_codigo_descricao = cursor.fetchall()
        logger.info("📋 Tabelas com CODIGO e DESCRICAO/NOME (filtradas):")
        for tabela in tabelas_codigo_descricao:
            logger.info(f"  - {tabela[0]}")
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    encontrar_estoques()


