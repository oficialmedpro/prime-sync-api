#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comparar dados entre Firebird e Supabase
e identificar EXATAMENTE o que está faltando

Compara:
- Telefones (tabela CADASTRO_TELEFONE)
- Endereços (tabela CADASTRO_ENDERECO)
- Data de nascimento
- E-mail
- CPF
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

print("=" * 120)
print("COMPARACAO DE DADOS: FIREBIRD vs SUPABASE")
print("Identificando dados que existem no Firebird mas estao faltando no Supabase")
print("=" * 120)

try:
    # 1. Conectar ao Firebird
    print("\n[1/6] Conectando ao Firebird...")
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    cursor = conn.cursor()
    print("      [OK] Conectado ao Firebird")

    # 2. Buscar clientes do Supabase
    print("\n[2/6] Buscando clientes do Supabase...")
    
    # Buscar em lotes
    todos_clientes_sb = []
    offset = 0
    limit = 1000
    
    while True:
        url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
        params = {
            'select': 'codigo_cliente_original,nome,telefone,endereco_logradouro,endereco_cep,data_nascimento,email,cpf_cnpj',
            'order': 'codigo_cliente_original',
            'limit': limit,
            'offset': offset
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            dados = response.json()
            if not dados:
                break
            todos_clientes_sb.extend(dados)
            offset += limit
            print(f"      Carregados {len(todos_clientes_sb)} clientes...")
        else:
            print(f"      [ERRO] {response.status_code}")
            break
    
    print(f"      [OK] {len(todos_clientes_sb)} clientes carregados do Supabase")
    
    # Criar dicionário para acesso rápido
    clientes_sb_dict = {c['codigo_cliente_original']: c for c in todos_clientes_sb}
    codigos_sb = list(clientes_sb_dict.keys())
    
    # 3. Buscar dados do Firebird
    print(f"\n[3/6] Buscando dados dos {len(codigos_sb)} clientes no Firebird...")
    
    # Buscar em lotes de 500
    batch_size = 500
    total_batches = (len(codigos_sb) + batch_size - 1) // batch_size
    
    clientes_fb = []
    telefones_fb = {}
    enderecos_fb = {}
    
    for i in range(0, len(codigos_sb), batch_size):
        batch = codigos_sb[i:i + batch_size]
        codigos_str = ','.join(map(str, batch))
        
        print(f"      Processando lote {(i//batch_size)+1}/{total_batches}...")
        
        # Buscar dados básicos
        cursor.execute(f"""
            SELECT 
                C.CODIGO,
                C.NOMECLIENTE,
                C.CPF_CNPJ,
                C.DIANASCIMENTO,
                C.MESNASCIMENTO,
                C.ANONASCIMENTO,
                C.EMAIL1
            FROM CLIENTE C
            WHERE C.CODIGO IN ({codigos_str})
        """)
        clientes_fb.extend(cursor.fetchall())
        
        # Buscar telefones
        cursor.execute(f"""
            SELECT 
                CT.CODIGO_CADASTRO,
                CT.TELEFONEPREFIXO,
                CT.TELEFONE
            FROM CADASTRO_TELEFONE CT
            WHERE CT.TIPO_CADASTRO = 1
            AND CT.CODIGO_CADASTRO IN ({codigos_str})
        """)
        
        for tel in cursor.fetchall():
            codigo = tel[0]
            prefixo = str(tel[1]).strip() if tel[1] else ""
            numero = str(tel[2]).strip() if tel[2] else ""
            telefone = (prefixo + numero).strip()
            
            if telefone and codigo not in telefones_fb:
                telefones_fb[codigo] = telefone
        
        # Buscar endereços
        cursor.execute(f"""
            SELECT 
                CE.CODIGO_CADASTRO,
                CE.ENDERECO,
                CE.NUMERO,
                CE.CEP
            FROM CADASTRO_ENDERECO CE
            WHERE CE.TIPO_CADASTRO = 1
            AND CE.CODIGO_CADASTRO IN ({codigos_str})
        """)
        
        for end in cursor.fetchall():
            codigo = end[0]
            if codigo not in enderecos_fb:
                enderecos_fb[codigo] = {
                    'endereco': end[1],
                    'numero': end[2],
                    'cep': end[3]
                }
    
    conn.close()
    print(f"      [OK] Dados do Firebird carregados")
    print(f"      - {len(clientes_fb)} clientes")
    print(f"      - {len(telefones_fb)} telefones")
    print(f"      - {len(enderecos_fb)} enderecos")

    # 4. Comparar dados
    print(f"\n[4/6] Comparando dados...")
    
    faltam_telefone = []
    faltam_endereco = []
    faltam_data_nasc = []
    faltam_email = []
    faltam_cpf = []
    
    clientes_fb_dict = {}
    for cli in clientes_fb:
        codigo = cli[0]
        clientes_fb_dict[codigo] = {
            'nome': cli[1],
            'cpf': cli[2],
            'dia_nasc': cli[3],
            'mes_nasc': cli[4],
            'ano_nasc': cli[5],
            'email': cli[6]
        }
    
    for codigo, cli_sb in clientes_sb_dict.items():
        cli_fb = clientes_fb_dict.get(codigo)
        
        if not cli_fb:
            continue
        
        # Verificar telefone
        telefone_fb = telefones_fb.get(codigo)
        telefone_sb = cli_sb.get('telefone')
        
        if telefone_fb and not telefone_sb:
            faltam_telefone.append({
                'codigo': codigo,
                'nome': cli_sb.get('nome'),
                'telefone_fb': telefone_fb
            })
        
        # Verificar endereço
        endereco_fb = enderecos_fb.get(codigo)
        endereco_sb = cli_sb.get('endereco_logradouro')
        
        if endereco_fb and not endereco_sb:
            faltam_endereco.append({
                'codigo': codigo,
                'nome': cli_sb.get('nome'),
                'endereco_fb': endereco_fb.get('endereco'),
                'cep_fb': endereco_fb.get('cep')
            })
        
        # Verificar data de nascimento
        data_nasc_fb = None
        if cli_fb['dia_nasc'] and cli_fb['mes_nasc'] and cli_fb['ano_nasc']:
            data_nasc_fb = f"{cli_fb['ano_nasc']}-{cli_fb['mes_nasc']:02d}-{cli_fb['dia_nasc']:02d}"
        
        data_nasc_sb = cli_sb.get('data_nascimento')
        
        if data_nasc_fb and not data_nasc_sb:
            faltam_data_nasc.append({
                'codigo': codigo,
                'nome': cli_sb.get('nome'),
                'data_nasc_fb': data_nasc_fb
            })
        
        # Verificar email
        email_fb = cli_fb.get('email')
        email_sb = cli_sb.get('email')
        
        if email_fb and not email_sb:
            faltam_email.append({
                'codigo': codigo,
                'nome': cli_sb.get('nome'),
                'email_fb': email_fb
            })
        
        # Verificar CPF
        cpf_fb = cli_fb.get('cpf')
        cpf_sb = cli_sb.get('cpf_cnpj')
        
        if cpf_fb and not cpf_sb:
            faltam_cpf.append({
                'codigo': codigo,
                'nome': cli_sb.get('nome'),
                'cpf_fb': cpf_fb
            })

    # 5. Exibir resultados
    print(f"\n[5/6] Resultados da comparacao:")
    print("=" * 120)
    
    print(f"\n[TELEFONES FALTANDO]")
    print(f"Total: {len(faltam_telefone)} clientes tem telefone no Firebird mas NAO no Supabase")
    if faltam_telefone:
        print("\nPrimeiros 10 exemplos:")
        for i, item in enumerate(faltam_telefone[:10], 1):
            print(f"  {i}. Codigo: {item['codigo']} | Nome: {item['nome'][:40]:40} | Telefone FB: {item['telefone_fb']}")
    
    print(f"\n[ENDERECOS FALTANDO]")
    print(f"Total: {len(faltam_endereco)} clientes tem endereco no Firebird mas NAO no Supabase")
    if faltam_endereco:
        print("\nPrimeiros 10 exemplos:")
        for i, item in enumerate(faltam_endereco[:10], 1):
            print(f"  {i}. Codigo: {item['codigo']} | Nome: {item['nome'][:40]:40} | Endereco FB: {item['endereco_fb'][:50]}")
    
    print(f"\n[DATA DE NASCIMENTO FALTANDO]")
    print(f"Total: {len(faltam_data_nasc)} clientes tem data de nascimento no Firebird mas NAO no Supabase")
    if faltam_data_nasc:
        print("\nPrimeiros 10 exemplos:")
        for i, item in enumerate(faltam_data_nasc[:10], 1):
            print(f"  {i}. Codigo: {item['codigo']} | Nome: {item['nome'][:40]:40} | Data FB: {item['data_nasc_fb']}")
    
    print(f"\n[E-MAIL FALTANDO]")
    print(f"Total: {len(faltam_email)} clientes tem e-mail no Firebird mas NAO no Supabase")
    if faltam_email:
        print("\nPrimeiros 10 exemplos:")
        for i, item in enumerate(faltam_email[:10], 1):
            print(f"  {i}. Codigo: {item['codigo']} | Nome: {item['nome'][:40]:40} | E-mail FB: {item['email_fb']}")
    
    print(f"\n[CPF FALTANDO]")
    print(f"Total: {len(faltam_cpf)} clientes tem CPF no Firebird mas NAO no Supabase")
    if faltam_cpf:
        print("\nPrimeiros 10 exemplos:")
        for i, item in enumerate(faltam_cpf[:10], 1):
            print(f"  {i}. Codigo: {item['codigo']} | Nome: {item['nome'][:40]:40} | CPF FB: {item['cpf_fb']}")

    # 6. Resumo
    print("\n" + "=" * 120)
    print("[6/6] RESUMO GERAL")
    print("=" * 120)
    print(f"\nTotal de clientes analisados: {len(clientes_sb_dict)}")
    print(f"\nDados faltando no Supabase:")
    print(f"  - Telefones:         {len(faltam_telefone):>6} clientes ({len(faltam_telefone)/len(clientes_sb_dict)*100:.1f}%)")
    print(f"  - Enderecos:         {len(faltam_endereco):>6} clientes ({len(faltam_endereco)/len(clientes_sb_dict)*100:.1f}%)")
    print(f"  - Data Nascimento:   {len(faltam_data_nasc):>6} clientes ({len(faltam_data_nasc)/len(clientes_sb_dict)*100:.1f}%)")
    print(f"  - E-mail:            {len(faltam_email):>6} clientes ({len(faltam_email)/len(clientes_sb_dict)*100:.1f}%)")
    print(f"  - CPF:               {len(faltam_cpf):>6} clientes ({len(faltam_cpf)/len(clientes_sb_dict)*100:.1f}%)")
    
    print("\n" + "=" * 120)
    print("[OK] ANALISE CONCLUIDA")
    print("=" * 120)
    
    # Salvar lista de códigos para correção
    if faltam_telefone or faltam_endereco:
        print("\n[INFO] Salvando lista de codigos para correcao...")
        
        codigos_corrigir = set()
        codigos_corrigir.update([item['codigo'] for item in faltam_telefone])
        codigos_corrigir.update([item['codigo'] for item in faltam_endereco])
        
        with open('clientes_para_corrigir.txt', 'w') as f:
            f.write(f"# Clientes que precisam ser corrigidos\n")
            f.write(f"# Gerado em: {datetime.now()}\n")
            f.write(f"# Total: {len(codigos_corrigir)} clientes\n\n")
            for codigo in sorted(codigos_corrigir):
                f.write(f"{codigo}\n")
        
        print(f"      [OK] Lista salva em: clientes_para_corrigir.txt ({len(codigos_corrigir)} clientes)")

except Exception as e:
    print(f"\n[ERRO] {str(e)}")
    import traceback
    traceback.print_exc()



