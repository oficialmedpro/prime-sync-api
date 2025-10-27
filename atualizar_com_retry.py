#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATUALIZACAO COM RETRY E RATE LIMITING
Versão robusta com delays para evitar rate limit
"""
import fdb
import requests
import os
import sys
import time
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
    'Content-Type': 'application/json',
    'Accept-Profile': 'api'
}

# Configurações de rate limiting
DELAY_ENTRE_REQUESTS = 0.05  # 50ms entre cada request
MAX_RETRIES = 3

print("="*80)
print("ATUALIZACAO COM RETRY E RATE LIMITING")
print("="*80)
print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
sys.stdout.flush()

inicio = time.time()

try:
    # 1. Buscar apenas pedidos SEM data_criacao (otimização!)
    print("\n1. Buscando pedidos SEM data_criacao no Supabase...")
    sys.stdout.flush()

    url = f"{SUPABASE_URL}/rest/v1/prime_pedidos"
    pedidos = []
    offset = 0
    limit = 1000

    while True:
        resp = requests.get(
            url,
            headers=headers,
            params={
                'select': 'id,codigo_orcamento_original,data_criacao',
                'data_criacao': 'is.null',  # APENAS os que estão vazios!
                'limit': limit,
                'offset': offset
            }
        )
        batch = resp.json()
        if not batch:
            break
        pedidos.extend(batch)
        offset += limit
        print(f"   Baixados: {len(pedidos)}")
        sys.stdout.flush()
        if len(batch) < limit:
            break

    print(f"Total a atualizar: {len(pedidos)} pedidos")
    sys.stdout.flush()

    if len(pedidos) == 0:
        print("\n✅ Nenhum pedido para atualizar! Todos já têm data_criacao.")
        sys.exit(0)

    # 2. Buscar Firebird em cache
    print("\n2. Buscando dados do Firebird...")
    sys.stdout.flush()

    codigos = [p['codigo_orcamento_original'] for p in pedidos]

    conn = fdb.connect(
        host=FIREBIRD_HOST,
        database=FIREBIRD_DB,
        user=FIREBIRD_USER,
        password=FIREBIRD_PASS,
        charset='UTF8'
    )
    cursor = conn.cursor()

    cache = {}
    batch_size = 500

    for i in range(0, len(codigos), batch_size):
        batch_codes = codigos[i:i+batch_size]
        codes_str = ','.join(map(str, batch_codes))

        cursor.execute(f"""
            SELECT
                A.CODIGO,
                A.CADASTRO_DT,
                A.AVIADA_DT,
                A.ENTREGUE_DT
            FROM ATENDIMENTO_A1 A
            WHERE A.CODIGO IN ({codes_str})
        """)

        for row in cursor.fetchall():
            codigo, cad, avi, ent = row
            cache[codigo] = {
                'data_criacao': cad.isoformat() if cad else None,
                'data_aprovacao': avi.isoformat() if avi else None,
                'data_entrega': ent.isoformat() if ent else None
            }

        print(f"   Firebird: {len(cache)}/{len(pedidos)}")
        sys.stdout.flush()

    conn.close()

    # 3. Atualizar Supabase COM RETRY e DELAY
    print("\n3. Atualizando Supabase (com rate limiting)...")
    sys.stdout.flush()

    atualizados = 0
    erros = 0
    sem_dados = 0

    for idx, pedido in enumerate(pedidos):
        codigo = pedido['codigo_orcamento_original']
        dados = cache.get(codigo)

        if not dados:
            sem_dados += 1
            continue

        # Tentar atualizar com retry
        sucesso = False
        for tentativa in range(MAX_RETRIES):
            try:
                resp = requests.patch(
                    f"{SUPABASE_URL}/rest/v1/prime_pedidos",
                    headers=headers,
                    params={'id': f"eq.{pedido['id']}"},
                    json=dados,
                    timeout=10
                )

                if resp.status_code in [200, 204]:
                    atualizados += 1
                    sucesso = True
                    break
                elif resp.status_code == 429:  # Too Many Requests
                    print(f"\n   Rate limit! Aguardando 2s...")
                    sys.stdout.flush()
                    time.sleep(2)
                else:
                    erros += 1
                    break

            except Exception as e:
                if tentativa < MAX_RETRIES - 1:
                    print(f"\n   Erro temporário, tentando novamente... ({tentativa+1}/{MAX_RETRIES})")
                    sys.stdout.flush()
                    time.sleep(1)
                else:
                    erros += 1
                    print(f"\n   Erro ao atualizar pedido {codigo}: {e}")
                    sys.stdout.flush()

        # Delay para evitar rate limit
        time.sleep(DELAY_ENTRE_REQUESTS)

        # Progresso a cada 100
        if (atualizados + erros) % 100 == 0:
            porcentagem = ((atualizados + erros) / len(pedidos)) * 100
            tempo_decorrido = time.time() - inicio
            velocidade = (atualizados + erros) / tempo_decorrido if tempo_decorrido > 0 else 0
            tempo_restante = (len(pedidos) - (atualizados + erros)) / velocidade if velocidade > 0 else 0

            print(f"   Progresso: {atualizados}/{len(pedidos)} ({porcentagem:.1f}%) | Erros: {erros} | Velocidade: {velocidade:.1f} p/s | Restam: {tempo_restante/60:.1f} min")
            sys.stdout.flush()

    # 4. Resultados
    fim = time.time()
    duracao = fim - inicio

    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"\nPedidos processados:  {len(pedidos)}")
    print(f"Atualizados:          {atualizados}")
    print(f"Sem dados Firebird:   {sem_dados}")
    print(f"Erros:                {erros}")
    print(f"\nDuração:              {duracao:.1f}s ({duracao/60:.1f} min)")
    print(f"Velocidade média:     {atualizados/duracao:.1f} pedidos/s")

    if atualizados > 0:
        print(f"\n✅ {atualizados} pedidos atualizados com sucesso!")

    # 5. Verificar quantos ainda faltam
    print("\n" + "="*80)
    print("VERIFICACAO FINAL")
    print("="*80)

    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/prime_pedidos",
        headers={**headers, 'Prefer': 'count=exact'},
        params={'select': 'id', 'data_criacao': 'is.null', 'limit': 0}
    )

    faltando = int(resp.headers.get('Content-Range', '0').split('/')[-1])

    print(f"\nPedidos ainda sem data_criacao: {faltando}")

    if faltando == 0:
        print("\n🎉 PERFEITO! Todos os pedidos têm data_criacao!")
    elif faltando > 0:
        print(f"\n⚠️  Ainda restam {faltando} pedidos.")
        print("Execute o script novamente para continuar.")

    print("\n" + "="*80)

except KeyboardInterrupt:
    print("\n\n⚠️  Processo interrompido pelo usuário!")
    print("Execute novamente para continuar de onde parou.")

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
