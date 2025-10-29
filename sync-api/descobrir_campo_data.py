#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descobrir qual campo contem a data de criacao do pedido
Data: 27/10/2025
"""

import fdb
import os

FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or 'Lt-@=waIh))Ql3~'

print("="*80)
print("DESCOBRINDO CAMPO DE DATA DE CRIACAO")
print("="*80)

# Possíveis nomes de campos de data
campos_testar = [
    'DATA_PEDIDO',
    'DATA_CRIACAO',
    'DATA_CADASTRO',
    'DT_CRIACAO',
    'DT_PEDIDO',
    'DT_CADASTRO',
    'DATACAD',
    'CREATED_AT',
    'CREATED_DATE',
    'DATAATEND',
    'DATA_ATEND',
    'DATA_ATENDIMENTO',
    'DATAABERTURA',
    'DATA_ABERTURA'
]

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)

cursor = conn.cursor()

print("\nTestando campos possíveis...\n")

campos_encontrados = []

for campo in campos_testar:
    try:
        cursor.execute(f"""
            SELECT FIRST 1 {campo}
            FROM ATENDIMENTO_A1
            WHERE {campo} IS NOT NULL
        """)
        valor = cursor.fetchone()
        if valor:
            campos_encontrados.append((campo, valor[0]))
            print(f"  OK  {campo:<25} = {valor[0]}")
    except Exception as e:
        print(f"  --  {campo:<25} (nao existe)")

conn.close()

print("\n" + "="*80)
print("RESULTADO")
print("="*80)

if campos_encontrados:
    print("\nCAMPOS ENCONTRADOS:")
    for campo, valor in campos_encontrados:
        print(f"  -> {campo:<25} = {valor}")
    
    print("\n" + "="*80)
    print("USE ESTE CAMPO NA QUERY:")
    print("="*80)
    print(f"\nA.{campos_encontrados[0][0]},  -- data_criacao")
else:
    print("\nNENHUM campo de data encontrado com esses nomes")
    print("O campo pode ter outro nome ou nao existir")

print("\n")



