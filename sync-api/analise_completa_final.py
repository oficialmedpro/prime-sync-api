#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISE COMPLETA - Validação Firebird vs Supabase
Verifica TODOS os clientes sem dados no Supabase para confirmar
se realmente não têm no Firebird também
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
}

print("="*100)
print("ANALISE COMPLETA - VALIDACAO FIREBIRD vs SUPABASE")
print("="*100)
print("Isso pode levar alguns minutos...")
print("="*100)

# ============================================================================
# PARTE 1: TELEFONES
# ============================================================================
print("\n[1/2] ANALISANDO TELEFONES...")
print("-"*100)

# Buscar TODOS os clientes sem telefone no Supabase (em lotes)
print("   Buscando clientes SEM telefone no Supabase...")
clientes_sem_tel_sb = []
offset = 0
batch_size = 1000

while True:
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes?telefone=is.null&ativo=eq.true&select=codigo_cliente_original&limit={batch_size}&offset={offset}"
    response = requests.get(url, headers=headers)
    batch = response.json()
    
    if not batch:
        break
    
    clientes_sem_tel_sb.extend([c['codigo_cliente_original'] for c in batch])
    offset += batch_size
    print(f"      Processados: {len(clientes_sem_tel_sb)} clientes...")
    
    if len(batch) < batch_size:
        break

print(f"\n   Total de clientes SEM telefone no Supabase: {len(clientes_sem_tel_sb)}")

# Verificar no Firebird quantos desses TÊM telefone
print("   Verificando no Firebird quantos TÊM telefone...")

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

# Processar em lotes de 500 (limite SQL IN)
erros_telefone = []
batch_size_fb = 500

for i in range(0, len(clientes_sem_tel_sb), batch_size_fb):
    batch = clientes_sem_tel_sb[i:i+batch_size_fb]
    codigos_str = ','.join(map(str, batch))
    
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
    
    for row in cursor.fetchall():
        codigo = row[0]
        tel = (str(row[1] or '') + str(row[2] or '')).strip()
        if tel:
            erros_telefone.append({'codigo': codigo, 'telefone': tel})
    
    if (i // batch_size_fb + 1) % 5 == 0:
        print(f"      Processados: {i + len(batch)}/{len(clientes_sem_tel_sb)} clientes...")

conn.close()

print(f"\n   RESULTADO TELEFONES:")
print(f"   - Clientes SEM telefone no Supabase: {len(clientes_sem_tel_sb)}")
print(f"   - Desses, TÊM telefone no Firebird (ERRO): {len(erros_telefone)}")
print(f"   - Desses, NÃO TÊM no Firebird também (OK): {len(clientes_sem_tel_sb) - len(erros_telefone)}")
print(f"   - Taxa de acerto: {((len(clientes_sem_tel_sb) - len(erros_telefone)) / len(clientes_sem_tel_sb) * 100):.2f}%")

if erros_telefone:
    print(f"\n   [AVISO] {len(erros_telefone)} clientes com erro de sincronização (telefone)!")
    print("   Primeiros 10:")
    for erro in erros_telefone[:10]:
        print(f"      - Cliente {erro['codigo']}: {erro['telefone']}")
else:
    print(f"\n   [OK] PERFEITO! Todos os clientes sem telefone no Supabase também não têm no Firebird!")

# ============================================================================
# PARTE 2: ENDEREÇOS
# ============================================================================
print("\n" + "-"*100)
print("[2/2] ANALISANDO ENDEREÇOS...")
print("-"*100)

# Buscar TODOS os clientes sem endereço no Supabase (em lotes)
print("   Buscando clientes SEM endereço no Supabase...")
clientes_sem_end_sb = []
offset = 0
batch_size = 1000

while True:
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes?endereco_logradouro=is.null&ativo=eq.true&select=codigo_cliente_original&limit={batch_size}&offset={offset}"
    response = requests.get(url, headers=headers)
    batch = response.json()
    
    if not batch:
        break
    
    clientes_sem_end_sb.extend([c['codigo_cliente_original'] for c in batch])
    offset += batch_size
    print(f"      Processados: {len(clientes_sem_end_sb)} clientes...")
    
    if len(batch) < batch_size:
        break

print(f"\n   Total de clientes SEM endereço no Supabase: {len(clientes_sem_end_sb)}")

# Verificar no Firebird quantos desses TÊM endereço
print("   Verificando no Firebird quantos TÊM endereço...")

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)
cursor = conn.cursor()

# Processar em lotes de 500
erros_endereco = []
batch_size_fb = 500

for i in range(0, len(clientes_sem_end_sb), batch_size_fb):
    batch = clientes_sem_end_sb[i:i+batch_size_fb]
    codigos_str = ','.join(map(str, batch))
    
    cursor.execute(f"""
        SELECT 
            CE.CODIGO_CADASTRO,
            CE.ENDERECO
        FROM CADASTRO_ENDERECO CE
        WHERE CE.TIPO_CADASTRO = 1
        AND CE.CODIGO_CADASTRO IN ({codigos_str})
        AND CE.ENDERECO IS NOT NULL
    """)
    
    for row in cursor.fetchall():
        codigo = row[0]
        end = str(row[1] or '').strip()
        if end:
            erros_endereco.append({'codigo': codigo, 'endereco': end[:50]})
    
    if (i // batch_size_fb + 1) % 5 == 0:
        print(f"      Processados: {i + len(batch)}/{len(clientes_sem_end_sb)} clientes...")

conn.close()

print(f"\n   RESULTADO ENDEREÇOS:")
print(f"   - Clientes SEM endereço no Supabase: {len(clientes_sem_end_sb)}")
print(f"   - Desses, TÊM endereço no Firebird (ERRO): {len(erros_endereco)}")
print(f"   - Desses, NÃO TÊM no Firebird também (OK): {len(clientes_sem_end_sb) - len(erros_endereco)}")
print(f"   - Taxa de acerto: {((len(clientes_sem_end_sb) - len(erros_endereco)) / len(clientes_sem_end_sb) * 100):.2f}%")

if erros_endereco:
    print(f"\n   [AVISO] {len(erros_endereco)} clientes com erro de sincronização (endereço)!")
    print("   Primeiros 10:")
    for erro in erros_endereco[:10]:
        print(f"      - Cliente {erro['codigo']}: {erro['endereco']}")
else:
    print(f"\n   [OK] PERFEITO! Todos os clientes sem endereço no Supabase também não têm no Firebird!")

# ============================================================================
# RESUMO FINAL
# ============================================================================
print("\n" + "="*100)
print("RESUMO FINAL DA ANÁLISE")
print("="*100)

total_erros = len(erros_telefone) + len(erros_endereco)
total_analisados = len(clientes_sem_tel_sb) + len(clientes_sem_end_sb)
taxa_acerto = ((total_analisados - total_erros) / total_analisados * 100) if total_analisados > 0 else 0

print(f"\nClientes analisados: {total_analisados:,}")
print(f"Erros de sincronização encontrados: {total_erros:,}")
print(f"Taxa de acerto geral: {taxa_acerto:.2f}%")

if total_erros == 0:
    print("\n" + "="*100)
    print("RESULTADO: SINCRONIZAÇÃO 100% CORRETA!")
    print("="*100)
    print("Todos os clientes sem dados no Supabase também NÃO TÊM esses dados no Firebird.")
    print("O sistema está sincronizado perfeitamente!")
else:
    print("\n" + "="*100)
    print(f"RESULTADO: {total_erros:,} ERROS ENCONTRADOS ({(total_erros/total_analisados*100):.2f}%)")
    print("="*100)
    print("Recomendação: Executar script de correção para esses clientes.")
    
    # Salvar lista de códigos com erro
    with open('clientes_erro_sincronizacao_analise_completa.txt', 'w') as f:
        f.write("# Clientes com erro de sincronização\n")
        f.write(f"# Total: {total_erros}\n\n")
        f.write("# Telefones:\n")
        for erro in erros_telefone:
            f.write(f"{erro['codigo']}\n")
        f.write("\n# Endereços:\n")
        for erro in erros_endereco:
            f.write(f"{erro['codigo']}\n")
    
    print(f"Lista salva em: clientes_erro_sincronizacao_analise_completa.txt")

print("="*100)



