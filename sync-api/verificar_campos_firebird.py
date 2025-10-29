#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar TODOS os campos da tabela ATENDIMENTO_A1 no Firebird
Data: 27/10/2025
"""

import fdb
import os

FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or 'Lt-@=waIh))Ql3~'

print("="*80)
print("VERIFICANDO TODOS OS CAMPOS DA TABELA ATENDIMENTO_A1")
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
    
    print("\nConsultando campos da tabela ATENDIMENTO_A1...")
    
    # Query para listar TODOS os campos
    cursor.execute("""
        SELECT FIRST 1 * FROM ATENDIMENTO_A1
    """)
    
    # Pegar descrição dos campos
    descricao = cursor.description
    
    print("\n" + "="*80)
    print("CAMPOS DISPONIVEIS na tabela ATENDIMENTO_A1:")
    print("="*80)
    
    for i, campo in enumerate(descricao, 1):
        nome = campo[0]
        print(f"{i:2}. {nome}")
    
    # Buscar um registro para ver valores de exemplo
    print("\n" + "="*80)
    print("REGISTRO DE EXEMPLO:")
    print("="*80)
    
    cursor.execute("""
        SELECT FIRST 1 * FROM ATENDIMENTO_A1
        ORDER BY CODIGO DESC
    """)
    
    colunas = [desc[0] for desc in cursor.description]
    valores = cursor.fetchone()
    
    if valores:
        for coluna, valor in zip(colunas, valores):
            if valor is not None:
                print(f"{coluna:<30} = {valor}")
    
    # Verificar campos de DATA especificamente
    print("\n" + "="*80)
    print("CAMPOS QUE PODEM SER DATA DE CRIACAO:")
    print("="*80)
    
    campos_data = []
    for i, campo in enumerate(descricao):
        nome = campo[0].upper()
        valor = valores[i] if valores else None
        
        # Procurar por campos relacionados a data/criacao
        if ('DATA' in nome or 'DATE' in nome or 'CRIACAO' in nome or 'CADASTRO' in nome or 'CREATED' in nome or 'PEDIDO' in nome):
            campos_data.append((campo[0], valor))
    
    if campos_data:
        print("\nCandidatos encontrados:")
        for nome, valor in campos_data:
            print(f"  -> {nome:<30} = {valor}")
    else:
        print("\nNenhum campo obvio de data encontrado")
        print("Listando todos os campos para inspecao manual:")
        for campo in descricao:
            print(f"  - {campo[0]}")
    
    conn.close()
    
    # Recomendacao
    print("\n" + "="*80)
    print("RECOMENDACAO:")
    print("="*80)
    print("\nProcure no Firebird qual campo representa a DATA DE CRIACAO")
    print("Provavelmente e um destes:")
    print("  - DATA_PEDIDO")
    print("  - DATA_CADASTRO") 
    print("  - DT_CRIACAO")
    print("  - CREATED_AT")
    print("  - DATA")
    print("\nDepois, adicione esse campo na query SELECT e mapeie para 'data_criacao'")
    
except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n")



