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
print("INVESTIGANDO CLIENTE 32126 (VALERIA)")
print("="*80)

cursor.execute("""
    SELECT 
        CODIGO,
        NOMECLIENTE,
        SEXO,
        CPF_CNPJ,
        EMAIL1,
        DIANASCIMENTO,
        MESNASCIMENTO,
        ANONASCIMENTO
    FROM CLIENTE
    WHERE CODIGO = 32126
""")

row = cursor.fetchone()
if row:
    print(f"\nCodigo: {row[0]}")
    print(f"Nome: {row[1]}")
    print(f"Sexo: {row[2]} (tipo: {type(row[2])})")
    print(f"CPF: {row[3]}")
    print(f"Email: {row[4]}")
    print(f"Data Nasc: {row[5]}/{row[6]}/{row[7]}")
else:
    print("Cliente nao encontrado!")

conn.close()
print("="*80)


