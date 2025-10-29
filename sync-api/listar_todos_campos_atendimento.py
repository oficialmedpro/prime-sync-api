#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Listar TODOS os campos de ATENDIMENTO_A1 usando metadata do Firebird
Data: 27/10/2025
"""

import fdb
import os

FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or 'Lt-@=waIh))Ql3~'

print("="*80)
print("LISTANDO TODOS OS CAMPOS DA TABELA ATENDIMENTO_A1")
print("="*80)

try:
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    
    cursor = conn.cursor()
    
    # Query metadata do Firebird para listar campos
    cursor.execute("""
        SELECT 
            RF.RDB$FIELD_NAME,
            RF.RDB$FIELD_POSITION
        FROM RDB$RELATION_FIELDS RF
        WHERE RF.RDB$RELATION_NAME = 'ATENDIMENTO_A1'
        ORDER BY RF.RDB$FIELD_POSITION
    """)
    
    campos = cursor.fetchall()
    
    print(f"\nTotal de campos encontrados: {len(campos)}\n")
    print(f"{'#':<5} {'NOME DO CAMPO':<40} {'POSIÇÃO'}")
    print("-"*80)
    
    for i, (nome, pos) in enumerate(campos, 1):
        nome_limpo = nome.strip()
        print(f"{i:<5} {nome_limpo:<40} {pos}")
    
    # Filtrar apenas campos com DATA, DT, HORA no nome
    print("\n" + "="*80)
    print("CAMPOS RELACIONADOS A DATA/HORA:")
    print("="*80)
    
    campos_data = []
    for nome, pos in campos:
        nome_limpo = nome.strip().upper()
        if any(palavra in nome_limpo for palavra in ['DATA', 'DT', 'HORA', 'DATE', 'TIME']):
            campos_data.append(nome_limpo)
            print(f"  -> {nome_limpo}")
    
    if not campos_data:
        print("  Nenhum campo relacionado a data encontrado")
    
    # Testar valores de um registro
    print("\n" + "="*80)
    print("EXEMPLO DE REGISTRO (campos de data):")
    print("="*80)
    
    if campos_data:
        select_campos = ", ".join(campos_data)
        cursor.execute(f"""
            SELECT {select_campos}
            FROM ATENDIMENTO_A1
            WHERE CODIGO_CLIENTE IS NOT NULL
            ORDER BY CODIGO DESC
            ROWS 1
        """)
        
        valores = cursor.fetchone()
        if valores:
            for campo, valor in zip(campos_data, valores):
                print(f"  {campo:<30} = {valor}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("ANÁLISE:")
    print("="*80)
    print("\nProcure por campos que podem ser a data de CRIAÇÃO:")
    print("  - Campos com _DT, DATA, ou DT_ no início")
    print("  - Campo que sempre tem valor (mesmo pedidos não aprovados)")
    print("  - Campo com data ANTERIOR a AVIADA_DT")
    
except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n")




