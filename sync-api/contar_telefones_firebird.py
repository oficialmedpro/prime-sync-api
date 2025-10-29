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
print("CONTANDO TELEFONES NO FIREBIRD")
print("="*80)

# Total de clientes ativos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
""")
total = cursor.fetchone()[0]

# Com telefone na tabela CADASTRO_TELEFONE
cursor.execute("""
    SELECT COUNT(DISTINCT CT.CODIGO_CADASTRO)
    FROM CADASTRO_TELEFONE CT
    INNER JOIN CLIENTE C ON C.CODIGO = CT.CODIGO_CADASTRO
    WHERE C.ATIVO = -1
    AND C.CODIGO < 500000
    AND CT.TIPO_CADASTRO = 1
    AND CT.TELEFONE IS NOT NULL
    AND TRIM(CT.TELEFONE) <> ''
""")
com_telefone = cursor.fetchone()[0]

sem_telefone = total - com_telefone

print(f"\nTotal de clientes ativos: {total:,}")
print(f"COM telefone: {com_telefone:,} ({com_telefone/total*100:.2f}%)")
print(f"SEM telefone: {sem_telefone:,} ({sem_telefone/total*100:.2f}%)")

# Exemplos
cursor.execute("""
    SELECT C.CODIGO, C.NOMECLIENTE, CT.TELEFONEPREFIXO, CT.TELEFONE
    FROM CADASTRO_TELEFONE CT
    INNER JOIN CLIENTE C ON C.CODIGO = CT.CODIGO_CADASTRO
    WHERE C.ATIVO = -1
    AND C.CODIGO < 500000
    AND CT.TIPO_CADASTRO = 1
    AND CT.TELEFONE IS NOT NULL
    ROWS 5
""")

print("\nExemplos de clientes COM telefone:")
for row in cursor.fetchall():
    prefixo = str(row[2] or '')
    numero = str(row[3] or '')
    tel = (prefixo + numero).strip()
    print(f"   {row[0]}: {row[1][:30]} - {tel}")

conn.close()
print("="*80)


