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
print("CONTANDO ENDERECOS NO FIREBIRD")
print("="*80)

# Total de clientes ativos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
""")
total = cursor.fetchone()[0]

# Com endereço na tabela CADASTRO_ENDERECO
cursor.execute("""
    SELECT COUNT(DISTINCT CE.CODIGO_CADASTRO)
    FROM CADASTRO_ENDERECO CE
    INNER JOIN CLIENTE C ON C.CODIGO = CE.CODIGO_CADASTRO
    WHERE C.ATIVO = -1
    AND C.CODIGO < 500000
    AND CE.TIPO_CADASTRO = 1
    AND CE.ENDERECO IS NOT NULL
    AND TRIM(CE.ENDERECO) <> ''
""")
com_endereco = cursor.fetchone()[0]

sem_endereco = total - com_endereco

print(f"\nTotal de clientes ativos: {total:,}")
print(f"COM endereco: {com_endereco:,} ({com_endereco/total*100:.2f}%)")
print(f"SEM endereco: {sem_endereco:,} ({sem_endereco/total*100:.2f}%)")

# Exemplos
cursor.execute("""
    SELECT C.CODIGO, C.NOMECLIENTE, CE.ENDERECO, CE.NUMERO, CE.CEP
    FROM CADASTRO_ENDERECO CE
    INNER JOIN CLIENTE C ON C.CODIGO = CE.CODIGO_CADASTRO
    WHERE C.ATIVO = -1
    AND C.CODIGO < 500000
    AND CE.TIPO_CADASTRO = 1
    AND CE.ENDERECO IS NOT NULL
    ROWS 5
""")

print("\nExemplos de clientes COM endereco:")
for row in cursor.fetchall():
    end = str(row[2] or '')[:40]
    num = str(row[3] or '')
    cep = str(row[4] or '')
    print(f"   {row[0]}: {row[1][:25]} - {end}, {num} - CEP: {cep}")

conn.close()
print("="*80)


