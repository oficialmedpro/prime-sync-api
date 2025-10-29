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
print("CLIENTES COM DATA DE NASCIMENTO INVALIDA (ANO <= 1900)")
print("="*80)

cursor.execute("""
    SELECT 
        C.CODIGO,
        C.NOMECLIENTE,
        C.DIANASCIMENTO,
        C.MESNASCIMENTO,
        C.ANONASCIMENTO
    FROM CLIENTE C
    WHERE C.ATIVO = -1
    AND C.CODIGO < 500000
    AND C.DIANASCIMENTO IS NOT NULL
    AND C.MESNASCIMENTO IS NOT NULL
    AND C.ANONASCIMENTO IS NOT NULL
    AND C.ANONASCIMENTO <= 1900
    ROWS 10
""")

print("\nCodigo | Nome                              | Dia | Mes | Ano")
print("-"*80)

for row in cursor.fetchall():
    codigo = row[0]
    nome = row[1][:35] if row[1] else "SEM NOME"
    dia = row[2] if row[2] else 0
    mes = row[3] if row[3] else 0
    ano = row[4] if row[4] else 0
    
    print(f"{codigo:6} | {nome:35} | {dia:3} | {mes:3} | {ano:4}")

conn.close()

print("="*80)
print("Esses clientes tem anos <= 1900 (provavelmente dados placeholder ou erro)")
print("="*80)



