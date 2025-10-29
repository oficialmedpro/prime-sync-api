#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICAÇÃO: Cliente código 9999999 existe no Firebird/Prime?
Data: 27/10/2025
"""

import fdb
import os

# ============================================================================
# CONFIGURAÇÃO - Ajuste conforme suas credenciais
# ============================================================================

FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or input("Digite a senha do Firebird: ")

print("="*80)
print("🔍 VERIFICAÇÃO: Cliente 9999999 existe no Prime/Firebird?")
print("="*80)

try:
    # Conectar no Firebird
    print(f"\n📡 Conectando no Firebird...")
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
    
    print("✅ Conectado com sucesso!\n")
    
    cursor = conn.cursor()
    
    # ========================================================================
    # 1. Verificar se código 9999999 existe no Firebird
    # ========================================================================
    print("="*80)
    print("1️⃣ VERIFICANDO: Cliente 9999999 no Firebird")
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
        print("❌ CLIENTE 9999999 EXISTE NO FIREBIRD!")
        print(f"\n   Código: {resultado[0]}")
        print(f"   Nome: {resultado[1]}")
        print(f"   CPF/CNPJ: {resultado[2]}")
        print(f"   Ativo: {'Sim' if resultado[3] == -1 else 'Não'}")
        print(f"   Email: {resultado[4] or 'N/A'}")
        print(f"   Telefone: {resultado[5] or 'N/A'}")
        print("\n⚠️  NÃO DELETAR este cliente do Supabase!")
        print("   Ele é um cliente legítimo do sistema Prime.")
    else:
        print("✅ Cliente 9999999 NÃO existe no Firebird")
        print("   Este código provavelmente foi inserido por teste/erro")
        print("   É SEGURO deletar do Supabase")
    
    # ========================================================================
    # 2. Verificar códigos REAIS de clientes no Firebird
    # ========================================================================
    print("\n" + "="*80)
    print("2️⃣ CÓDIGOS REAIS no Firebird (últimos 20 clientes ativos)")
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
        print("\n📋 Últimos 20 clientes cadastrados:")
        print(f"\n{'Código':<12} {'Nome':<50} {'Status'}")
        print("-"*80)
        
        for cliente in clientes:
            codigo = cliente[0]
            nome = (cliente[1] or 'N/A')[:48]
            ativo = 'Ativo' if cliente[2] == -1 else 'Inativo'
            print(f"{codigo:<12} {nome:<50} {ativo}")
        
        ultimo_codigo = clientes[0][0]
        primeiro_codigo = clientes[-1][0]
        
        print("\n" + "="*80)
        print(f"✅ Último código REAL no Firebird: {ultimo_codigo}")
        print(f"✅ Faixa dos últimos 20: {primeiro_codigo} até {ultimo_codigo}")
        
        if ultimo_codigo < 500000:
            print("\n💡 ANÁLISE:")
            print("   Os códigos reais estão abaixo de 500.000")
            print("   Códigos acima de 500.000 são SUSPEITOS de serem testes/erros")
    
    # ========================================================================
    # 3. Verificar códigos suspeitos no Firebird
    # ========================================================================
    print("\n" + "="*80)
    print("3️⃣ VERIFICANDO: Códigos suspeitos no Firebird (> 500.000)")
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
        print(f"\n⚠️  Encontrados {len(suspeitos)} clientes com códigos suspeitos:")
        print(f"\n{'Código':<12} {'Nome':<50} {'Status'}")
        print("-"*80)
        
        for cliente in suspeitos:
            codigo = cliente[0]
            nome = (cliente[1] or 'N/A')[:48]
            ativo = 'Ativo' if cliente[2] == -1 else 'Inativo'
            print(f"{codigo:<12} {nome:<50} {ativo}")
            
        print("\n💡 AÇÃO RECOMENDADA:")
        print("   Se esses clientes são testes/erros, deletar do Supabase é SEGURO")
        print("   Se são clientes legítimos, NÃO deletar!")
    else:
        print("\n✅ Nenhum cliente com código > 500.000 encontrado no Firebird")
        print("   Códigos acima de 500.000 no Supabase são TESTES/ERROS")
        print("   É SEGURO deletar do Supabase")
    
    # ========================================================================
    # 4. Estatísticas Gerais
    # ========================================================================
    print("\n" + "="*80)
    print("4️⃣ ESTATÍSTICAS GERAIS")
    print("="*80)
    
    # Total de clientes
    cursor.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1")
    total_ativos = cursor.fetchone()[0]
    
    # Maior código
    cursor.execute("SELECT MAX(CODIGO) FROM CLIENTE WHERE ATIVO = -1")
    maior_codigo = cursor.fetchone()[0]
    
    # Menor código
    cursor.execute("SELECT MIN(CODIGO) FROM CLIENTE WHERE ATIVO = -1")
    menor_codigo = cursor.fetchone()[0]
    
    print(f"\n📊 Clientes ATIVOS no Firebird:")
    print(f"   Total: {total_ativos:,} clientes")
    print(f"   Faixa de códigos: {menor_codigo} até {maior_codigo}")
    
    conn.close()
    
    # ========================================================================
    # CONCLUSÃO
    # ========================================================================
    print("\n" + "="*80)
    print("🎯 CONCLUSÃO E RECOMENDAÇÃO")
    print("="*80)
    
    if not resultado:  # Se 9999999 NÃO existe no Firebird
        print("\n✅ SEGURO DELETAR do Supabase:")
        print("   - Cliente 9999999 NÃO existe no Firebird")
        print("   - É um registro de teste/erro")
        print("   - Está impedindo a sincronização")
        
        print("\n📋 SQL PARA EXECUTAR NO SUPABASE:")
        print("-"*80)
        print("DELETE FROM api.prime_clientes WHERE codigo_cliente_original = 9999999;")
        print("-"*80)
    else:
        print("\n⚠️  NÃO DELETAR do Supabase:")
        print("   - Cliente 9999999 EXISTE no Firebird")
        print("   - É um cliente legítimo")
        print("   - O problema está em outro lugar")
        
        print("\n🔍 INVESTIGAR:")
        print("   Por que este código está sendo considerado o 'último'?")
        print("   Talvez o problema seja na query de busca do último código.")
    
    print("\n" + "="*80)

except fdb.DatabaseError as e:
    print(f"\n❌ Erro ao conectar no Firebird: {e}")
    print("\n💡 Verifique:")
    print("   1. Host está correto?")
    print("   2. Database está correto?")
    print("   3. Usuário/senha estão corretos?")
    print("   4. Servidor Firebird está acessível?")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")

print("\n")



