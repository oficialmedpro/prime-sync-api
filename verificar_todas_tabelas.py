#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar TODAS as tabelas para garantir sincronização 100%
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
    'Content-Type': 'application/json'
}

def get_ultimo_supabase(tabela, campo):
    """Busca último ID no Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/{tabela}"

    params = {
        'select': campo,
        'order': f'{campo}.desc',
        'limit': 1
    }

    # Para clientes, ignorar códigos especiais
    if tabela == 'prime_clientes':
        params[campo] = 'lt.500000'

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code in [200, 206]:
        dados = resp.json()
        return dados[0][campo] if dados else 0
    return 0

def verificar_clientes(conn):
    """Verifica clientes"""
    print("\n" + "="*80)
    print("1. CLIENTES (prime_clientes)")
    print("="*80)

    ultimo = get_ultimo_supabase('prime_clientes', 'codigo_cliente_original')
    print(f"   Último no Supabase: {ultimo}")

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM CLIENTE C
        WHERE C.ATIVO = -1
        AND C.CODIGO > {ultimo}
        AND C.CODIGO < 500000
    """)

    novos = cursor.fetchone()[0]
    print(f"   Novos no Firebird:  {novos}")

    if novos == 0:
        print("   Status: OK (tudo sincronizado)")
    else:
        print(f"   Status: PENDENTE ({novos} clientes para sincronizar)")

    return novos

def verificar_pedidos(conn):
    """Verifica pedidos"""
    print("\n" + "="*80)
    print("2. PEDIDOS (prime_pedidos)")
    print("="*80)

    ultimo = get_ultimo_supabase('prime_pedidos', 'codigo_orcamento_original')
    print(f"   Último no Supabase: {ultimo}")

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IS NOT NULL
        AND A.CODIGO > {ultimo}
    """)

    novos = cursor.fetchone()[0]
    print(f"   Novos no Firebird:  {novos}")

    if novos == 0:
        print("   Status: OK (tudo sincronizado)")
    else:
        print(f"   Status: PENDENTE ({novos} pedidos para sincronizar)")

    return novos

def verificar_formulas(conn):
    """Verifica fórmulas"""
    print("\n" + "="*80)
    print("3. FORMULAS (prime_formulas)")
    print("="*80)

    ultimo = get_ultimo_supabase('prime_formulas', 'codigo_orcamento_original')
    print(f"   Último no Supabase: {ultimo}")

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(DISTINCT A.CODIGO)
        FROM ATENDIMENTO_A3 A
        WHERE A.CODIGO > {ultimo}
    """)

    novos = cursor.fetchone()[0]
    print(f"   Novos no Firebird:  {novos}")

    if novos == 0:
        print("   Status: OK (tudo sincronizado)")
    else:
        print(f"   Status: PENDENTE ({novos} formulas para sincronizar)")

    return novos

def verificar_formulas_itens(conn):
    """Verifica itens de fórmulas"""
    print("\n" + "="*80)
    print("4. FORMULAS ITENS (prime_formulas_itens)")
    print("="*80)

    ultimo = get_ultimo_supabase('prime_formulas_itens', 'codigo_atendimento_original')
    print(f"   Último no Supabase: {ultimo}")

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM ATENDIMENTO_A3 A3
        WHERE A3.CODIGO_ATEND_A1 > {ultimo}
        AND A3.CODIGO_ATEND_A1 IS NOT NULL
    """)

    novos = cursor.fetchone()[0]
    print(f"   Novos no Firebird:  {novos}")

    if novos == 0:
        print("   Status: OK (tudo sincronizado)")
    else:
        print(f"   Status: PENDENTE ({novos} itens para sincronizar)")

    return novos

def verificar_rastreabilidade(conn):
    """Verifica rastreabilidade"""
    print("\n" + "="*80)
    print("5. RASTREABILIDADE (prime_rastreabilidade)")
    print("="*80)

    ultimo = get_ultimo_supabase('prime_rastreabilidade', 'codigo_processo_original')
    print(f"   Último no Supabase: {ultimo}")

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM PROCESSO_MANIPULACAO PM
        WHERE PM.CODIGO > {ultimo}
    """)

    novos = cursor.fetchone()[0]
    print(f"   Novos no Firebird:  {novos}")

    if novos == 0:
        print("   Status: OK (tudo sincronizado)")
    else:
        print(f"   Status: PENDENTE ({novos} registros para sincronizar)")

    return novos

def verificar_tipos_processo(conn):
    """Verifica tipos de processo"""
    print("\n" + "="*80)
    print("6. TIPOS PROCESSO (prime_tipos_processo)")
    print("="*80)

    # Buscar ultimo_codigo baseado em codigo_atendimento_original (conforme app.py linha 705)
    url = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
    resp = requests.get(
        url,
        headers=headers,
        params={
            'select': 'codigo_atendimento_original',
            'order': 'codigo_atendimento_original.desc',
            'limit': 1
        }
    )

    ultimo = 0
    if resp.status_code in [200, 206]:
        dados = resp.json()
        if dados:
            ultimo = dados[0]['codigo_atendimento_original']

    print(f"   Último no Supabase: {ultimo}")

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM FORMAFARMACEUTICA_PROCESSO_TIPO FPT
        WHERE FPT.CODIGO > {ultimo}
    """)

    novos = cursor.fetchone()[0]
    print(f"   Novos no Firebird:  {novos}")

    if novos == 0:
        print("   Status: OK (tudo sincronizado)")
    else:
        print(f"   Status: PENDENTE ({novos} tipos para sincronizar)")

    return novos

print("="*80)
print("VERIFICACAO COMPLETA DE TODAS AS TABELAS")
print("="*80)
print("\nConectando ao Firebird...")

try:
    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )

    # Verificar cada tabela
    pendentes = {
        'clientes': verificar_clientes(conn),
        'pedidos': verificar_pedidos(conn),
        'formulas': verificar_formulas(conn),
        'formulas_itens': verificar_formulas_itens(conn),
        'rastreabilidade': verificar_rastreabilidade(conn),
        'tipos_processo': verificar_tipos_processo(conn)
    }

    conn.close()

    # Resumo final
    print("\n" + "="*80)
    print("RESUMO GERAL")
    print("="*80)

    total_pendentes = sum(pendentes.values())

    print(f"\nTabelas verificadas: 6")
    print(f"Total de registros pendentes: {total_pendentes}")

    if total_pendentes == 0:
        print("\n" + "="*80)
        print("PERFEITO! TODAS AS TABELAS ESTAO 100% SINCRONIZADAS!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("ATENCAO! Ha registros pendentes:")
        print("="*80)
        for tabela, count in pendentes.items():
            if count > 0:
                print(f"   - {tabela}: {count} registros")

        print("\nExecute /sync para sincronizar os pendentes:")
        print("   curl -X POST https://sincro.oficialmed.com.br/sync")

except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()
