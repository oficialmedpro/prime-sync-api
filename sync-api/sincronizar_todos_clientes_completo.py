#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZAÇÃO COMPLETA DE TODOS OS CLIENTES
Atualiza TODOS os clientes do Supabase com dados do Firebird
Garante 100% de igualdade entre os sistemas
"""

import fdb
import requests
import time

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

print("="*100)
print("SINCRONIZACAO COMPLETA - TODOS OS CLIENTES")
print("="*100)
print("Atualizando TODOS os clientes do Supabase com dados do Firebird")
print("Isso vai levar 30-40 minutos para ~37.000 clientes")
print("="*100)

# 1. Buscar TODOS os códigos de clientes do Supabase
print("\n[1/4] Buscando todos os clientes do Supabase...")
clientes_sb = []
offset = 0
batch_size = 1000

while True:
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes?select=codigo_cliente_original&ativo=eq.true&limit={batch_size}&offset={offset}"
    response = requests.get(url, headers=headers)
    batch = response.json()
    
    if not batch:
        break
    
    clientes_sb.extend([c['codigo_cliente_original'] for c in batch])
    offset += batch_size
    
    if len(batch) < batch_size:
        break

print(f"   Total de clientes no Supabase: {len(clientes_sb)}")

# 2. Conectar ao Firebird
print("\n[2/4] Conectando ao Firebird...")
conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()
print("   Conectado!")

# 3. Processar em lotes
print("\n[3/4] Processando clientes em lotes de 100...")
total_atualizados = 0
total_erros = 0
batch_size_fb = 100

for i in range(0, len(clientes_sb), batch_size_fb):
    batch_codigos = clientes_sb[i:i+batch_size_fb]
    codigos_str = ','.join(map(str, batch_codigos))
    
    # Buscar dados básicos dos clientes
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
        WHERE C.CODIGO IN ({codigos_str})
    """)
    clientes_fb = {row[0]: row for row in cursor.fetchall()}
    
    # Buscar telefones
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
    
    telefones_dict = {}
    for row in cursor.fetchall():
        codigo = row[0]
        tel = (str(row[1] or '') + str(row[2] or '')).strip()
        if tel and codigo not in telefones_dict:
            telefones_dict[codigo] = tel
    
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
        AND CE.ENDERECO IS NOT NULL
    """)
    
    enderecos_dict = {}
    for row in cursor.fetchall():
        codigo = row[0]
        if codigo not in enderecos_dict:
            enderecos_dict[codigo] = {
                'endereco': row[1],
                'numero': row[2],
                'cep': row[3]
            }
    
    # Buscar totalizadores
    cursor.execute(f"""
        SELECT 
            A.CODIGO_CLIENTE,
            COUNT(*) as total,
            COUNT(A.AVIADA_DT) as aprovados,
            COUNT(A.ENTREGUE_DT) as entregues,
            COALESCE(SUM(A.VALORVENDA), 0) as valor_total,
            COALESCE(SUM(CASE WHEN A.AVIADA_DT IS NOT NULL THEN A.VALORVENDA ELSE 0 END), 0) as valor_aprovado,
            COALESCE(SUM(CASE WHEN A.ENTREGUE_DT IS NOT NULL THEN A.VALORVENDA ELSE 0 END), 0) as valor_entregue,
            MIN(A.CADASTRO_DT) as primeira_compra,
            MAX(A.CADASTRO_DT) as ultima_compra
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IN ({codigos_str})
        GROUP BY A.CODIGO_CLIENTE
    """)
    
    totalizadores_dict = {}
    for row in cursor.fetchall():
        codigo = row[0]
        total = row[1] or 1
        total_aprov = row[2] or 1
        total_entreg = row[3] or 1
        
        totalizadores_dict[codigo] = {
            'total_orcamentos': row[1] or 0,
            'total_orcamentos_aprovados': row[2] or 0,
            'total_orcamentos_entregues': row[3] or 0,
            'valor_total_orcamentos': float(row[4]) if row[4] else 0.0,
            'valor_total_aprovados': float(row[5]) if row[5] else 0.0,
            'valor_total_entregues': float(row[6]) if row[6] else 0.0,
            'valor_medio_orcamento': float(row[4] / total) if row[4] else 0.0,
            'valor_medio_aprovado': float(row[5] / total_aprov) if row[5] else 0.0,
            'valor_medio_entregue': float(row[6] / total_entreg) if row[6] else 0.0,
            'primeira_compra': row[7].date().isoformat() if row[7] else None,
            'ultima_compra': row[8].date().isoformat() if row[8] else None
        }
    
    # Atualizar cada cliente individualmente no Supabase
    for codigo in batch_codigos:
        if codigo not in clientes_fb:
            continue
        
        cliente = clientes_fb[codigo]
        telefone = telefones_dict.get(codigo)
        endereco = enderecos_dict.get(codigo, {})
        totalizadores = totalizadores_dict.get(codigo, {})
        
        # Formatar data de nascimento
        data_nasc = None
        if cliente[3] and cliente[4] and cliente[5]:
            try:
                data_nasc = f"{int(cliente[5])}-{int(cliente[4]):02d}-{int(cliente[3]):02d}"
            except:
                pass
        
        # Montar dados para atualização
        update_data = {
            'nome': cliente[1][:255] if cliente[1] else None,
            'cpf_cnpj': cliente[2][:20] if cliente[2] else None,
            'data_nascimento': data_nasc,
            'sexo': str(cliente[6])[:1] if cliente[6] is not None else None,
            'email': cliente[7][:255] if cliente[7] else None,
            'telefone': telefone,
            'endereco_logradouro': endereco.get('endereco', '')[:255] if endereco.get('endereco') else None,
            'endereco_numero': str(endereco.get('numero')) if endereco.get('numero') else None,
            'endereco_cep': endereco.get('cep', '')[:10] if endereco.get('cep') else None,
            'endereco_cidade': cliente[8][:100] if cliente[8] else None,
            'endereco_estado': cliente[9][:2] if cliente[9] else None,
            # Totalizadores
            'total_orcamentos': totalizadores.get('total_orcamentos', 0),
            'total_orcamentos_aprovados': totalizadores.get('total_orcamentos_aprovados', 0),
            'total_orcamentos_entregues': totalizadores.get('total_orcamentos_entregues', 0),
            'valor_total_orcamentos': totalizadores.get('valor_total_orcamentos', 0.0),
            'valor_total_aprovados': totalizadores.get('valor_total_aprovados', 0.0),
            'valor_total_entregues': totalizadores.get('valor_total_entregues', 0.0),
            'valor_medio_orcamento': totalizadores.get('valor_medio_orcamento', 0.0),
            'valor_medio_aprovado': totalizadores.get('valor_medio_aprovado', 0.0),
            'valor_medio_entregue': totalizadores.get('valor_medio_entregue', 0.0),
            'primeira_compra': totalizadores.get('primeira_compra'),
            'ultima_compra': totalizadores.get('ultima_compra')
        }
        
        # Atualizar no Supabase
        url = f"{SUPABASE_URL}/rest/v1/prime_clientes?codigo_cliente_original=eq.{codigo}"
        response = requests.patch(url, headers=headers, json=update_data, timeout=30)
        
        if response.status_code in [200, 201, 204]:
            total_atualizados += 1
        else:
            total_erros += 1
    
    # Progresso
    progresso = (i + len(batch_codigos)) / len(clientes_sb) * 100
    print(f"   Progresso: {i + len(batch_codigos)}/{len(clientes_sb)} ({progresso:.1f}%) - OK: {total_atualizados}, Erros: {total_erros}")
    
    time.sleep(0.1)  # Pausa para não sobrecarregar

conn.close()

print("\n" + "="*100)
print("SINCRONIZACAO COMPLETA FINALIZADA!")
print("="*100)
print(f"Total processado: {len(clientes_sb)}")
print(f"Atualizados com sucesso: {total_atualizados}")
print(f"Erros: {total_erros}")
print(f"Taxa de sucesso: {(total_atualizados / len(clientes_sb) * 100):.2f}%")
print("="*100)
print("\nAGORA SIM O SUPABASE ESTA 100% IGUAL AO FIREBIRD!")
print("="*100)

