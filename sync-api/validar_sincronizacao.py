# -*- coding: utf-8 -*-
"""
Script de validacao rapida - Verifica integridade dos ultimos dados sincronizados
"""
import fdb
import requests
import sys

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

def validar_ultimos_registros():
    """Valida os ultimos 3 registros sincronizados de cada tabela"""

    print("\n" + "="*80)
    print("VALIDACAO DE INTEGRIDADE - ULTIMOS REGISTROS SINCRONIZADOS")
    print("="*80)

    conn = fdb.connect(**FIREBIRD_CONFIG)
    cursor = conn.cursor()

    # 1. VALIDAR CLIENTES
    print("\n[CLIENTES] VALIDANDO ULTIMOS 3 CLIENTES...")
    cursor.execute("""
        SELECT FIRST 3
            C.CODIGO,
            C.NOMECLIENTE,
            C.EMAIL1,
            C.TELEFONE1
        FROM CLIENTE C
        WHERE C.ATIVO = -1 AND C.CODIGO < 500000
        ORDER BY C.CODIGO DESC
    """)

    clientes_fb = cursor.fetchall()
    clientes_ok = 0

    for codigo, nome, email, telefone in clientes_fb:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_clientes",
            headers=HEADERS,
            params={
                'select': 'nome,email,telefone',
                'codigo_cliente_original': f'eq.{codigo}',
                'limit': 1
            }
        )

        if resp.status_code == 200 and resp.json():
            cliente_sb = resp.json()[0]
            if cliente_sb['nome'] == nome:
                print(f"  [OK] Cliente {codigo}: {nome[:40]} - OK")
                clientes_ok += 1
            else:
                print(f"  [DIVERGE] Cliente {codigo}: DADOS DIVERGEM")
        else:
            print(f"  [NAO ENCONTRADO] Cliente {codigo}: NAO ENCONTRADO no Supabase")

    # 2. VALIDAR PEDIDOS
    print("\n[PEDIDOS] VALIDANDO ULTIMOS 3 PEDIDOS...")
    cursor.execute("""
        SELECT FIRST 3
            A.CODIGO,
            A.CODIGO_CLIENTE,
            A.VALORVENDA
        FROM ATENDIMENTO_A1 A
        WHERE A.CODIGO_CLIENTE IS NOT NULL
        ORDER BY A.CODIGO DESC
    """)

    pedidos_fb = cursor.fetchall()
    pedidos_ok = 0

    for codigo, codigo_cliente, valor in pedidos_fb:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_pedidos",
            headers=HEADERS,
            params={
                'select': 'codigo_cliente_original,valor_total',
                'codigo_orcamento_original': f'eq.{codigo}',
                'limit': 1
            }
        )

        if resp.status_code == 200 and resp.json():
            pedido_sb = resp.json()[0]
            if pedido_sb['codigo_cliente_original'] == codigo_cliente:
                print(f"  [OK] Pedido {codigo}: Cliente={codigo_cliente}, Valor={valor} - OK")
                pedidos_ok += 1
            else:
                print(f"  [DIVERGE] Pedido {codigo}: DADOS DIVERGEM")
        else:
            print(f"  [NAO ENCONTRADO] Pedido {codigo}: NAO ENCONTRADO no Supabase")

    # 3. VALIDAR FORMULAS
    print("\n[FORMULAS] VALIDANDO ULTIMAS 3 FORMULAS...")
    cursor.execute("""
        SELECT FIRST 3
            A2.CODIGO,
            A2.CODIGO_ATEND_A1
        FROM ATENDIMENTO_A2 A2
        WHERE A2.CODIGO_ATEND_A1 IS NOT NULL
        ORDER BY A2.CODIGO DESC
    """)

    formulas_fb = cursor.fetchall()
    formulas_ok = 0

    for codigo, codigo_pedido in formulas_fb:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_formulas",
            headers=HEADERS,
            params={
                'select': 'codigo_orcamento_original',
                'numero_formula': f'eq.{codigo}',
                'limit': 1
            }
        )

        if resp.status_code == 200 and resp.json():
            formula_sb = resp.json()[0]
            if formula_sb['codigo_orcamento_original'] == codigo_pedido:
                print(f"  [OK] Formula {codigo}: Pedido={codigo_pedido} - OK")
                formulas_ok += 1
            else:
                print(f"  [DIVERGE] Formula {codigo}: DADOS DIVERGEM")
        else:
            print(f"  [NAO ENCONTRADO] Formula {codigo}: NAO ENCONTRADA no Supabase")

    # 4. VALIDAR ITENS DE FORMULAS
    print("\n[ITENS] VALIDANDO ULTIMOS 3 ITENS DE FORMULAS...")
    cursor.execute("""
        SELECT FIRST 3
            A3.CODIGO,
            A3.CODIGO_ATEND_A1,
            A3.CODIGO_PRODUTO,
            A3.QUANTIDADE
        FROM ATENDIMENTO_A3 A3
        WHERE A3.CODIGO_ATEND_A1 IS NOT NULL
        ORDER BY A3.CODIGO DESC
    """)

    itens_fb = cursor.fetchall()
    itens_ok = 0

    for codigo, codigo_pedido, codigo_produto, qtd in itens_fb:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
            headers=HEADERS,
            params={
                'select': 'codigo_pedido_original,quantidade',
                'codigo_item_original': f'eq.{codigo}',
                'limit': 1
            }
        )

        if resp.status_code == 200 and resp.json():
            item_sb = resp.json()[0]
            if item_sb['codigo_pedido_original'] == codigo_pedido:
                print(f"  [OK] Item {codigo}: Pedido={codigo_pedido}, Qtd={qtd} - OK")
                itens_ok += 1
            else:
                print(f"  [DIVERGE] Item {codigo}: DADOS DIVERGEM")
        else:
            print(f"  [NAO ENCONTRADO] Item {codigo}: NAO ENCONTRADO no Supabase")

    conn.close()

    # RESUMO
    print("\n" + "="*80)
    print("RESUMO DA VALIDACAO DE INTEGRIDADE")
    print("="*80)
    print(f"[OK] Clientes validos: {clientes_ok}/3")
    print(f"[OK] Pedidos validos: {pedidos_ok}/3")
    print(f"[OK] Formulas validas: {formulas_ok}/3")
    print(f"[OK] Itens validos: {itens_ok}/3")

    total_ok = clientes_ok + pedidos_ok + formulas_ok + itens_ok
    total = 12

    print(f"\n[RESULTADO] INTEGRIDADE GERAL: {total_ok}/{total} ({total_ok/total*100:.1f}%)")

    if total_ok == total:
        print("[SUCESSO] TODOS OS DADOS VALIDADOS ESTAO INTEGROS!")
        return True
    else:
        print(f"[AVISO] {total - total_ok} registros com divergencias")
        return False

if __name__ == "__main__":
    try:
        sucesso = validar_ultimos_registros()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
