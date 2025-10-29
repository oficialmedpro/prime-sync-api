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
print("VERIFICACAO DETALHADA - DATAS DE NASCIMENTO NO FIREBIRD")
print("="*80)

# 1. Total de clientes ativos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
""")
total = cursor.fetchone()[0]
print(f"\n1. Total de clientes ativos: {total:,}")

# 2. Clientes com TODOS os campos preenchidos
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND DIANASCIMENTO IS NOT NULL
    AND MESNASCIMENTO IS NOT NULL
    AND ANONASCIMENTO IS NOT NULL
""")
todos_campos = cursor.fetchone()[0]
print(f"2. Com TODOS os campos (DIA, MES, ANO): {todos_campos:,}")

# 3. Clientes com PELO MENOS UM campo preenchido
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND (DIANASCIMENTO IS NOT NULL
         OR MESNASCIMENTO IS NOT NULL
         OR ANONASCIMENTO IS NOT NULL)
""")
algum_campo = cursor.fetchone()[0]
print(f"3. Com PELO MENOS UM campo preenchido: {algum_campo:,}")

# 4. Clientes com data VÁLIDA (ano > 1900)
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND DIANASCIMENTO IS NOT NULL
    AND MESNASCIMENTO IS NOT NULL
    AND ANONASCIMENTO IS NOT NULL
    AND ANONASCIMENTO > 1900
""")
datas_validas = cursor.fetchone()[0]
print(f"4. Com data VÁLIDA (ano > 1900): {datas_validas:,}")

# 5. Mostrar alguns exemplos
cursor.execute("""
    SELECT CODIGO, NOMECLIENTE, DIANASCIMENTO, MESNASCIMENTO, ANONASCIMENTO
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND DIANASCIMENTO IS NOT NULL
    AND MESNASCIMENTO IS NOT NULL
    AND ANONASCIMENTO IS NOT NULL
    AND ANONASCIMENTO > 1900
    ROWS 10
""")

print(f"\n5. Exemplos de clientes COM data válida:")
for row in cursor.fetchall():
    try:
        data = f"{int(row[4])}-{int(row[3]):02d}-{int(row[2]):02d}"
        print(f"   {row[0]}: {row[1]} → {data}")
    except:
        print(f"   {row[0]}: {row[1]} → ERRO AO FORMATAR")

# 6. Verificar se há algum com ano = 0 ou inválido
cursor.execute("""
    SELECT COUNT(*) 
    FROM CLIENTE 
    WHERE ATIVO = -1
    AND CODIGO < 500000
    AND DIANASCIMENTO IS NOT NULL
    AND MESNASCIMENTO IS NOT NULL
    AND ANONASCIMENTO IS NOT NULL
    AND ANONASCIMENTO <= 1900
""")
datas_invalidas = cursor.fetchone()[0]
print(f"\n6. Com data INVÁLIDA (ano <= 1900): {datas_invalidas:,}")

conn.close()

print("\n" + "="*80)
print("CONCLUSAO:")
print("="*80)
print(f"A contagem CORRETA deve ser: {datas_validas:,} clientes")
print("(Considerando apenas datas válidas com ano > 1900)")
print("="*80)


