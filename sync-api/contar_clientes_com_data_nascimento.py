#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import fdb

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

print("="*80)
print("CONTANDO CLIENTES COM DATA DE NASCIMENTO NO FIREBIRD")
print("="*80)

# Total de clientes ativos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
""")
total_clientes = cursor.fetchone()[0]

# Clientes COM data de nascimento completa
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND DIANASCIMENTO IS NOT NULL
    AND MESNASCIMENTO IS NOT NULL
    AND ANONASCIMENTO IS NOT NULL
""")
com_data = cursor.fetchone()[0]

# Clientes SEM data de nascimento
sem_data = total_clientes - com_data

conn.close()

print(f"\nTotal de clientes ativos: {total_clientes:,}")
print(f"COM data de nascimento: {com_data:,} ({com_data/total_clientes*100:.2f}%)")
print(f"SEM data de nascimento: {sem_data:,} ({sem_data/total_clientes*100:.2f}%)")
print("="*80)



