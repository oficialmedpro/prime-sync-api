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
print("CONTANDO SEXO NO FIREBIRD")
print("="*80)

# Total de clientes ativos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
""")
total = cursor.fetchone()[0]

# Com sexo preenchido
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND SEXO IS NOT NULL
    AND TRIM(SEXO) <> ''
""")
com_sexo = cursor.fetchone()[0]

# Distribuição
cursor.execute("""
    SELECT SEXO, COUNT(*) as qtd
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND SEXO IS NOT NULL
    AND TRIM(SEXO) <> ''
    GROUP BY SEXO
    ORDER BY qtd DESC
""")

sem_sexo = total - com_sexo

print(f"\nTotal de clientes ativos: {total:,}")
print(f"COM sexo: {com_sexo:,} ({com_sexo/total*100:.2f}%)")
print(f"SEM sexo: {sem_sexo:,} ({sem_sexo/total*100:.2f}%)")

print("\nDistribuicao por sexo:")
for row in cursor.fetchall():
    sexo_raw = row[0]
    if isinstance(sexo_raw, int):
        sexo = str(sexo_raw)
    elif sexo_raw:
        sexo = str(sexo_raw).strip()
    else:
        sexo = "VAZIO"
    qtd = row[1]
    print(f"   {sexo}: {qtd:,} ({qtd/com_sexo*100:.2f}% dos que tem)")

conn.close()
print("="*80)

