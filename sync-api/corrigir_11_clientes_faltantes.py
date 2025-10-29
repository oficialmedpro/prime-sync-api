#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correção dos 11 clientes faltantes identificados na análise
"""

import fdb
import requests

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

SUPABASE_URL = 'https://agdffspstbxeqhqtltvb.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA'

# Clientes com erro
clientes_telefone = [37545, 37546, 37547, 37548, 37549, 37550, 37551, 37553, 37554]
clientes_endereco = [37546, 3510]

todos_clientes = list(set(clientes_telefone + clientes_endereco))

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

print("="*80)
print("CORRIGINDO 11 CLIENTES FALTANTES")
print("="*80)

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

corrigidos = 0

for codigo in todos_clientes:
    print(f"\n[{corrigidos+1}/{len(todos_clientes)}] Cliente {codigo}...")
    
    # 1. Buscar dados do Firebird
    cursor.execute(f"""
        SELECT 
            C.CODIGO,
            C.NOMECLIENTE,
            C.CPF_CNPJ,
            C.DIANASCIMENTO,
            C.MESNASCIMENTO,
            C.ANONASCIMENTO,
            C.SEXO,
            C.EMAIL1,
            CE.NOMECIDADE,
            CE.UF
        FROM CLIENTE C
        LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
        WHERE C.CODIGO = {codigo}
    """)
    
    cliente = cursor.fetchone()
    if not cliente:
        print(f"   [ERRO] Cliente não encontrado no Firebird!")
        continue
    
    # 2. Buscar telefone
    cursor.execute(f"""
        SELECT TELEFONEPREFIXO, TELEFONE
        FROM CADASTRO_TELEFONE
        WHERE TIPO_CADASTRO = 1
        AND CODIGO_CADASTRO = {codigo}
        AND TELEFONE IS NOT NULL
        ROWS 1
    """)
    tel_row = cursor.fetchone()
    telefone = None
    if tel_row:
        telefone = (str(tel_row[0] or '') + str(tel_row[1] or '')).strip() or None
    
    # 3. Buscar endereço
    cursor.execute(f"""
        SELECT ENDERECO, NUMERO, CEP
        FROM CADASTRO_ENDERECO
        WHERE TIPO_CADASTRO = 1
        AND CODIGO_CADASTRO = {codigo}
        AND ENDERECO IS NOT NULL
        ROWS 1
    """)
    end_row = cursor.fetchone()
    
    # 4. Formatar data de nascimento
    data_nasc = None
    if cliente[3] and cliente[4] and cliente[5]:
        try:
            data_nasc = f"{int(cliente[5])}-{int(cliente[4]):02d}-{int(cliente[3]):02d}"
        except:
            pass
    
    # 5. Montar dados para atualização
    update_data = {
        'nome': cliente[1][:255] if cliente[1] else None,
        'cpf_cnpj': cliente[2][:20] if cliente[2] else None,
        'data_nascimento': data_nasc,
        'sexo': str(cliente[6])[:1] if cliente[6] else None,
        'email': cliente[7][:255] if cliente[7] else None,
        'telefone': telefone,
        'endereco_logradouro': end_row[0][:255] if (end_row and end_row[0]) else None,
        'endereco_numero': str(end_row[1]) if (end_row and end_row[1]) else None,
        'endereco_cep': end_row[2][:10] if (end_row and end_row[2]) else None,
        'endereco_cidade': cliente[8][:100] if cliente[8] else None,
        'endereco_estado': cliente[9][:2] if cliente[9] else None,
    }
    
    # 6. Atualizar no Supabase
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes?codigo_cliente_original=eq.{codigo}"
    response = requests.patch(url, headers=headers, json=update_data, timeout=30)
    
    if response.status_code in [200, 201, 204]:
        print(f"   [OK] Cliente {codigo} - {cliente[1]}")
        if telefone:
            print(f"      Tel: {telefone}")
        if end_row and end_row[0]:
            print(f"      End: {end_row[0][:50]}")
        corrigidos += 1
    else:
        print(f"   [ERRO] HTTP {response.status_code}: {response.text[:200]}")

conn.close()

print("\n" + "="*80)
print(f"RESULTADO: {corrigidos}/{len(todos_clientes)} clientes corrigidos!")
print("="*80)



