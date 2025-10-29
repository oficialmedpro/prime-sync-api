# -*- coding: utf-8 -*-
"""
Script para verificar duplicatas no Supabase
"""
import requests

SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA"

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
}

def verificar_duplicatas_sql():
    """Executa query SQL no Supabase para encontrar duplicatas"""

    print("\n" + "="*80)
    print("VERIFICACAO DE DUPLICATAS NO SUPABASE")
    print("="*80)

    tabelas = [
        {
            'nome': 'prime_clientes',
            'campo_original': 'codigo_cliente_original',
            'nome_amigavel': 'CLIENTES'
        },
        {
            'nome': 'prime_pedidos',
            'campo_original': 'codigo_orcamento_original',
            'nome_amigavel': 'PEDIDOS'
        },
        {
            'nome': 'prime_formulas',
            'campo_original': 'numero_formula',
            'nome_amigavel': 'FORMULAS'
        },
        {
            'nome': 'prime_formulas_itens',
            'campo_original': 'codigo_item_original',
            'nome_amigavel': 'FORMULAS ITENS'
        }
    ]

    for tab in tabelas:
        print(f"\n[{tab['nome_amigavel']}] Verificando duplicatas...")

        # Buscar alguns registros duplicados
        # Não posso fazer GROUP BY direto via API REST, então vou buscar
        # uma amostra e verificar manualmente

        # Pegar total de registros
        resp_total = requests.get(
            f"{SUPABASE_URL}/rest/v1/{tab['nome']}",
            headers={**HEADERS, 'Prefer': 'count=exact'},
            params={'select': 'id', 'limit': 0}
        )
        total = int(resp_total.headers.get('Content-Range', '0').split('/')[-1])

        # Pegar todos os códigos originais (limitado a 10000)
        resp_codigos = requests.get(
            f"{SUPABASE_URL}/rest/v1/{tab['nome']}",
            headers=HEADERS,
            params={
                'select': f"id,{tab['campo_original']}",
                'limit': 10000,
                'order': f"{tab['campo_original']}.asc"
            },
            timeout=30
        )

        if resp_codigos.status_code == 200:
            dados = resp_codigos.json()
            codigos = [d[tab['campo_original']] for d in dados if d[tab['campo_original']] is not None]

            # Contar duplicatas
            from collections import Counter
            counter = Counter(codigos)
            duplicatas = {codigo: count for codigo, count in counter.items() if count > 1}

            if duplicatas:
                print(f"  [PROBLEMA] Encontradas {len(duplicatas)} codigos DUPLICADOS!")
                print(f"  Total de registros duplicados: {sum(duplicatas.values()) - len(duplicatas)}")
                print(f"  Exemplos:")
                for codigo, count in list(duplicatas.items())[:5]:
                    print(f"    - Codigo {codigo}: {count} vezes")
            else:
                print(f"  [OK] Nenhuma duplicata encontrada (verificados {len(codigos)} registros)")
        else:
            print(f"  [ERRO] Falha ao buscar dados: {resp_codigos.status_code}")

    print("\n" + "="*80)

if __name__ == "__main__":
    verificar_duplicatas_sql()
