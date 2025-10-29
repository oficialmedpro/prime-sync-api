#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPARAÇÃO: Clientes Firebird vs Supabase
Identifica discrepâncias e registros inválidos
Data: 27/10/2025
"""

import fdb
import requests
import os

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Firebird
FIREBIRD_HOST = os.getenv('FIREBIRD_HOST') or 'db.primesoftware.com.br'
FIREBIRD_DB = os.getenv('FIREBIRD_DB') or 'oficialmed1250'
FIREBIRD_USER = os.getenv('FIREBIRD_USER') or 'OFICIALMED'
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS') or input("Digite a senha do Firebird: ")

# Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL') or input("Digite a URL do Supabase: ")
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('VITE_SUPABASE_SERVICE_ROLE_KEY') or input("Digite a Service Role Key: ")

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api'
}

print("\n" + "="*80)
print("🔍 COMPARAÇÃO: Clientes Firebird vs Supabase")
print("="*80)

try:
    # ========================================================================
    # 1. Buscar dados do FIREBIRD
    # ========================================================================
    print("\n📡 Conectando no Firebird...")
    
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    
    print("✅ Conectado!\n")
    
    cursor = conn.cursor()
    
    # Buscar estatísticas do Firebird
    cursor.execute("SELECT MIN(CODIGO), MAX(CODIGO), COUNT(*) FROM CLIENTE WHERE ATIVO = -1")
    min_fb, max_fb, total_fb = cursor.fetchone()
    
    print("="*80)
    print("📊 FIREBIRD (Prime)")
    print("="*80)
    print(f"Total de clientes ativos: {total_fb:,}")
    print(f"Menor código: {min_fb}")
    print(f"Maior código: {max_fb}")
    
    # Buscar últimos 10 códigos do Firebird
    cursor.execute("""
        SELECT CODIGO, NOMECLIENTE 
        FROM CLIENTE 
        WHERE ATIVO = -1 
        ORDER BY CODIGO DESC 
        ROWS 10
    """)
    ultimos_fb = cursor.fetchall()
    
    print(f"\nÚltimos 10 clientes cadastrados:")
    for codigo, nome in ultimos_fb:
        print(f"   {codigo} - {(nome or 'N/A')[:50]}")
    
    conn.close()
    
    # ========================================================================
    # 2. Buscar dados do SUPABASE
    # ========================================================================
    print("\n📡 Conectando no Supabase...")
    
    # Total de clientes
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
    response = requests.get(
        url,
        headers={**headers, 'Prefer': 'count=exact'},
        params={'select': 'id', 'limit': 0}
    )
    
    total_sb = 0
    if response.status_code == 200:
        total_sb = int(response.headers.get('Content-Range', '0').split('/')[-1])
    
    # Menor código
    response_min = requests.get(
        url,
        headers=headers,
        params={'select': 'codigo_cliente_original', 'order': 'codigo_cliente_original.asc', 'limit': 1}
    )
    min_sb = 0
    if response_min.status_code == 200 and response_min.json():
        min_sb = response_min.json()[0]['codigo_cliente_original']
    
    # Maior código
    response_max = requests.get(
        url,
        headers=headers,
        params={'select': 'codigo_cliente_original', 'order': 'codigo_cliente_original.desc', 'limit': 1}
    )
    max_sb = 0
    if response_max.status_code == 200 and response_max.json():
        max_sb = response_max.json()[0]['codigo_cliente_original']
    
    print("✅ Conectado!\n")
    
    print("="*80)
    print("📊 SUPABASE")
    print("="*80)
    print(f"Total de clientes: {total_sb:,}")
    print(f"Menor código: {min_sb}")
    print(f"Maior código: {max_sb}")
    
    # Buscar últimos 10 códigos do Supabase
    response_ultimos = requests.get(
        url,
        headers=headers,
        params={
            'select': 'codigo_cliente_original,nome',
            'order': 'codigo_cliente_original.desc',
            'limit': 10
        }
    )
    
    if response_ultimos.status_code == 200:
        ultimos_sb = response_ultimos.json()
        print(f"\nÚltimos 10 clientes cadastrados:")
        for cliente in ultimos_sb:
            print(f"   {cliente['codigo_cliente_original']} - {(cliente.get('nome') or 'N/A')[:50]}")
    
    # ========================================================================
    # 3. COMPARAÇÃO E ANÁLISE
    # ========================================================================
    print("\n" + "="*80)
    print("🔍 ANÁLISE COMPARATIVA")
    print("="*80)
    
    print(f"\n📊 Diferenças:")
    print(f"   Firebird: {total_fb:,} clientes")
    print(f"   Supabase: {total_sb:,} clientes")
    print(f"   Diferença: {total_fb - total_sb:,} clientes")
    
    if total_fb > total_sb:
        print(f"\n⚠️  Supabase está DESATUALIZADO ({total_fb - total_sb} clientes faltando)")
    elif total_sb > total_fb:
        print(f"\n⚠️  Supabase tem MAIS clientes que Firebird (+{total_sb - total_fb})")
        print("   Pode haver registros de teste/erro no Supabase")
    else:
        print("\n✅ Totais estão IGUAIS")
    
    print(f"\n📏 Faixa de códigos:")
    print(f"   Firebird: {min_fb} → {max_fb}")
    print(f"   Supabase: {min_sb} → {max_sb}")
    
    if max_sb > max_fb:
        print(f"\n⚠️  PROBLEMA DETECTADO!")
        print(f"   Maior código Supabase ({max_sb}) > Firebird ({max_fb})")
        print(f"   Códigos entre {max_fb + 1} e {max_sb} são INVÁLIDOS")
    
    # ========================================================================
    # 4. BUSCAR CÓDIGOS SUSPEITOS NO SUPABASE
    # ========================================================================
    print("\n" + "="*80)
    print("🚨 CÓDIGOS SUSPEITOS NO SUPABASE")
    print("="*80)
    
    # Buscar códigos acima do máximo do Firebird
    response_suspeitos = requests.get(
        url,
        headers=headers,
        params={
            'select': 'id,codigo_cliente_original,nome,created_at',
            'codigo_cliente_original': f'gt.{max_fb}',
            'order': 'codigo_cliente_original.desc'
        }
    )
    
    if response_suspeitos.status_code == 200:
        suspeitos = response_suspeitos.json()
        
        if suspeitos:
            print(f"\n❌ Encontrados {len(suspeitos)} registros com códigos INVÁLIDOS:")
            print(f"   (Códigos maiores que {max_fb}, que é o máximo no Firebird)\n")
            print(f"{'ID':<10} {'Código':<12} {'Nome':<40} {'Criado em'}")
            print("-"*80)
            
            for r in suspeitos:
                id_reg = str(r['id'])[:8]
                codigo = r['codigo_cliente_original']
                nome = (r.get('nome') or 'N/A')[:38]
                created = r['created_at'][:19]
                print(f"{id_reg:<10} {codigo:<12} {nome:<40} {created}")
            
            print("\n🔧 AÇÃO RECOMENDADA:")
            print("   Esses registros são INVÁLIDOS e estão impedindo a sincronização!")
            print("\n   SQL para deletar:")
            print("   " + "-"*76)
            print(f"   DELETE FROM api.prime_clientes WHERE codigo_cliente_original > {max_fb};")
            print("   " + "-"*76)
        else:
            print("\n✅ Nenhum código suspeito encontrado!")
            print("   Todos os códigos no Supabase são ≤ máximo do Firebird")
    
    # ========================================================================
    # 5. VERIFICAR CÓDIGOS ESPECÍFICOS
    # ========================================================================
    print("\n" + "="*80)
    print("🎯 VERIFICAÇÃO: Código 9999999")
    print("="*80)
    
    response_9999999 = requests.get(
        url,
        headers=headers,
        params={
            'select': 'id,codigo_cliente_original,nome,created_at',
            'codigo_cliente_original': 'eq.9999999'
        }
    )
    
    if response_9999999.status_code == 200 and response_9999999.json():
        reg = response_9999999.json()[0]
        print("\n❌ Código 9999999 EXISTE no Supabase:")
        print(f"   ID: {reg['id']}")
        print(f"   Nome: {reg.get('nome') or 'N/A'}")
        print(f"   Criado em: {reg['created_at']}")
        
        if max_fb < 9999999:
            print("\n⚠️  Este código NÃO existe no Firebird (máximo lá é {})".format(max_fb))
            print("   É SEGURO deletar!")
        else:
            print("\n⚠️  Verificar no Firebird se este cliente existe!")
    else:
        print("\n✅ Código 9999999 NÃO existe no Supabase")
    
    print("\n" + "="*80)

except fdb.DatabaseError as e:
    print(f"\n❌ Erro no Firebird: {e}")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ Erro no Supabase: {e}")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")

print("\n")



