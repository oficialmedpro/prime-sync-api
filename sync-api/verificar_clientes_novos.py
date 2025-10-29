#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar se há clientes novos para sincronizar
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
    'Content-Type': 'application/json',
    'Prefer': 'count=exact'
}

print("="*80)
print("VERIFICAR CLIENTES NOVOS")
print("="*80)

try:
    # 1. Buscar último cliente no Supabase
    print("\n1. Último cliente no Supabase:")
    url = f"{SUPABASE_URL}/rest/v1/prime_clientes"

    # Buscar o maior código (excluindo códigos especiais > 500000)
    resp = requests.get(
        url,
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        },
        params={
            'select': 'codigo_cliente_original',
            'codigo_cliente_original': 'lt.500000',
            'order': 'codigo_cliente_original.desc',
            'limit': 1
        }
    )

    if resp.status_code in [200, 206]:  # 206 = Partial Content (paginação)
        dados = resp.json()
        if dados:
            ultimo_codigo = dados[0]['codigo_cliente_original']
            print(f"   Último código: {ultimo_codigo}")
        else:
            ultimo_codigo = 0
            print(f"   Nenhum cliente encontrado (começando do 0)")
    else:
        print(f"   Erro: {resp.status_code}")
        print(f"   Resposta: {resp.text[:200]}")
        exit(1)

    # 2. Verificar quantos clientes novos no Firebird
    print("\n2. Clientes novos no Firebird:")

    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    cursor = conn.cursor()

    # Contar clientes novos
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM CLIENTE C
        WHERE C.ATIVO = -1
        AND C.CODIGO > {ultimo_codigo}
        AND C.CODIGO < 500000
    """)

    count = cursor.fetchone()[0]
    print(f"   Total de clientes novos: {count}")

    if count > 0:
        # Buscar os primeiros 10
        cursor.execute(f"""
            SELECT
                C.CODIGO,
                C.NOME,
                C.CPF,
                C.FONE,
                CE.CIDADE
            FROM CLIENTE C
            LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
            WHERE C.ATIVO = -1
            AND C.CODIGO > {ultimo_codigo}
            AND C.CODIGO < 500000
            ORDER BY C.CODIGO
            ROWS 10
        """)

        print("\n   Primeiros 10 clientes novos:")
        for row in cursor.fetchall():
            codigo, nome, cpf, fone, cidade = row
            print(f"   - Código: {codigo} | Nome: {nome[:30] if nome else 'N/A'} | CPF: {cpf or 'N/A'} | Cidade: {cidade or 'N/A'}")

    conn.close()

    # 3. Tentar inserir um cliente manualmente
    if count > 0:
        print("\n3. Testando inserção manual de 1 cliente:")

        conn = fdb.connect(
            host=FIREBIRD_HOST,
            database=FIREBIRD_DB,
            user=FIREBIRD_USER,
            password=FIREBIRD_PASS,
            charset='UTF8'
        )
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT FIRST 1
                C.CODIGO,
                C.NOME,
                C.CPF,
                C.FONE,
                C.EMAIL,
                C.ENDERECO,
                C.BAIRRO,
                C.NUMERO,
                C.CEP,
                CE.CIDADE,
                CE.UF
            FROM CLIENTE C
            LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
            WHERE C.ATIVO = -1
            AND C.CODIGO > {ultimo_codigo}
            AND C.CODIGO < 500000
            ORDER BY C.CODIGO
        """)

        row = cursor.fetchone()
        if row:
            cliente = {
                'codigo_cliente_original': row[0],
                'nome_completo': row[1][:200] if row[1] else None,
                'cpf': row[2][:14] if row[2] else None,
                'telefone': row[3][:20] if row[3] else None,
                'email': row[4][:100] if row[4] else None,
                'endereco_logradouro': row[5][:200] if row[5] else None,
                'endereco_bairro': row[6][:100] if row[6] else None,
                'endereco_numero': str(row[7]) if row[7] else None,
                'endereco_cep': row[8][:10] if row[8] else None,
                'endereco_cidade': row[9][:100] if row[9] else None,
                'endereco_estado': row[10][:2] if row[10] else None
            }

            print(f"   Tentando inserir cliente {cliente['codigo_cliente_original']}...")

            resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/prime_clientes",
                headers={
                    'apikey': SUPABASE_KEY,
                    'Authorization': f'Bearer {SUPABASE_KEY}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                },
                json=cliente
            )

            if resp.status_code in [200, 201]:
                print(f"   ✅ Sucesso! Cliente inserido.")
            else:
                print(f"   ❌ Erro {resp.status_code}: {resp.text[:200]}")

        conn.close()

    # 4. Resumo
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"\nÚltimo cliente Supabase:  {ultimo_codigo}")
    print(f"Clientes novos Firebird:  {count}")

    if count == 0:
        print("\n✅ Não há clientes novos para sincronizar.")
    else:
        print(f"\n⚠️  Há {count} clientes novos que deveriam ser sincronizados!")
        print("   Verifique os logs do Portainer para ver o erro.")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
