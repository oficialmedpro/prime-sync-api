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
print("CONTANDO EMAILS NO FIREBIRD")
print("="*80)

# Total de clientes ativos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
""")
total = cursor.fetchone()[0]

# Com EMAIL1 preenchido
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND EMAIL1 IS NOT NULL
    AND TRIM(EMAIL1) <> ''
""")
com_email = cursor.fetchone()[0]

sem_email = total - com_email

print(f"\nTotal de clientes ativos: {total:,}")
print(f"COM email: {com_email:,} ({com_email/total*100:.2f}%)")
print(f"SEM email: {sem_email:,} ({sem_email/total*100:.2f}%)")

# Exemplos
cursor.execute("""
    SELECT CODIGO, NOMECLIENTE, EMAIL1
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND EMAIL1 IS NOT NULL
    AND TRIM(EMAIL1) <> ''
    ROWS 5
""")

print("\nExemplos de clientes COM email:")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1][:30]} - {row[2]}")

conn.close()
print("="*80)


