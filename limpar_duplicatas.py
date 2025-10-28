# -*- coding: utf-8 -*-
"""
Script para limpar duplicatas no Supabase
Mantém apenas o registro mais antigo (menor id) de cada codigo_original
"""
import requests
from collections import defaultdict

SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA"

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
}

def limpar_duplicatas_formulas():
    """Remove duplicatas de prime_formulas (mantém o mais antigo)"""
    print("\n" + "="*80)
    print("LIMPEZA DE DUPLICATAS - prime_formulas")
    print("="*80)

    # Buscar todas as fórmulas (em lotes)
    todas_formulas = []
    offset = 0
    limit = 1000

    print("\n[1/3] Buscando todas as formulas do Supabase...")

    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_formulas",
            headers=HEADERS,
            params={
                'select': 'id,numero_formula',
                'limit': limit,
                'offset': offset,
                'order': 'id.asc'
            },
            timeout=30
        )

        if resp.status_code == 200:
            dados = resp.json()
            if not dados:
                break
            todas_formulas.extend(dados)
            offset += limit
            print(f"   Carregadas {len(todas_formulas)} formulas...")
        else:
            print(f"   [ERRO] Status {resp.status_code}")
            return False

    print(f"\n   Total de formulas no Supabase: {len(todas_formulas)}")

    # Agrupar por numero_formula
    grupos = defaultdict(list)
    for formula in todas_formulas:
        if formula['numero_formula'] is not None:
            grupos[formula['numero_formula']].append(formula['id'])

    # Identificar duplicatas
    duplicatas_ids = []
    for numero_formula, ids in grupos.items():
        if len(ids) > 1:
            # Manter o MENOR ID (mais antigo), deletar os outros
            ids_ordenados = sorted(ids)
            duplicatas_ids.extend(ids_ordenados[1:])  # Todos exceto o primeiro

    if not duplicatas_ids:
        print("\n   [OK] Nenhuma duplicata encontrada!")
        return True

    print(f"\n[2/3] Encontradas {len(duplicatas_ids)} formulas DUPLICADAS para deletar")
    print(f"   Exemplo de formulas duplicadas:")
    for numero_formula, ids in list(grupos.items())[:3]:
        if len(ids) > 1:
            print(f"     - Formula {numero_formula}: {len(ids)} copias (IDs: {ids[:5]}...)")

    # Deletar duplicatas em lotes de 100
    print(f"\n[3/3] Deletando {len(duplicatas_ids)} duplicatas...")
    total_deletado = 0

    for i in range(0, len(duplicatas_ids), 100):
        lote = duplicatas_ids[i:i+100]
        ids_str = ','.join(map(str, lote))

        resp_delete = requests.delete(
            f"{SUPABASE_URL}/rest/v1/prime_formulas",
            headers=HEADERS,
            params={'id': f'in.({ids_str})'},
            timeout=60
        )

        if resp_delete.status_code == 204:
            total_deletado += len(lote)
            print(f"   ✅ Lote {i//100 + 1}: {len(lote)} duplicatas deletadas (total: {total_deletado})")
        else:
            print(f"   ❌ Erro ao deletar lote {i//100 + 1}: {resp_delete.status_code}")

    print(f"\n✅ CONCLUIDO - {total_deletado} duplicatas deletadas!")
    print("="*80 + "\n")
    return True

def limpar_duplicatas_itens():
    """Remove duplicatas de prime_formulas_itens"""
    print("\n" + "="*80)
    print("LIMPEZA DE DUPLICATAS - prime_formulas_itens")
    print("="*80)

    todas_itens = []
    offset = 0
    limit = 1000

    print("\n[1/3] Buscando todos os itens do Supabase...")

    while True:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
            headers=HEADERS,
            params={
                'select': 'id,codigo_item_original',
                'limit': limit,
                'offset': offset,
                'order': 'id.asc'
            },
            timeout=30
        )

        if resp.status_code == 200:
            dados = resp.json()
            if not dados:
                break
            todas_itens.extend(dados)
            offset += limit
            if offset % 10000 == 0:
                print(f"   Carregados {len(todas_itens)} itens...")
        else:
            print(f"   [ERRO] Status {resp.status_code}")
            return False

    print(f"\n   Total de itens no Supabase: {len(todas_itens)}")

    # Agrupar por codigo_item_original
    grupos = defaultdict(list)
    for item in todas_itens:
        if item['codigo_item_original'] is not None:
            grupos[item['codigo_item_original']].append(item['id'])

    # Identificar duplicatas
    duplicatas_ids = []
    for codigo_item, ids in grupos.items():
        if len(ids) > 1:
            ids_ordenados = sorted(ids)
            duplicatas_ids.extend(ids_ordenados[1:])

    if not duplicatas_ids:
        print("\n   [OK] Nenhuma duplicata encontrada!")
        return True

    print(f"\n[2/3] Encontradas {len(duplicatas_ids)} itens DUPLICADOS para deletar")

    # Deletar duplicatas em lotes de 100
    print(f"\n[3/3] Deletando {len(duplicatas_ids)} duplicatas...")
    total_deletado = 0

    for i in range(0, len(duplicatas_ids), 100):
        lote = duplicatas_ids[i:i+100]
        ids_str = ','.join(map(str, lote))

        resp_delete = requests.delete(
            f"{SUPABASE_URL}/rest/v1/prime_formulas_itens",
            headers=HEADERS,
            params={'id': f'in.({ids_str})'},
            timeout=60
        )

        if resp_delete.status_code == 204:
            total_deletado += len(lote)
            if (i + 100) % 1000 == 0:
                print(f"   ✅ Progresso: {total_deletado} duplicatas deletadas")
        else:
            print(f"   ❌ Erro ao deletar lote {i//100 + 1}: {resp_delete.status_code}")

    print(f"\n✅ CONCLUIDO - {total_deletado} duplicatas deletadas!")
    print("="*80 + "\n")
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SCRIPT DE LIMPEZA DE DUPLICATAS")
    print("="*80)
    print("\nEste script vai:")
    print("1. Buscar todas as formulas e itens no Supabase")
    print("2. Identificar duplicatas (mesmo codigo_original)")
    print("3. Manter apenas o registro mais antigo (menor ID)")
    print("4. Deletar as copias duplicadas")
    print("\n" + "="*80)

    input("\nPressione ENTER para continuar ou CTRL+C para cancelar...")

    # Limpar formulas
    sucesso_formulas = limpar_duplicatas_formulas()

    # Limpar itens
    sucesso_itens = limpar_duplicatas_itens()

    if sucesso_formulas and sucesso_itens:
        print("\n" + "="*80)
        print("✅ LIMPEZA CONCLUIDA COM SUCESSO!")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ LIMPEZA CONCLUIDA COM ERROS")
        print("="*80 + "\n")
