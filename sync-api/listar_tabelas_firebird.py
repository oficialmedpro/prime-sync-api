#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Listar todas as tabelas do Firebird relacionadas a cliente
"""
import fdb

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

print("=" * 100)
print("LISTANDO TABELAS DO FIREBIRD")
print("=" * 100)

try:
    conn = fdb.connect(
        host=FIREBIRD_HOST, 
        database=FIREBIRD_DB, 
        user=FIREBIRD_USER, 
        password=FIREBIRD_PASS, 
        charset='UTF8'
    )
    cursor = conn.cursor()
    
    # Listar tabelas que contenham CLIENTE, TELEFONE ou ENDERECO no nome
    query = """
        SELECT DISTINCT RDB$RELATION_NAME
        FROM RDB$RELATIONS
        WHERE RDB$SYSTEM_FLAG = 0
        AND (
            RDB$RELATION_NAME LIKE '%CLIENTE%'
            OR RDB$RELATION_NAME LIKE '%TELEFONE%'
            OR RDB$RELATION_NAME LIKE '%ENDERECO%'
            OR RDB$RELATION_NAME LIKE '%FONE%'
        )
        ORDER BY RDB$RELATION_NAME
    """
    
    cursor.execute(query)
    tabelas = cursor.fetchall()
    
    print("\n[TABELAS ENCONTRADAS]")
    print("-" * 100)
    for tabela in tabelas:
        nome_tabela = tabela[0].strip()
        print(f"  - {nome_tabela}")
    
    print("\n" + "=" * 100)
    
    # Agora vamos ver os dados do cliente 37479 nessas tabelas relacionadas
    codigo_cliente = 37479
    
    # Tentar buscar telefones
    print(f"\n[BUSCANDO TELEFONES DO CLIENTE {codigo_cliente}]")
    print("-" * 100)
    
    # Possíveis tabelas de telefone
    tabelas_telefone = ['CLIENTETELEFONE', 'CLIENTE_TELEFONE', 'TELEFONE', 'FONE']
    
    for tab in tabelas_telefone:
        try:
            cursor.execute(f"SELECT FIRST 5 * FROM {tab} WHERE CODIGO_CLIENTE = ?", (codigo_cliente,))
            telefones = cursor.fetchall()
            if telefones:
                print(f"\n  Encontrado em {tab}:")
                for tel in telefones:
                    print(f"    {tel}")
        except:
            pass
    
    # Tentar buscar endereços
    print(f"\n[BUSCANDO ENDERECOS DO CLIENTE {codigo_cliente}]")
    print("-" * 100)
    
    tabelas_endereco = ['CLIENTEENDERECO', 'CLIENTE_ENDERECO', 'ENDERECO']
    
    for tab in tabelas_endereco:
        try:
            cursor.execute(f"SELECT FIRST 5 * FROM {tab} WHERE CODIGO_CLIENTE = ?", (codigo_cliente,))
            enderecos = cursor.fetchall()
            if enderecos:
                print(f"\n  Encontrado em {tab}:")
                for end in enderecos:
                    print(f"    {end}")
        except:
            pass
    
    conn.close()
    print("\n" + "=" * 100)
    print("[OK] CONSULTA FINALIZADA")
    print("=" * 100 + "\n")
    
except Exception as e:
    print(f"\n[ERRO] {str(e)}\n")
    import traceback
    traceback.print_exc()



