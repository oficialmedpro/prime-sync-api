#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar quais campos existem no Firebird mas não estão sendo sincronizados
Data: 27/10/2025
"""

import fdb
import os

FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or 'Lt-@=waIh))Ql3~'

print("="*80)
print("VERIFICANDO CAMPOS DISPONIVEIS EM ATENDIMENTO_A1")
print("="*80)

# Campos que ESTAO sendo sincronizados atualmente
campos_sincronizados = [
    'CODIGO',
    'CODIGO_CLIENTE',
    'AVIADA_DT',
    'ENTREGUE_DT',
    'DATA',            # <- NOVO (data_criacao)
    'VALORVENDA',
    'OBSERVACAO'
]

# Campos que podem ser úteis
campos_interessantes = [
    'DATA',
    'HORA',
    'VENDEDOR',
    'CODIGO_VENDEDOR',
    'DESCONTO',
    'FORMA_PAGAMENTO',
    'STATUS',
    'TIPO',
    'NUMERO',
    'SERIE',
    'NOTA_FISCAL',
    'VALOR_DESCONTO',
    'VALOR_TOTAL',
    'CANCELADO'
]

try:
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    
    cursor = conn.cursor()
    
    # Buscar campos usando apenas alguns campos conhecidos
    cursor.execute("""
        SELECT FIRST 1
            CODIGO,
            CODIGO_CLIENTE,
            DATA,
            AVIADA_DT,
            ENTREGUE_DT,
            VALORVENDA,
            OBSERVACAO
        FROM ATENDIMENTO_A1
    """)
    
    # Pegar descrição
    descricao = cursor.description
    campos_base = [desc[0] for desc in descricao]
    
    print("\nCAMPOS BASE encontrados:")
    for campo in campos_base:
        print(f"  - {campo}")
    
    # Testar campos adicionais
    print("\n" + "="*80)
    print("TESTANDO CAMPOS ADICIONAIS COMUNS")
    print("="*80)
    
    campos_encontrados = []
    campos_nao_encontrados = []
    
    for campo in campos_interessantes:
        try:
            cursor.execute(f"""
                SELECT FIRST 1 {campo}
                FROM ATENDIMENTO_A1
            """)
            valor = cursor.fetchone()
            campos_encontrados.append((campo, valor[0] if valor else None))
            print(f"  OK  {campo:<25} = {valor[0] if valor else 'NULL'}")
        except:
            campos_nao_encontrados.append(campo)
            print(f"  --  {campo:<25} (nao existe)")
    
    conn.close()
    
    # Recomendações
    print("\n" + "="*80)
    print("RECOMENDACOES")
    print("="*80)
    
    print("\nCAMPOS SENDO SINCRONIZADOS:")
    for campo in campos_sincronizados:
        print(f"  -> {campo}")
    
    print("\nCAMPOS DISPONIVEIS QUE PODEM SER ADICIONADOS:")
    for campo, valor in campos_encontrados:
        if campo not in campos_sincronizados:
            print(f"  -> {campo:<25} (exemplo: {valor})")
    
    print("\n" + "="*80)
    print("SUGESTAO DE QUERY COMPLETA")
    print("="*80)
    
    query_sugerida = """
SELECT
    A.CODIGO,
    A.CODIGO_CLIENTE,
    A.DATA,              -- data_criacao
    A.AVIADA_DT,         -- data_aprovacao
    A.ENTREGUE_DT,       -- data_entrega
    A.VALORVENDA,        -- valor_total
    A.OBSERVACAO         -- observacoes
"""
    
    # Adicionar campos encontrados
    for campo, _ in campos_encontrados:
        if campo not in campos_sincronizados:
            query_sugerida += f",\n    A.{campo}            -- {campo.lower()}"
    
    query_sugerida += """
FROM ATENDIMENTO_A1 A
WHERE A.CODIGO_CLIENTE IS NOT NULL
AND A.CODIGO > {ultimo_codigo}
ORDER BY A.CODIGO
ROWS 1000
"""
    
    print(query_sugerida)
    
except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n")

