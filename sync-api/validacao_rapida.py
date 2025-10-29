#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validacao RAPIDA - Cliente Nelson Moreno
Verifica se a correcao funcionou

Data: 28/10/2025
"""

import fdb
import requests

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

SUPABASE_URL = 'https://agdffspstbxeqhqtltvb.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA'

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}

print("="*80)
print("VALIDACAO RAPIDA - NELSON MORENO (37479)")
print("="*80)

# FIREBIRD
conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

cursor.execute("""
    SELECT CT.TELEFONEPREFIXO, CT.TELEFONE
    FROM CADASTRO_TELEFONE CT
    WHERE CT.TIPO_CADASTRO = 1 AND CT.CODIGO_CADASTRO = 37479
""")
tel_fb = cursor.fetchone()
telefone_fb = (str(tel_fb[0]) + str(tel_fb[1])).strip() if tel_fb else None

cursor.execute("""
    SELECT CE.ENDERECO FROM CADASTRO_ENDERECO CE
    WHERE CE.TIPO_CADASTRO = 1 AND CE.CODIGO_CADASTRO = 37479
""")
end_fb = cursor.fetchone()
endereco_fb = end_fb[0] if end_fb else None

cursor.execute("""
    SELECT COUNT(*) FROM ATENDIMENTO_A1 WHERE CODIGO_CLIENTE = 37479
""")
total_fb = cursor.fetchone()[0]

conn.close()

# SUPABASE
response = requests.get(
    f"{SUPABASE_URL}/rest/v1/prime_clientes",
    headers=headers,
    params={'select': '*', 'codigo_cliente_original': 'eq.37479'}
)

if response.status_code == 200 and response.json():
    cliente_sb = response.json()[0]
    
    print("\nFIREBIRD:")
    print(f"  Telefone: {telefone_fb}")
    print(f"  Endereco: {endereco_fb}")
    print(f"  Total Orcamentos: {total_fb}")
    
    print("\nSUPABASE:")
    print(f"  Telefone: {cliente_sb.get('telefone')}")
    print(f"  Endereco: {cliente_sb.get('endereco_logradouro')}")
    print(f"  Total Orcamentos: {cliente_sb.get('total_orcamentos')}")
    
    print("\nRESULTADO:")
    ok = True
    if telefone_fb and not cliente_sb.get('telefone'):
        print("  [ERRO] Telefone ainda faltando!")
        ok = False
    if endereco_fb and not cliente_sb.get('endereco_logradouro'):
        print("  [ERRO] Endereco ainda faltando!")
        ok = False
    if total_fb != cliente_sb.get('total_orcamentos', 0):
        print(f"  [ERRO] Total diferente! FB:{total_fb} SB:{cliente_sb.get('total_orcamentos')}")
        ok = False
    
    if ok:
        print("  [OK] TUDO CERTO! Cliente corrigido com sucesso!")
    
    print("="*80)
else:
    print("\n[ERRO] Nao conseguiu buscar cliente do Supabase!")
    print("="*80)


