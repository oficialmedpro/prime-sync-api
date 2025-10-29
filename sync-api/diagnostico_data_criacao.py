#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNOSTICO: Verificar situação dos pedidos antes de atualizar
"""

import fdb
import requests
import os

# Configuração
FIREBIRD_HOST = os.getenv('FIREBIRD_HOST', 'db.primesoftware.com.br')
FIREBIRD_DB = os.getenv('FIREBIRD_DB', 'oficialmed1250')
FIREBIRD_USER = os.getenv('FIREBIRD_USER', 'OFICIALMED')
FIREBIRD_PASS = os.getenv('FIREBIRD_PASS', 'Lt-@=waIh))Ql3~')

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://agdffspstbxeqhqtltvb.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA')

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'count=exact'
}

print("="*80)
print("DIAGNOSTICO: Situação dos pedidos")
print("="*80)

try:
    # ========================================================================
    # 1. VERIFICAR SUPABASE
    # ========================================================================
    print("\n1. SUPABASE - Estatísticas")
    print("-" * 80)

    url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"

    # Total de pedidos
    resp = requests.get(url, headers=headers, params={'select': 'id', 'limit': 0})
    total = int(resp.headers.get('Content-Range', '0').split('/')[-1])
    print(f"   Total de pedidos: {total}")

    # Pedidos SEM data_criacao
    resp = requests.get(url, headers=headers, params={'select': 'id', 'data_criacao': 'is.null', 'limit': 0})
    sem_data = int(resp.headers.get('Content-Range', '0').split('/')[-1])
    print(f"   Sem data_criacao: {sem_data}")

    # Pedidos COM data_criacao
    com_data = total - sem_data
    percent_com = (com_data / total * 100) if total > 0 else 0
    percent_sem = (sem_data / total * 100) if total > 0 else 0

    print(f"   Com data_criacao: {com_data} ({percent_com:.1f}%)")
    print(f"   Faltando:         {sem_data} ({percent_sem:.1f}%)")

    # ========================================================================
    # 2. BUSCAR EXEMPLOS NO SUPABASE (5 pedidos sem data)
    # ========================================================================
    print("\n2. SUPABASE - Exemplos de pedidos SEM data_criacao")
    print("-" * 80)

    resp = requests.get(
        url,
        headers={**headers, 'Prefer': 'return=representation'},
        params={
            'select': 'id,codigo_orcamento_original,data_criacao,data_aprovacao,data_entrega',
            'data_criacao': 'is.null',
            'limit': 5
        }
    )

    pedidos_sem_data = resp.json()

    if pedidos_sem_data:
        print(f"\n   Encontrados {len(pedidos_sem_data)} exemplos:")
        for p in pedidos_sem_data:
            print(f"   - Código: {p['codigo_orcamento_original']} | data_criacao: {p['data_criacao']}")
    else:
        print("   ✅ Nenhum pedido sem data_criacao!")

    # ========================================================================
    # 3. VERIFICAR FIREBIRD - Se os dados existem lá
    # ========================================================================
    print("\n3. FIREBIRD - Verificar se dados existem")
    print("-" * 80)

    if pedidos_sem_data:
        conn = fdb.connect(
            host=FIREBIRD_HOST,
            database=FIREBIRD_DB,
            user=FIREBIRD_USER,
            password=FIREBIRD_PASS,
            charset='UTF8'
        )
        cursor = conn.cursor()

        codigos = [p['codigo_orcamento_original'] for p in pedidos_sem_data]
        codigos_str = ','.join(map(str, codigos))

        cursor.execute(f"""
            SELECT
                A.CODIGO,
                A.CADASTRO_DT,
                A.AVIADA_DT,
                A.ENTREGUE_DT
            FROM ATENDIMENTO_A1 A
            WHERE A.CODIGO IN ({codigos_str})
        """)

        print("\n   Dados no Firebird:")
        encontrados = 0
        for row in cursor.fetchall():
            codigo, cad, avi, ent = row
            encontrados += 1
            print(f"   - Código: {codigo}")
            print(f"     CADASTRO_DT:  {cad}")
            print(f"     AVIADA_DT:    {avi}")
            print(f"     ENTREGUE_DT:  {ent}")

        conn.close()

        print(f"\n   Encontrados no Firebird: {encontrados}/{len(codigos)}")

        if encontrados > 0:
            print("\n   ✅ Dados existem no Firebird! Pode prosseguir com atualização.")
        else:
            print("\n   ❌ Dados NÃO encontrados no Firebird!")

    # ========================================================================
    # 4. RESUMO E RECOMENDAÇÃO
    # ========================================================================
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"\n✓ Total de pedidos:           {total}")
    print(f"✓ Pedidos sem data_criacao:   {sem_data} ({percent_sem:.1f}%)")
    print(f"✓ Pedidos com data_criacao:   {com_data} ({percent_com:.1f}%)")

    if sem_data > 0:
        print(f"\n⚠️  AÇÃO NECESSÁRIA:")
        print(f"   {sem_data} pedidos precisam ser atualizados")
        print(f"\n   Execute: python atualizar_data_criacao_otimizado.py")
    else:
        print(f"\n✅ TUDO OK! Todos os pedidos têm data_criacao.")

    print("\n" + "="*80)

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
