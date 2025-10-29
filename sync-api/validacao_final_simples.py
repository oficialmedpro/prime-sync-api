#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validação Final Simples - Supabase vs Firebird
Verifica se a sincronização está funcionando corretamente
"""

import fdb
import requests
import os
from dotenv import load_dotenv

load_dotenv('../config.env')

# Configurações Firebird
FIREBIRD_HOST = os.getenv('FIREBIRD_HOST', 'localhost')
FIREBIRD_PORT = int(os.getenv('FIREBIRD_PORT', 3050))
FIREBIRD_DATABASE = os.getenv('FIREBIRD_DATABASE')
FIREBIRD_USER = os.getenv('FIREBIRD_USER', 'SYSDBA')
FIREBIRD_PASSWORD = os.getenv('FIREBIRD_PASSWORD')

# Configurações Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def conectar_firebird():
    return fdb.connect(
        host=FIREBIRD_HOST,
        port=FIREBIRD_PORT,
        database=FIREBIRD_DATABASE,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASSWORD,
        charset='WIN1252'
    )

print("="*100)
print("VALIDACAO FINAL - SUPABASE vs FIREBIRD")
print("="*100)

# 1. Validar Nelson Moreno (37479)
print("\n[1] Validando NELSON MORENO (37479)...")
conn = conectar_firebird()
cursor = conn.cursor()

cursor.execute("""
    SELECT C.NOMECLIENTE, CT.TELEFONEPREFIXO, CT.TELEFONE, CE.ENDERECO,
           (SELECT COUNT(*) FROM ATENDIMENTO_A1 A WHERE A.CODIGO_CLIENTE = 37479)
    FROM CLIENTE C
    LEFT JOIN CADASTRO_TELEFONE CT ON CT.CODIGO_CADASTRO = 37479 AND CT.TIPO_CADASTRO = 1
    LEFT JOIN CADASTRO_ENDERECO CE ON CE.CODIGO_CADASTRO = 37479 AND CE.TIPO_CADASTRO = 1
    WHERE C.CODIGO = 37479
    ROWS 1
""")
row = cursor.fetchone()
fb_nome = row[0] if row else None
fb_tel = (str(row[1] or '') + str(row[2] or '')).strip() if row else None
fb_end = row[3] if row else None
fb_total = row[4] if row else 0

conn.close()

# Buscar no Supabase
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}
url = f"{SUPABASE_URL}/rest/v1/prime_clientes?codigo_cliente_original=eq.37479&select=nome,telefone,endereco_logradouro,total_orcamentos"
response = requests.get(url, headers=headers)
sb_data = response.json()[0] if response.json() else {}

sb_nome = sb_data.get('nome')
sb_tel = sb_data.get('telefone')
sb_end = sb_data.get('endereco_logradouro')
sb_total = sb_data.get('total_orcamentos', 0)

print(f"   FIREBIRD -> Nome: {fb_nome}, Tel: {fb_tel}, End: {fb_end}, Total: {fb_total}")
print(f"   SUPABASE -> Nome: {sb_nome}, Tel: {sb_tel}, End: {sb_end}, Total: {sb_total}")

if fb_tel == sb_tel and fb_end == sb_end and fb_total == sb_total:
    print("   [OK] NELSON MORENO 100% CORRETO!")
else:
    print("   [ERRO] Dados ainda inconsistentes!")

# 2. Contar clientes com telefone
print("\n[2] Validando clientes COM telefone...")
conn = conectar_firebird()
cursor = conn.cursor()
cursor.execute("""
    SELECT COUNT(DISTINCT CT.CODIGO_CADASTRO)
    FROM CADASTRO_TELEFONE CT
    WHERE CT.TIPO_CADASTRO = 1
    AND CT.TELEFONE IS NOT NULL
""")
fb_com_tel = cursor.fetchone()[0]
conn.close()

url = f"{SUPABASE_URL}/rest/v1/prime_clientes?telefone=not.is.null&select=codigo_cliente_original"
response = requests.get(url, headers=headers)
sb_com_tel = len(response.json())

print(f"   FIREBIRD: {fb_com_tel} clientes com telefone")
print(f"   SUPABASE: {sb_com_tel} clientes com telefone")
print(f"   DIFERENCA: {fb_com_tel - sb_com_tel}")

# 3. Contar clientes com endereço
print("\n[3] Validando clientes COM endereco...")
conn = conectar_firebird()
cursor = conn.cursor()
cursor.execute("""
    SELECT COUNT(DISTINCT CE.CODIGO_CADASTRO)
    FROM CADASTRO_ENDERECO CE
    WHERE CE.TIPO_CADASTRO = 1
    AND CE.ENDERECO IS NOT NULL
""")
fb_com_end = cursor.fetchone()[0]
conn.close()

url = f"{SUPABASE_URL}/rest/v1/prime_clientes?endereco_logradouro=not.is.null&select=codigo_cliente_original"
response = requests.get(url, headers=headers)
sb_com_end = len(response.json())

print(f"   FIREBIRD: {fb_com_end} clientes com endereco")
print(f"   SUPABASE: {sb_com_end} clientes com endereco")
print(f"   DIFERENCA: {fb_com_end - sb_com_end}")

# 4. Teste de sincronização em tempo real
print("\n[4] Testando API de sincronizacao em producao...")
response = requests.post("https://sincro.oficialmed.com.br/sync", headers={'Content-Type': 'application/json'}, timeout=120)
if response.status_code == 200:
    data = response.json()
    clientes_inseridos = data.get('clientes', {}).get('inseridos', 0)
    print(f"   [OK] API funcionando! Clientes inseridos: {clientes_inseridos}")
else:
    print(f"   [ERRO] API retornou status {response.status_code}")

print("\n" + "="*100)
print("VALIDACAO CONCLUIDA!")
print("="*100)



