#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para encontrar a tabela de produtos correta
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

def encontrar_tabela_produtos():
    """Encontra a tabela de produtos correta"""
    conn = conectar_firebird()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Buscar tabelas que podem conter produtos
        logger.info("🔍 Buscando tabelas relacionadas a produtos...")
        cursor.execute("""
            SELECT RDB$RELATION_NAME
            FROM RDB$RELATIONS
            WHERE RDB$RELATION_TYPE = 0
            AND RDB$RELATION_NAME LIKE '%PROD%'
            ORDER BY RDB$RELATION_NAME
        """)
        
        tabelas_produto = cursor.fetchall()
        logger.info("📋 Tabelas encontradas com 'PROD':")
        for tabela in tabelas_produto:
            logger.info(f"  - {tabela[0]}")
        
        # Buscar tabelas que podem conter itens/ingredientes
        logger.info("\n🔍 Buscando tabelas relacionadas a itens/ingredientes...")
        cursor.execute("""
            SELECT RDB$RELATION_NAME
            FROM RDB$RELATIONS
            WHERE RDB$RELATION_TYPE = 0
            AND (RDB$RELATION_NAME LIKE '%ITEM%' 
                 OR RDB$RELATION_NAME LIKE '%INGRED%'
                 OR RDB$RELATION_NAME LIKE '%MATERIA%')
            ORDER BY RDB$RELATION_NAME
        """)
        
        tabelas_item = cursor.fetchall()
        logger.info("📋 Tabelas encontradas com 'ITEM/INGRED/MATERIA':")
        for tabela in tabelas_item:
            logger.info(f"  - {tabela[0]}")
        
        # Testar algumas tabelas comuns
        tabelas_teste = ['PRODUTO', 'PRODUTOS', 'ITEM', 'ITENS', 'MATERIA_PRIMA', 'INGREDIENTE']
        
        for tabela in tabelas_teste:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Tabela {tabela} existe com {count} registros")
            except:
                logger.info(f"❌ Tabela {tabela} não existe")
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    encontrar_tabela_produtos()
