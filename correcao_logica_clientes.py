#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORRECAO: Modificar logica de sincronizacao de clientes
Problema: Cliente 9999999 (VENDA AO CONSUMIDOR) e legitimo mas impede sincronizacao
Solucao: Ignorar codigos especiais (> 500000) na busca do ultimo codigo
Data: 27/10/2025
"""

print("="*80)
print("CORRECAO: Logica de Sincronizacao de Clientes")
print("="*80)

print("""
PROBLEMA IDENTIFICADO:
======================
- Cliente 9999999 existe no Firebird (VENDA AO CONSUMIDOR)
- E um codigo ESPECIAL usado pelo sistema Prime
- Script busca MAX(codigo) e encontra 9999999
- Depois busca clientes com codigo > 9999999
- Nao encontra nada e nao sincroniza!

CLIENTES REAIS:
===============
- Faixa normal: 1 ate 37.457
- Total: 37.366 clientes ativos
- Ultimo cliente real: 37457 (nao 9999999!)

SOLUCAO:
========
Modificar funcao get_ultimo_id_supabase() para IGNORAR codigos especiais
""")

print("\n" + "="*80)
print("CODIGO MODIFICADO PARA app.py")
print("="*80)

codigo_novo = '''
def get_ultimo_id_supabase(tabela, campo_id='codigo_cliente_original'):
    """Pega o maior ID ja migrado (IGNORANDO codigos especiais > 500000)"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{tabela}"
        
        # NOVO: Adicionar filtro para ignorar codigos especiais
        params = {
            'select': campo_id,
            'order': f'{campo_id}.desc',
            'limit': 1
        }
        
        # Para clientes, ignorar codigos > 500000 (codigos especiais)
        if tabela == 'prime_clientes':
            params[campo_id] = 'lt.500000'  # Menor que 500000
        
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            dados = response.json()
            if dados:
                ultimo_id = dados[0][campo_id]
                logger.info(f"   Ultimo codigo (ignorando especiais): {ultimo_id}")
                return ultimo_id
        return 0
    except Exception as e:
        logger.error(f"Erro ao buscar ultimo ID de {tabela}: {e}")
        return 0
'''

print(codigo_novo)

print("\n" + "="*80)
print("ALTERNATIVA: Modificar query do Firebird")
print("="*80)

codigo_firebird = '''
def sync_clientes_novos():
    """Sincroniza apenas clientes novos (IGNORANDO codigos especiais)"""
    try:
        ultimo_codigo = get_ultimo_id_supabase('prime_clientes', 'codigo_cliente_original')
        logger.info(f"Clientes - Ultimo codigo: {ultimo_codigo}")

        conn = conectar_firebird()
        cursor = conn.cursor()
        
        # MODIFICADO: Adicionar filtro para ignorar codigos especiais
        cursor.execute(f"""
            SELECT 
                C.CODIGO,
                C.NOMECLIENTE,
                C.CPF_CNPJ,
                ... (demais campos)
            FROM CLIENTE C
            LEFT JOIN CIDADEESTADO CE ON C.CODIGO_CIDADEESTADO = CE.CODIGO
            WHERE C.ATIVO = -1
            AND C.CODIGO > {ultimo_codigo}
            AND C.CODIGO < 500000  -- NOVO: Ignorar codigos especiais
            ORDER BY C.CODIGO
            ROWS 1000
        """)
        ...
'''

print(codigo_firebird)

print("\n" + "="*80)
print("IMPLEMENTACAO RECOMENDADA")
print("="*80)

print("""
FAZER EM ORDEM:

1. MODIFICAR app.py - Funcao get_ultimo_id_supabase()
   - Adicionar filtro: codigo < 500000 para prime_clientes
   - Linha ~70-92 do arquivo app.py

2. MODIFICAR app.py - Funcao sync_clientes_novos()
   - Adicionar: AND C.CODIGO < 500000 na query
   - Linha ~132 do arquivo app.py

3. TESTAR localmente:
   python app.py
   # Verificar se busca o codigo correto (37457, nao 9999999)

4. REBUILD Docker:
   docker build -t oficialmedpro/prime-sync-api:latest .
   docker push oficialmedpro/prime-sync-api:latest

5. UPDATE no Portainer:
   Stacks -> prime-sync-api -> Update the stack

6. VERIFICAR logs:
   docker service logs prime-sync-api_prime-sync-api --tail 100

RESULTADO ESPERADO:
===================
Clientes - Ultimo codigo: 37457  (NAO 9999999!)
Encontrados X clientes novos
Clientes: {'inseridos': X, 'mensagem': 'X clientes sincronizados'}
""")

print("\n" + "="*80)
print("PROXIMOS PASSOS")
print("="*80)

print("""
1. Vou criar o patch automatico para app.py
2. Aplicar as modificacoes
3. Testar localmente
4. Deploy
""")

print("\n")

