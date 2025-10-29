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
print("CONTANDO CPF/CNPJ NO FIREBIRD")
print("="*80)

# Total de clientes ativos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
""")
total = cursor.fetchone()[0]

# Com CPF/CNPJ preenchido
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND CPF_CNPJ IS NOT NULL
    AND TRIM(CPF_CNPJ) <> ''
""")
com_cpf = cursor.fetchone()[0]

sem_cpf = total - com_cpf

print(f"\nTotal de clientes ativos: {total:,}")
print(f"COM CPF/CNPJ: {com_cpf:,} ({com_cpf/total*100:.2f}%)")
print(f"SEM CPF/CNPJ: {sem_cpf:,} ({sem_cpf/total*100:.2f}%)")

# Exemplos
cursor.execute("""
    SELECT CODIGO, NOMECLIENTE, CPF_CNPJ
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND CPF_CNPJ IS NOT NULL
    AND TRIM(CPF_CNPJ) <> ''
    ROWS 5
""")

print("\nExemplos de clientes COM CPF/CNPJ:")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1][:30]} - {row[2]}")

conn.close()
print("="*80)



