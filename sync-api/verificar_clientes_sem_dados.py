#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar clientes SEM dados no Supabase
e confirmar se eles REALMENTE não têm esses dados no Firebird

Objetivo: Descobrir se os dados estão faltando legitimamente ou se é erro de sincronização
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
print("VERIFICANDO CLIENTES SEM DADOS NO SUPABASE")
print("Confirmando se eles REALMENTE nao tem esses dados no Firebird")
print("=" * 120)

try:
    # 1. Buscar clientes SEM telefone no Supabase
    print("\n[1/5] Buscando clientes SEM telefone no Supabase...")
    
    clientes_sem_telefone = []
    offset = 0
    limit = 1000
    
    while True:
        url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
        params = {
            'select': 'codigo_cliente_original,nome',
            'telefone': 'is.null',
            'order': 'codigo_cliente_original',
            'limit': limit,
            'offset': offset
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            dados = response.json()
            if not dados:
                break
            clientes_sem_telefone.extend(dados)
            offset += limit
            if len(clientes_sem_telefone) % 5000 == 0:
                print(f"      {len(clientes_sem_telefone)} clientes sem telefone encontrados...")
        else:
            print(f"      [ERRO] {response.status_code}")
            break
    
    print(f"      [OK] {len(clientes_sem_telefone)} clientes SEM telefone no Supabase")
    
    # 2. Buscar clientes SEM endereco no Supabase
    print("\n[2/5] Buscando clientes SEM endereco no Supabase...")
    
    clientes_sem_endereco = []
    offset = 0
    
    while True:
        url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
        params = {
            'select': 'codigo_cliente_original,nome',
            'endereco_logradouro': 'is.null',
            'order': 'codigo_cliente_original',
            'limit': limit,
            'offset': offset
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            dados = response.json()
            if not dados:
                break
            clientes_sem_endereco.extend(dados)
            offset += limit
            if len(clientes_sem_endereco) % 5000 == 0:
                print(f"      {len(clientes_sem_endereco)} clientes sem endereco encontrados...")
        else:
            print(f"      [ERRO] {response.status_code}")
            break
    
    print(f"      [OK] {len(clientes_sem_endereco)} clientes SEM endereco no Supabase")
    
    # 3. Verificar no Firebird se esses clientes TEM os dados
    print(f"\n[3/5] Verificando no Firebird...")
    
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    cursor = conn.cursor()
    
    # Verificar telefones
    print(f"\n      [3a] Verificando telefones no Firebird...")
    codigos_sem_tel = [c['codigo_cliente_original'] for c in clientes_sem_telefone]
    
    tem_telefone_firebird = []
    nao_tem_telefone_firebird = []
    
    batch_size = 500
    total_batches = (len(codigos_sem_tel) + batch_size - 1) // batch_size
    
    for i in range(0, len(codigos_sem_tel), batch_size):
        batch = codigos_sem_tel[i:i + batch_size]
        codigos_str = ','.join(map(str, batch))
        
        if (i // batch_size + 1) % 10 == 0:
            print(f"          Processando lote {(i//batch_size)+1}/{total_batches}...")
        
        # Buscar na tabela CADASTRO_TELEFONE
        cursor.execute(f"""
            SELECT DISTINCT CT.CODIGO_CADASTRO
            FROM CADASTRO_TELEFONE CT
            WHERE CT.TIPO_CADASTRO = 1
            AND CT.CODIGO_CADASTRO IN ({codigos_str})
            AND (CT.TELEFONE IS NOT NULL OR CT.TELEFONEPREFIXO IS NOT NULL)
        """)
        
        codigos_com_tel = [row[0] for row in cursor.fetchall()]
        tem_telefone_firebird.extend(codigos_com_tel)
    
    # Clientes que não têm telefone nem no Supabase nem no Firebird (correto)
    codigos_com_tel_fb = set(tem_telefone_firebird)
    nao_tem_telefone_firebird = [c for c in codigos_sem_tel if c not in codigos_com_tel_fb]
    
    print(f"          [OK] {len(tem_telefone_firebird)} TEM telefone no Firebird (ERRO DE SINC)")
    print(f"          [OK] {len(nao_tem_telefone_firebird)} NAO TEM telefone no Firebird (CORRETO)")
    
    # Verificar endereços
    print(f"\n      [3b] Verificando enderecos no Firebird...")
    codigos_sem_end = [c['codigo_cliente_original'] for c in clientes_sem_endereco]
    
    tem_endereco_firebird = []
    nao_tem_endereco_firebird = []
    
    total_batches = (len(codigos_sem_end) + batch_size - 1) // batch_size
    
    for i in range(0, len(codigos_sem_end), batch_size):
        batch = codigos_sem_end[i:i + batch_size]
        codigos_str = ','.join(map(str, batch))
        
        if (i // batch_size + 1) % 10 == 0:
            print(f"          Processando lote {(i//batch_size)+1}/{total_batches}...")
        
        # Buscar na tabela CADASTRO_ENDERECO
        cursor.execute(f"""
            SELECT DISTINCT CE.CODIGO_CADASTRO
            FROM CADASTRO_ENDERECO CE
            WHERE CE.TIPO_CADASTRO = 1
            AND CE.CODIGO_CADASTRO IN ({codigos_str})
            AND CE.ENDERECO IS NOT NULL
        """)
        
        codigos_com_end = [row[0] for row in cursor.fetchall()]
        tem_endereco_firebird.extend(codigos_com_end)
    
    codigos_com_end_fb = set(tem_endereco_firebird)
    nao_tem_endereco_firebird = [c for c in codigos_sem_end if c not in codigos_com_end_fb]
    
    print(f"          [OK] {len(tem_endereco_firebird)} TEM endereco no Firebird (ERRO DE SINC)")
    print(f"          [OK] {len(nao_tem_endereco_firebird)} NAO TEM endereco no Firebird (CORRETO)")
    
    conn.close()
    
    # 4. Resultados detalhados
    print("\n" + "=" * 120)
    print("[4/5] RESULTADOS DETALHADOS")
    print("=" * 120)
    
    print(f"\n[TELEFONES]")
    print(f"  Total SEM telefone no Supabase: {len(clientes_sem_telefone)}")
    print(f"  Desses, quantos TEM no Firebird: {len(tem_telefone_firebird)} ({len(tem_telefone_firebird)/len(clientes_sem_telefone)*100:.1f}%) - ERRO!")
    print(f"  Desses, quantos NAO TEM no Firebird: {len(nao_tem_telefone_firebird)} ({len(nao_tem_telefone_firebird)/len(clientes_sem_telefone)*100:.1f}%) - OK!")
    
    print(f"\n[ENDERECOS]")
    print(f"  Total SEM endereco no Supabase: {len(clientes_sem_endereco)}")
    print(f"  Desses, quantos TEM no Firebird: {len(tem_endereco_firebird)} ({len(tem_endereco_firebird)/len(clientes_sem_endereco)*100:.1f}%) - ERRO!")
    print(f"  Desses, quantos NAO TEM no Firebird: {len(nao_tem_endereco_firebird)} ({len(nao_tem_endereco_firebird)/len(clientes_sem_endereco)*100:.1f}%) - OK!")
    
    # 5. Resumo
    print("\n" + "=" * 120)
    print("[5/5] RESUMO FINAL")
    print("=" * 120)
    
    total_clientes = 37457
    
    print(f"\nTotal de clientes no sistema: {total_clientes}")
    print(f"\nErros de sincronizacao encontrados:")
    print(f"  - Telefones faltando: {len(tem_telefone_firebird)} clientes ({len(tem_telefone_firebird)/total_clientes*100:.2f}%)")
    print(f"  - Enderecos faltando: {len(tem_endereco_firebird)} clientes ({len(tem_endereco_firebird)/total_clientes*100:.2f}%)")
    
    print(f"\nDados corretamente vazios (cliente realmente nao tem):")
    print(f"  - Sem telefone (correto): {len(nao_tem_telefone_firebird)} clientes ({len(nao_tem_telefone_firebird)/total_clientes*100:.1f}%)")
    print(f"  - Sem endereco (correto): {len(nao_tem_endereco_firebird)} clientes ({len(nao_tem_endereco_firebird)/total_clientes*100:.1f}%)")
    
    # Salvar lista de clientes para corrigir
    if tem_telefone_firebird or tem_endereco_firebird:
        print("\n[INFO] Salvando lista de codigos que precisam correcao urgente...")
        
        codigos_urgentes = set()
        codigos_urgentes.update(tem_telefone_firebird)
        codigos_urgentes.update(tem_endereco_firebird)
        
        with open('clientes_erro_sincronizacao_urgente.txt', 'w') as f:
            f.write(f"# Clientes com ERRO DE SINCRONIZACAO - Tem dados no Firebird mas NAO no Supabase\n")
            f.write(f"# Gerado em: {datetime.now()}\n")
            f.write(f"# Total: {len(codigos_urgentes)} clientes\n")
            f.write(f"# {len(tem_telefone_firebird)} sem telefone | {len(tem_endereco_firebird)} sem endereco\n\n")
            for codigo in sorted(codigos_urgentes):
                f.write(f"{codigo}\n")
        
        print(f"      [OK] Lista salva: clientes_erro_sincronizacao_urgente.txt ({len(codigos_urgentes)} clientes)")
    
    print("\n" + "=" * 120)
    print("[OK] ANALISE CONCLUIDA")
    print("=" * 120)

except Exception as e:
    print(f"\n[ERRO] {str(e)}")
    import traceback
    traceback.print_exc()



