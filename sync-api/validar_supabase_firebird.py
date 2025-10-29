#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validacao: Supabase vs Firebird
Verifica se os dados estao sincronizados corretamente

Data: 28/10/2025
"""

import fdb
import requests
from datetime import datetime

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

SUPABASE_URL = 'https://agdffspstbxeqhqtltvb.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

print("=" * 100)
print("VALIDACAO: SUPABASE vs FIREBIRD")
print("=" * 100)
print(f"Iniciado em: {datetime.now()}")
print("=" * 100)

# ============================================================================
# 1. VALIDAR CLIENTE NELSON MORENO (caso de teste)
# ============================================================================
print("\n[1/5] Validando cliente Nelson Moreno (37479)...")

# Firebird
conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

# Buscar dados basicos
cursor.execute("""
    SELECT C.CODIGO, C.NOMECLIENTE
    FROM CLIENTE C
    WHERE C.CODIGO = 37479
""")
cliente_fb = cursor.fetchone()

# Buscar telefone
cursor.execute("""
    SELECT CT.TELEFONEPREFIXO, CT.TELEFONE
    FROM CADASTRO_TELEFONE CT
    WHERE CT.TIPO_CADASTRO = 1
    AND CT.CODIGO_CADASTRO = 37479
""")
tel_fb = cursor.fetchone()
telefone_fb = (str(tel_fb[0]) + str(tel_fb[1])).strip() if tel_fb else None

# Buscar endereco
cursor.execute("""
    SELECT CE.ENDERECO, CE.NUMERO, CE.CEP
    FROM CADASTRO_ENDERECO CE
    WHERE CE.TIPO_CADASTRO = 1
    AND CE.CODIGO_CADASTRO = 37479
""")
end_fb = cursor.fetchone()

# Buscar totalizadores
cursor.execute("""
    SELECT 
        COUNT(*) as total_orcamentos,
        SUM(A.VALORVENDA) as valor_total
    FROM ATENDIMENTO_A1 A
    WHERE A.CODIGO_CLIENTE = 37479
""")
tot_fb = cursor.fetchone()

conn.close()

# Supabase
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/prime_clientes",
    headers=headers,
    params={
        'select': '*',
        'codigo_cliente_original': 'eq.37479'
    }
)

if response.status_code == 200:
    dados_sb = response.json()
    if dados_sb:
        cliente_sb = dados_sb[0]
        
        print(f"\n   FIREBIRD:")
        print(f"      Nome: {cliente_fb[1] if cliente_fb else 'N/A'}")
        print(f"      Telefone: {telefone_fb or 'N/A'}")
        print(f"      Endereco: {end_fb[0] if end_fb else 'N/A'}")
        print(f"      Total Orcamentos: {tot_fb[0] if tot_fb else 0}")
        print(f"      Valor Total: R$ {float(tot_fb[1]) if tot_fb and tot_fb[1] else 0:.2f}")
        
        print(f"\n   SUPABASE:")
        print(f"      Nome: {cliente_sb.get('nome', 'N/A')}")
        print(f"      Telefone: {cliente_sb.get('telefone', 'N/A')}")
        print(f"      Endereco: {cliente_sb.get('endereco_logradouro', 'N/A')}")
        print(f"      Total Orcamentos: {cliente_sb.get('total_orcamentos', 0)}")
        print(f"      Valor Total: R$ {float(cliente_sb.get('valor_total_orcamentos', 0)):.2f}")
        
        # Validar
        erros = []
        if telefone_fb and not cliente_sb.get('telefone'):
            erros.append("Telefone faltando no Supabase")
        if end_fb and not cliente_sb.get('endereco_logradouro'):
            erros.append("Endereco faltando no Supabase")
        if tot_fb and tot_fb[0] != cliente_sb.get('total_orcamentos', 0):
            erros.append(f"Total orcamentos diferente (FB: {tot_fb[0]}, SB: {cliente_sb.get('total_orcamentos', 0)})")
        
        if erros:
            print(f"\n   [ERRO] Diferencas encontradas:")
            for erro in erros:
                print(f"      - {erro}")
        else:
            print(f"\n   [OK] Cliente validado com sucesso!")
    else:
        print(f"\n   [ERRO] Cliente nao encontrado no Supabase!")
else:
    print(f"\n   [ERRO] Erro ao buscar Supabase: {response.status_code}")

# ============================================================================
# 2. VALIDAR TOTAIS GERAIS
# ============================================================================
print("\n[2/5] Validando totais gerais...")

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

# Total de clientes ativos
cursor.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1 AND CODIGO < 500000")
total_clientes_fb = cursor.fetchone()[0]

# Total de pedidos
cursor.execute("SELECT COUNT(*) FROM ATENDIMENTO_A1 WHERE CODIGO_CLIENTE IS NOT NULL AND CODIGO_CLIENTE < 500000")
total_pedidos_fb = cursor.fetchone()[0]

# Total de formulas
cursor.execute("SELECT COUNT(*) FROM ATENDIMENTO_A2 WHERE CODIGO_ATEND_A1 IS NOT NULL")
total_formulas_fb = cursor.fetchone()[0]

# Total de itens
cursor.execute("SELECT COUNT(*) FROM ATENDIMENTO_A3 WHERE CODIGO_ATEND_A1 IS NOT NULL")
total_itens_fb = cursor.fetchone()[0]

conn.close()

# Supabase
response = requests.get(f"{SUPABASE_URL}/rest/v1/prime_clientes", headers=headers, params={'select': 'count'})
total_clientes_sb = len(response.json()) if response.status_code == 200 else 0

response = requests.get(f"{SUPABASE_URL}/rest/v1/prime_pedidos", headers=headers, params={'select': 'count', 'limit': 1})
total_pedidos_sb = response.headers.get('Content-Range', '0').split('/')[-1] if response.status_code == 200 else 0

response = requests.get(f"{SUPABASE_URL}/rest/v1/prime_formulas", headers=headers, params={'select': 'count', 'limit': 1})
total_formulas_sb = response.headers.get('Content-Range', '0').split('/')[-1] if response.status_code == 200 else 0

response = requests.get(f"{SUPABASE_URL}/rest/v1/prime_formulas_itens", headers=headers, params={'select': 'count', 'limit': 1})
total_itens_sb = response.headers.get('Content-Range', '0').split('/')[-1] if response.status_code == 200 else 0

print(f"\n   {'Tabela':<20} {'Firebird':>15} {'Supabase':>15} {'Diferenca':>15}")
print(f"   {'-'*70}")
print(f"   {'Clientes':<20} {total_clientes_fb:>15,} {total_clientes_sb:>15,} {total_clientes_fb - total_clientes_sb:>15,}")
print(f"   {'Pedidos':<20} {total_pedidos_fb:>15,} {int(total_pedidos_sb):>15,} {total_pedidos_fb - int(total_pedidos_sb):>15,}")
print(f"   {'Formulas':<20} {total_formulas_fb:>15,} {int(total_formulas_sb):>15,} {total_formulas_fb - int(total_formulas_sb):>15,}")
print(f"   {'Itens':<20} {total_itens_fb:>15,} {int(total_itens_sb):>15,} {total_itens_fb - int(total_itens_sb):>15,}")

# ============================================================================
# 3. VALIDAR CLIENTES COM TELEFONE
# ============================================================================
print("\n[3/5] Validando clientes com telefone...")

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(DISTINCT CT.CODIGO_CADASTRO)
    FROM CADASTRO_TELEFONE CT
    WHERE CT.TIPO_CADASTRO = 1
    AND CT.CODIGO_CADASTRO < 500000
""")
total_com_tel_fb = cursor.fetchone()[0]

conn.close()

# Supabase
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/prime_clientes",
    headers=headers,
    params={'select': 'telefone', 'telefone': 'not.is.null'}
)
total_com_tel_sb = len(response.json()) if response.status_code == 200 else 0

print(f"   Clientes com telefone no Firebird: {total_com_tel_fb:,}")
print(f"   Clientes com telefone no Supabase: {total_com_tel_sb:,}")
print(f"   Diferenca: {total_com_tel_fb - total_com_tel_sb:,}")

if total_com_tel_fb - total_com_tel_sb > 100:
    print(f"   [ALERTA] Muitos telefones faltando no Supabase!")
elif total_com_tel_fb - total_com_tel_sb > 0:
    print(f"   [AVISO] Alguns telefones faltando no Supabase")
else:
    print(f"   [OK] Telefones sincronizados!")

# ============================================================================
# 4. VALIDAR TOTALIZADORES
# ============================================================================
print("\n[4/5] Validando totalizadores...")

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/prime_clientes",
    headers=headers,
    params={'select': 'total_orcamentos', 'total_orcamentos': 'gt.0'}
)
clientes_com_total_sb = len(response.json()) if response.status_code == 200 else 0

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(DISTINCT A.CODIGO_CLIENTE)
    FROM ATENDIMENTO_A1 A
    WHERE A.CODIGO_CLIENTE IS NOT NULL
    AND A.CODIGO_CLIENTE < 500000
""")
clientes_com_pedidos_fb = cursor.fetchone()[0]

conn.close()

print(f"   Clientes com pedidos no Firebird: {clientes_com_pedidos_fb:,}")
print(f"   Clientes com total_orcamentos > 0 no Supabase: {clientes_com_total_sb:,}")
print(f"   Diferenca: {clientes_com_pedidos_fb - clientes_com_total_sb:,}")

if clientes_com_pedidos_fb - clientes_com_total_sb > 100:
    print(f"   [ALERTA] Muitos totalizadores faltando!")
elif clientes_com_pedidos_fb - clientes_com_total_sb > 0:
    print(f"   [AVISO] Alguns totalizadores faltando")
else:
    print(f"   [OK] Totalizadores sincronizados!")

# ============================================================================
# 5. VALIDAR FORMULAS COM NOME
# ============================================================================
print("\n[5/5] Validando formulas com nome do produto...")

response = requests.get(
    f"{SUPABASE_URL}/rest/v1/prime_formulas",
    headers=headers,
    params={'select': 'descricao', 'descricao': 'not.is.null', 'limit': 10}
)

if response.status_code == 200:
    formulas = response.json()
    print(f"   Total de formulas com descricao: {len(formulas)}")
    if formulas:
        print(f"   Exemplo: {formulas[0].get('descricao', 'N/A')[:60]}...")
        print(f"   [OK] Formulas com nome do produto!")
    else:
        print(f"   [ERRO] Nenhuma formula com descricao!")
else:
    print(f"   [ERRO] Erro ao buscar formulas: {response.status_code}")

# ============================================================================
# RESUMO FINAL
# ============================================================================
print("\n" + "=" * 100)
print("RESUMO DA VALIDACAO")
print("=" * 100)
print("\nStatus geral: Verifique os alertas acima")
print("\nSe houver diferencas:")
print("  1. Rode novamente o script de correcao")
print("  2. Verifique se a API esta sincronizando corretamente")
print("  3. Execute este script novamente para validar")
print("\n" + "=" * 100)
print(f"Finalizado em: {datetime.now()}")
print("=" * 100)



