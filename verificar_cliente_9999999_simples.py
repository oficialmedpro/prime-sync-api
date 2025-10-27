#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICACAO: Cliente codigo 9999999 existe no Firebird/Prime?
Data: 27/10/2025
"""

import fdb
import os

# Configuracao
FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS')

if not FIREBIRD_PASS:
    print("ERRO: Configure FIREBIRD_PASS")
    exit(1)

print("="*80)
print("VERIFICACAO: Cliente 9999999 existe no Prime/Firebird?")
print("="*80)

try:
    # Conectar no Firebird
    print("\nConectando no Firebird...")
    print(f"   Host: {FIREBIRD_HOST}")
    print(f"   Database: {FIREBIRD_DB}")
    print(f"   User: {FIREBIRD_USER}")
    
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    
    print("OK - Conectado com sucesso!\n")
    
    cursor = conn.cursor()
    
    # Verificar se codigo 9999999 existe no Firebird
    print("="*80)
    print("1. VERIFICANDO: Cliente 9999999 no Firebird")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            C.CODIGO,
            C.NOMECLIENTE,
            C.CPF_CNPJ,
            C.ATIVO,
            C.EMAIL1,
            C.TELEFONE1
        FROM CLIENTE C
        WHERE C.CODIGO = 9999999
    """)
    
    resultado = cursor.fetchone()
    
    if resultado:
        print("\nRESULTADO: Cliente 9999999 EXISTE NO FIREBIRD!")
        print(f"\n   Codigo: {resultado[0]}")
        print(f"   Nome: {resultado[1]}")
        print(f"   CPF/CNPJ: {resultado[2]}")
        print(f"   Ativo: {'Sim' if resultado[3] == -1 else 'Nao'}")
        print(f"   Email: {resultado[4] or 'N/A'}")
        print(f"   Telefone: {resultado[5] or 'N/A'}")
        print("\nCONCLUSAO: NAO DELETAR este cliente do Supabase!")
        print("           Ele e um cliente legitimo do sistema Prime.")
    else:
        print("\nRESULTADO: Cliente 9999999 NAO existe no Firebird")
        print("           Este codigo provavelmente foi inserido por teste/erro")
        print("           E SEGURO deletar do Supabase")
    
    # Verificar codigos REAIS de clientes no Firebird
    print("\n" + "="*80)
    print("2. CODIGOS REAIS no Firebird (ultimos 20 clientes ativos)")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            C.CODIGO,
            C.NOMECLIENTE,
            C.ATIVO
        FROM CLIENTE C
        WHERE C.ATIVO = -1
        ORDER BY C.CODIGO DESC
        ROWS 20
    """)
    
    clientes = cursor.fetchall()
    
    if clientes:
        print("\nUltimos 20 clientes cadastrados:")
        print(f"\n{'Codigo':<12} {'Nome':<50} {'Status'}")
        print("-"*80)
        
        for cliente in clientes:
            codigo = cliente[0]
            nome = (cliente[1] or 'N/A')[:48]
            ativo = 'Ativo' if cliente[2] == -1 else 'Inativo'
            print(f"{codigo:<12} {nome:<50} {ativo}")
        
        ultimo_codigo = clientes[0][0]
        primeiro_codigo = clientes[-1][0]
        
        print("\n" + "="*80)
        print(f"Ultimo codigo REAL no Firebird: {ultimo_codigo}")
        print(f"Faixa dos ultimos 20: {primeiro_codigo} ate {ultimo_codigo}")
        
        if ultimo_codigo < 500000:
            print("\nANALISE:")
            print("   Os codigos reais estao abaixo de 500.000")
            print("   Codigos acima de 500.000 sao SUSPEITOS de serem testes/erros")
    
    # Verificar codigos suspeitos no Firebird
    print("\n" + "="*80)
    print("3. VERIFICANDO: Codigos suspeitos no Firebird (> 500.000)")
    print("="*80)
    
    cursor.execute("""
        SELECT 
            C.CODIGO,
            C.NOMECLIENTE,
            C.ATIVO
        FROM CLIENTE C
        WHERE C.CODIGO > 500000
        ORDER BY C.CODIGO DESC
    """)
    
    suspeitos = cursor.fetchall()
    
    if suspeitos:
        print(f"\nEncontrados {len(suspeitos)} clientes com codigos suspeitos:")
        print(f"\n{'Codigo':<12} {'Nome':<50} {'Status'}")
        print("-"*80)
        
        for cliente in suspeitos:
            codigo = cliente[0]
            nome = (cliente[1] or 'N/A')[:48]
            ativo = 'Ativo' if cliente[2] == -1 else 'Inativo'
            print(f"{codigo:<12} {nome:<50} {ativo}")
            
        print("\nACAO RECOMENDADA:")
        print("   Se esses clientes sao testes/erros, deletar do Supabase e SEGURO")
        print("   Se sao clientes legitimos, NAO deletar!")
    else:
        print("\nNenhum cliente com codigo > 500.000 encontrado no Firebird")
        print("   Codigos acima de 500.000 no Supabase sao TESTES/ERROS")
        print("   E SEGURO deletar do Supabase")
    
    # Estatisticas Gerais
    print("\n" + "="*80)
    print("4. ESTATISTICAS GERAIS")
    print("="*80)
    
    # Total de clientes
    cursor.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1")
    total_ativos = cursor.fetchone()[0]
    
    # Maior codigo
    cursor.execute("SELECT MAX(CODIGO) FROM CLIENTE WHERE ATIVO = -1")
    maior_codigo = cursor.fetchone()[0]
    
    # Menor codigo
    cursor.execute("SELECT MIN(CODIGO) FROM CLIENTE WHERE ATIVO = -1")
    menor_codigo = cursor.fetchone()[0]
    
    print(f"\nClientes ATIVOS no Firebird:")
    print(f"   Total: {total_ativos:,} clientes")
    print(f"   Faixa de codigos: {menor_codigo} ate {maior_codigo}")
    
    conn.close()
    
    # CONCLUSAO
    print("\n" + "="*80)
    print("CONCLUSAO E RECOMENDACAO")
    print("="*80)
    
    if not resultado:  # Se 9999999 NAO existe no Firebird
        print("\nSEGURO DELETAR do Supabase:")
        print("   - Cliente 9999999 NAO existe no Firebird")
        print("   - E um registro de teste/erro")
        print("   - Esta impedindo a sincronizacao")
        
        print("\nSQL PARA EXECUTAR NO SUPABASE:")
        print("-"*80)
        print("DELETE FROM api.prime_clientes WHERE codigo_cliente_original = 9999999;")
        print("-"*80)
    else:
        print("\nNAO DELETAR do Supabase:")
        print("   - Cliente 9999999 EXISTE no Firebird")
        print("   - E um cliente legitimo")
        print("   - O problema esta em outro lugar")
        
        print("\nINVESTIGAR:")
        print("   Por que este codigo esta sendo considerado o 'ultimo'?")
        print("   Talvez o problema seja na query de busca do ultimo codigo.")
    
    print("\n" + "="*80)

except fdb.DatabaseError as e:
    print(f"\nERRO ao conectar no Firebird: {e}")
    print("\nVerifique:")
    print("   1. Host esta correto?")
    print("   2. Database esta correto?")
    print("   3. Usuario/senha estao corretos?")
    print("   4. Servidor Firebird esta acessivel?")
    
except Exception as e:
    print(f"\nERRO: {e}")

print("\n")

