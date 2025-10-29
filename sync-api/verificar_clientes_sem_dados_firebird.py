#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica se os clientes sem telefone/endereço no Supabase
realmente não têm esses dados no Firebird também
"""

import fdb
import requests
import os
from dotenv import load_dotenv

load_dotenv('../config.env')
load_dotenv('../config_supabase.env')

# Configurações Firebird
FIREBIRD_DATABASE = os.getenv('FIREBIRD_DATABASE', 'C:/Banco de Dados Prime/psbd.fdb')
FIREBIRD_USER = os.getenv('FIREBIRD_USER', 'SYSDBA')
FIREBIRD_PASSWORD = os.getenv('FIREBIRD_PASSWORD', 'masterkey')

# Configurações Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Fallback para variáveis do app.py
if not SUPABASE_URL:
    SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
if not SUPABASE_KEY:
    SUPABASE_KEY = os.getenv('SERVICE_ROLE_KEY')

def conectar_firebird():
    return fdb.connect(
        database=FIREBIRD_DATABASE,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset='WIN1252'
    )

print("="*100)
print("VERIFICANDO CLIENTES SEM TELEFONE/ENDERECO")
print("="*100)

# 1. Buscar clientes SEM telefone no Supabase (pegar amostra de 50)
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

print("\n[1/3] Buscando clientes SEM telefone no Supabase (amostra de 50)...")
url = f"{SUPABASE_URL}/rest/v1/prime_clientes?telefone=is.null&ativo=eq.true&select=codigo_cliente_original,nome&limit=50"
response = requests.get(url, headers=headers)
clientes_sem_tel_sb = response.json()

print(f"   Encontrados: {len(clientes_sem_tel_sb)} clientes sem telefone no Supabase")

# 2. Verificar no Firebird se esses clientes têm telefone lá
print("\n[2/3] Verificando no Firebird se esses clientes TÊM telefone...")
conn = conectar_firebird()
cursor = conn.cursor()

codigos = [c['codigo_cliente_original'] for c in clientes_sem_tel_sb]
codigos_str = ','.join(map(str, codigos))

cursor.execute(f"""
    SELECT 
        CT.CODIGO_CADASTRO,
        CT.TELEFONEPREFIXO,
        CT.TELEFONE
    FROM CADASTRO_TELEFONE CT
    WHERE CT.TIPO_CADASTRO = 1
    AND CT.CODIGO_CADASTRO IN ({codigos_str})
    AND CT.TELEFONE IS NOT NULL
""")

clientes_com_tel_fb = {}
for row in cursor.fetchall():
    codigo = row[0]
    tel = (str(row[1] or '') + str(row[2] or '')).strip()
    if tel:
        clientes_com_tel_fb[codigo] = tel

conn.close()

# 3. Contar discrepâncias
tem_no_fb_mas_nao_sb = len(clientes_com_tel_fb)
nao_tem_nem_fb = len(clientes_sem_tel_sb) - tem_no_fb_mas_nao_sb

print(f"\n   RESULTADO:")
print(f"   - Clientes analisados: {len(clientes_sem_tel_sb)}")
print(f"   - TÊM telefone no Firebird (ERRO DE SINCRONIZAÇÃO): {tem_no_fb_mas_nao_sb}")
print(f"   - NÃO TÊM telefone nem no Firebird (CORRETO): {nao_tem_nem_fb}")

if tem_no_fb_mas_nao_sb > 0:
    print(f"\n   [AVISO] {tem_no_fb_mas_nao_sb} clientes encontrados COM telefone no Firebird!")
    print("   Códigos:")
    for codigo, tel in list(clientes_com_tel_fb.items())[:10]:
        print(f"      - Cliente {codigo}: {tel}")
else:
    print(f"\n   [OK] Todos os {nao_tem_nem_fb} clientes SEM telefone no Supabase também NÃO TÊM no Firebird!")

# 4. Fazer o mesmo para ENDEREÇOS
print("\n[3/3] Verificando ENDEREÇOS (amostra de 50)...")
url = f"{SUPABASE_URL}/rest/v1/prime_clientes?endereco_logradouro=is.null&ativo=eq.true&select=codigo_cliente_original,nome&limit=50"
response = requests.get(url, headers=headers)
clientes_sem_end_sb = response.json()

print(f"   Encontrados: {len(clientes_sem_end_sb)} clientes sem endereço no Supabase")

conn = conectar_firebird()
cursor = conn.cursor()

codigos = [c['codigo_cliente_original'] for c in clientes_sem_end_sb]
codigos_str = ','.join(map(str, codigos))

cursor.execute(f"""
    SELECT 
        CE.CODIGO_CADASTRO,
        CE.ENDERECO
    FROM CADASTRO_ENDERECO CE
    WHERE CE.TIPO_CADASTRO = 1
    AND CE.CODIGO_CADASTRO IN ({codigos_str})
    AND CE.ENDERECO IS NOT NULL
""")

clientes_com_end_fb = {}
for row in cursor.fetchall():
    codigo = row[0]
    end = str(row[1] or '').strip()
    if end:
        clientes_com_end_fb[codigo] = end

conn.close()

tem_no_fb_mas_nao_sb_end = len(clientes_com_end_fb)
nao_tem_nem_fb_end = len(clientes_sem_end_sb) - tem_no_fb_mas_nao_sb_end

print(f"\n   RESULTADO:")
print(f"   - Clientes analisados: {len(clientes_sem_end_sb)}")
print(f"   - TÊM endereço no Firebird (ERRO DE SINCRONIZAÇÃO): {tem_no_fb_mas_nao_sb_end}")
print(f"   - NÃO TÊM endereço nem no Firebird (CORRETO): {nao_tem_nem_fb_end}")

if tem_no_fb_mas_nao_sb_end > 0:
    print(f"\n   [AVISO] {tem_no_fb_mas_nao_sb_end} clientes encontrados COM endereço no Firebird!")
    print("   Códigos:")
    for codigo, end in list(clientes_com_end_fb.items())[:10]:
        print(f"      - Cliente {codigo}: {end[:50]}")
else:
    print(f"\n   [OK] Todos os {nao_tem_nem_fb_end} clientes SEM endereço no Supabase também NÃO TÊM no Firebird!")

print("\n" + "="*100)
print("CONCLUSÃO FINAL:")
print("="*100)

if tem_no_fb_mas_nao_sb == 0 and tem_no_fb_mas_nao_sb_end == 0:
    print("[OK] SINCRONIZAÇÃO 100% CORRETA!")
    print("Todos os clientes sem dados no Supabase também não têm no Firebird.")
else:
    total_erros = tem_no_fb_mas_nao_sb + tem_no_fb_mas_nao_sb_end
    print(f"[AVISO] {total_erros} clientes encontrados com dados no Firebird mas não no Supabase")
    print("Execute o script de correção novamente ou aguarde a próxima sincronização (30min)")

print("="*100)

