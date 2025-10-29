# -*- coding: utf-8 -*-
"""
Script para investigar registros faltantes
"""
import fdb
import requests

FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}

SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA"

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api'
}

def get_max_codigo_supabase(tabela, campo_codigo):
    """Pega o maior codigo sincronizado no Supabase"""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/{tabela}",
        headers=HEADERS,
        params={
            'select': campo_codigo,
            'order': f'{campo_codigo}.desc',
            'limit': 1
        }
    )

    if resp.status_code == 200 and resp.json():
        return resp.json()[0][campo_codigo]
    return 0

def investigar():
    print("\n" + "="*80)
    print("INVESTIGACAO DE REGISTROS FALTANTES")
    print("="*80)

    conn = fdb.connect(**FIREBIRD_CONFIG)
    cursor = conn.cursor()

    # 1. INVESTIGAR PEDIDOS (233 faltando)
    print("\n[PEDIDOS] Investigando 233 pedidos faltantes...")

    max_codigo_pedido = get_max_codigo_supabase('prime_pedidos', 'codigo_orcamento_original')
    print(f"  Ultimo pedido sincronizado no Supabase: {max_codigo_pedido}")

    # Query da API
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO > {max_codigo_pedido}
        AND A.CODIGO_CLIENTE IS NOT NULL
    """)
    novos_pedidos = cursor.fetchone()[0]
    print(f"  Pedidos NOVOS no Firebird (codigo > {max_codigo_pedido}): {novos_pedidos}")

    # Total geral no Firebird
    cursor.execute("""
        SELECT COUNT(*)
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IS NOT NULL
    """)
    total_pedidos_fb = cursor.fetchone()[0]
    print(f"  Total pedidos no Firebird: {total_pedidos_fb}")

    # Verificar se há pedidos ANTIGOS não sincronizados
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO <= {max_codigo_pedido}
        AND A.CODIGO_CLIENTE IS NOT NULL
    """)
    pedidos_antigos_fb = cursor.fetchone()[0]
    print(f"  Pedidos ANTIGOS no Firebird (codigo <= {max_codigo_pedido}): {pedidos_antigos_fb}")

    # Total no Supabase
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers={**HEADERS, 'Prefer': 'count=exact'},
        params={'select': 'id', 'limit': 0}
    )
    total_pedidos_sb = int(resp.headers.get('Content-Range', '0').split('/')[-1])
    print(f"  Total pedidos no Supabase: {total_pedidos_sb}")

    diferenca = pedidos_antigos_fb - total_pedidos_sb
    if diferenca > 0:
        print(f"  [PROBLEMA] Faltam {diferenca} pedidos ANTIGOS no Supabase!")
    elif diferenca < 0:
        print(f"  [PROBLEMA] Supabase tem {abs(diferenca)} pedidos A MAIS que Firebird!")
    else:
        print(f"  [OK] Pedidos antigos estao 100% sincronizados")

    # 2. INVESTIGAR RASTREABILIDADE (3,186 faltando)
    print("\n[RASTREABILIDADE] Investigando 3,186 registros faltantes...")

    max_codigo_rast = get_max_codigo_supabase('prime_rastreabilidade', 'codigo_original')
    print(f"  Ultimo registro sincronizado no Supabase: {max_codigo_rast}")

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM PROCESSO_MANIPULACAO PM
        WHERE PM.CODIGO > {max_codigo_rast}
    """)
    novos_rast = cursor.fetchone()[0]
    print(f"  Registros NOVOS no Firebird (codigo > {max_codigo_rast}): {novos_rast}")

    cursor.execute("""
        SELECT COUNT(*)
        FROM PROCESSO_MANIPULACAO
    """)
    total_rast_fb = cursor.fetchone()[0]
    print(f"  Total no Firebird: {total_rast_fb}")

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM PROCESSO_MANIPULACAO PM
        WHERE PM.CODIGO <= {max_codigo_rast}
    """)
    rast_antigos_fb = cursor.fetchone()[0]
    print(f"  Registros ANTIGOS no Firebird (codigo <= {max_codigo_rast}): {rast_antigos_fb}")

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_rastreabilidade",
        headers={**HEADERS, 'Prefer': 'count=exact'},
        params={'select': 'id', 'limit': 0}
    )
    total_rast_sb = int(resp.headers.get('Content-Range', '0').split('/')[-1])
    print(f"  Total no Supabase: {total_rast_sb}")

    diferenca_rast = rast_antigos_fb - total_rast_sb
    if diferenca_rast > 0:
        print(f"  [PROBLEMA] Faltam {diferenca_rast} registros ANTIGOS no Supabase!")
    elif diferenca_rast < 0:
        print(f"  [PROBLEMA] Supabase tem {abs(diferenca_rast)} registros A MAIS!")
    else:
        print(f"  [OK] Registros antigos estao 100% sincronizados")

    # 3. VERIFICAR FORMULAS
    print("\n[FORMULAS] Verificando discrepancia...")

    max_codigo_formula = get_max_codigo_supabase('prime_formulas', 'numero_formula')
    print(f"  Ultima formula sincronizada no Supabase: {max_codigo_formula}")

    cursor.execute("""
        SELECT COUNT(*)
        FROM ATENDIMENTO_A2
    """)
    total_formulas_fb = cursor.fetchone()[0]
    print(f"  Total formulas no Firebird: {total_formulas_fb}")

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_formulas",
        headers={**HEADERS, 'Prefer': 'count=exact'},
        params={'select': 'id', 'limit': 0}
    )
    total_formulas_sb = int(resp.headers.get('Content-Range', '0').split('/')[-1])
    print(f"  Total formulas no Supabase: {total_formulas_sb}")

    if total_formulas_sb > total_formulas_fb:
        print(f"  [PROBLEMA] Supabase tem {total_formulas_sb - total_formulas_fb} formulas A MAIS!")
        print(f"  Pode haver DUPLICATAS no Supabase!")

    # 4. VERIFICAR CLIENTES
    print("\n[CLIENTES] Verificando discrepancia...")

    cursor.execute("""
        SELECT COUNT(*)
        FROM CLIENTE C
        WHERE C.ATIVO = -1 AND C.CODIGO < 500000
    """)
    total_clientes_fb = cursor.fetchone()[0]
    print(f"  Total clientes no Firebird (ATIVO=-1, CODIGO<500000): {total_clientes_fb}")

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_clientes",
        headers={**HEADERS, 'Prefer': 'count=exact'},
        params={'select': 'id', 'limit': 0}
    )
    total_clientes_sb = int(resp.headers.get('Content-Range', '0').split('/')[-1])
    print(f"  Total clientes no Supabase: {total_clientes_sb}")

    if total_clientes_sb > total_clientes_fb:
        print(f"  [PROBLEMA] Supabase tem {total_clientes_sb - total_clientes_fb} clientes A MAIS!")
        print(f"  Pode haver DUPLICATAS no Supabase!")

    conn.close()

    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print("1. Verificar se ha DUPLICATAS no Supabase")
    print("2. Verificar se a API esta pulando registros antigos")
    print("3. Considerar sincronizacao COMPLETA (nao apenas incremental)")
    print("="*80 + "\n")

if __name__ == "__main__":
    investigar()
