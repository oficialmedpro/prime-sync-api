#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE REAL: Simular busca do Firebird com ROWS 5000
"""
import fdb
import time

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

print("=== TESTE REAL: Buscar com ROWS 5000 ===\n")

# Buscar último código real do Supabase (simulado)
ultimo_supabase = 251003534  # Exemplo

print(f"Ultimo codigo Supabase: {ultimo_supabase}\n")

try:
    conn = fdb.connect(host=FIREBIRD_HOST, database=FIREBIRD_DB, user=FIREBIRD_USER, password=FIREBIRD_PASS, charset='UTF8')
    cursor = conn.cursor()
    
    # Testar com ROWS 5000
    inicio = time.time()
    
    cursor.execute(f"""
        SELECT
            A3.CODIGO_ATEND_A1,
            A3.NUMEROFORMULA,
            A3.NUMEROLINHA,
            A3.CODIGO_PRODUTO,
            EG.NOMEPRODUTO,
            A3.QUANTIDADE,
            A3.UNIDADE,
            A3.VALORCUSTO,
            A3.VALORVENDA,
            A3.OBSERVACAO
        FROM ATENDIMENTO_A3 A3
        LEFT JOIN ESTOQUE_GERAL EG ON A3.CODIGO_PRODUTO = EG.CODIGO
        WHERE A3.CODIGO_ATEND_A1 > {ultimo_supabase}
        AND A3.CODIGO_ATEND_A1 IS NOT NULL
        ORDER BY A3.CODIGO_ATEND_A1, A3.NUMEROFORMULA, A3.NUMEROLINHA
        ROWS 5000
    """)
    
    resultado = cursor.fetchall()
    tempo = time.time() - inicio
    
    print(f"RESULTADO:")
    print(f"  Registros retornados: {len(resultado)}")
    print(f"  Tempo de busca: {tempo:.2f} segundos")
    print(f"  Velocidade: {len(resultado) / tempo:.0f} registros/segundo")
    
    if len(resultado) > 0:
        print(f"\n  Primeiro registro: Codigo {resultado[0][0]}")
        print(f"  Ultimo registro: Codigo {resultado[-1][0]}")
    
    # Testar upload (simulado)
    print(f"\nTestando tamanho do payload...")
    dados_teste = []
    for row in resultado:
        dados_teste.append({
            'codigo_atendimento_original': row[0],
            'numero_formula': row[1],
            'numero_linha': row[2],
            'codigo_produto': row[3],
            'nome_produto': row[4] or 'N/A',
            'quantidade': float(row[5]) if row[5] else None,
            'unidade': row[6] or None
        })
    
    import json
    payload_size = len(json.dumps(dados_teste))
    print(f"  Tamanho do JSON: {payload_size / 1024:.1f} KB")
    
    if payload_size > 500 * 1024:  # 500KB
        print(f"  ATENCAO: Payload muito grande ({payload_size / 1024:.0f} KB)")
        print(f"  Pode dar timeout no Supabase!")
    else:
        print(f"  Payload OK para upload")
    
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"CONCLUSÃO:")
    print(f"{'='*50}")
    
    if len(resultado) == 5000:
        print(f"  ROWS 5000 funcionou perfeitamente!")
        print(f"  Sem erros, sem timeout")
        print(f"  Buscou {len(resultado)} registros em {tempo:.2f}s")
    else:
        print(f"  Retornou {len(resultado)} registros (esperado 5000)")
        print(f"  Pode ser que nao tenha mais dados pendentes")
    
except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()

print()




