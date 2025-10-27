#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar a estrutura da tabela FORMAFARMACEUTICA_PROCESSO_TIPO
"""

import fdb
import os

# Configurações
FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS', 'Lt-@=waIh))Ql3~')

try:
    print("Conectando ao Firebird...")
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )

    cursor = conn.cursor()

    # Verificar colunas da tabela
    print("\nVerificando estrutura da tabela FORMAFARMACEUTICA_PROCESSO_TIPO:")
    cursor.execute("""
        SELECT
            RDB$FIELD_NAME as CAMPO
        FROM RDB$RELATION_FIELDS
        WHERE RDB$RELATION_NAME = 'FORMAFARMACEUTICA_PROCESSO_TIPO'
        ORDER BY RDB$FIELD_POSITION
    """)

    print("\nColunas disponiveis:")
    for row in cursor.fetchall():
        print(f"  - {row[0].strip()}")

    # Tentar buscar 1 registro
    print("\nBuscando 1 registro de exemplo:")
    cursor.execute("""
        SELECT FIRST 1 *
        FROM FORMAFARMACEUTICA_PROCESSO_TIPO
    """)

    resultado = cursor.fetchone()
    if resultado:
        print(f"Registro encontrado: {len(resultado)} colunas")
        print(f"Valores: {resultado}")
    else:
        print("Tabela vazia")

    conn.close()
    print("\nVerificacao concluida!")

except Exception as e:
    print(f"\nErro: {e}")
