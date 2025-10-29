#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORREÇÃO: Alterar tipos_processo para usar UPSERT (resolve HTTP 409)
Tabela de configuração não precisa sincronizar sempre, só atualizar quando necessário
Data: 27/10/2025
"""

import os

print("\n" + "="*80)
print("🔧 CORREÇÃO: Script de tipos_processo (UPSERT)")
print("="*80)

print("""
📋 PROBLEMA ATUAL:
   - Script tenta fazer INSERT de tipos de processo
   - Se já existirem, retorna HTTP 409 (conflito)
   - Logs mostram: "❌ Erro ao inserir tipos: 409"

✅ SOLUÇÃO:
   - Tipos de processo são CONFIGURAÇÕES (não dados transacionais)
   - Devem usar UPSERT (INSERT ou UPDATE se já existir)
   - Header: 'Prefer': 'resolution=merge-duplicates'
   
🎯 ESTRATÉGIA:
   Opção 1: Usar UPSERT no código Python
   Opção 2: Criar constraint UNIQUE e usar ON CONFLICT no Supabase
   Opção 3: Sincronizar apenas 1x e depois só atualizar quando necessário
""")

# ============================================================================
# SOLUÇÃO 1: Adicionar UNIQUE CONSTRAINT no Supabase
# ============================================================================

print("\n" + "="*80)
print("SOLUÇÃO 1: Adicionar UNIQUE CONSTRAINT (Recomendado)")
print("="*80)

print("""
Execute no Supabase SQL Editor:

-- 1. Verificar se já existe constraint
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'api.prime_tipos_processo'::regclass;

-- 2. Criar constraint de unicidade (se não existir)
ALTER TABLE api.prime_tipos_processo
ADD CONSTRAINT unique_codigo_tipo_original UNIQUE (codigo_tipo_original);

-- 3. Agora o INSERT com ON CONFLICT funcionará automaticamente
-- O Supabase com 'Prefer: resolution=merge-duplicates' fará UPSERT
""")

# ============================================================================
# SOLUÇÃO 2: Modificar função no app.py
# ============================================================================

print("\n" + "="*80)
print("SOLUÇÃO 2: Modificar função sync_tipos_processo_novos()")
print("="*80)

codigo_modificado = '''
def sync_tipos_processo_novos():
    """Sincroniza tipos de processo (UPSERT em vez de INSERT)"""
    try:
        logger.info("📋 Sincronizando tipos de processo...")

        # Buscar todos os tipos do Firebird
        conn = conectar_firebird()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                FPT.CODIGO,
                FPT.NOMETIPO,
                FPT.NOMEFICHA,
                FPT.TIPO_PRODUCAO,
                FPT.SEQUENCIA,
                FPT.ATIVO,
                FPT.PROCESSO_OPCIONAL,
                FPT.PAGARCOMISSAO,
                FPT.REGISTRAR_BAIXA,
                FPT.BLOQUEAR_CALCULO,
                FPT.LIBERAR_ENTREGA,
                FPT.BLOQUEAR_RECEITA,
                FPT.OBSERVACAO
            FROM FORMAFARMACEUTICA_PROCESSO_TIPO FPT
            WHERE FPT.ATIVO = -1
            ORDER BY FPT.CODIGO
        """)

        tipos = cursor.fetchall()
        conn.close()

        if not tipos:
            return {'inseridos': 0, 'mensagem': 'Nenhum tipo encontrado'}

        logger.info(f"✅ Encontrados {len(tipos)} tipos no Firebird")

        # Preparar dados
        tipos_dados = []
        for row in tipos:
            tipo = {
                'codigo_tipo_original': row[0],
                'nome_processo': limpar_string(row[1])[:100] if row[1] else None,
                'nome_ficha': limpar_string(row[2])[:100] if row[2] else None,
                'tipo_producao': row[3],
                'sequencia': row[4],
                'ativo': bool(row[5]) if row[5] is not None else True,
                'processo_opcional': bool(row[6]) if row[6] is not None else False,
                'pagar_comissao': bool(row[7]) if row[7] is not None else False,
                'registrar_baixa': bool(row[8]) if row[8] is not None else False,
                'bloquear_calculo': bool(row[9]) if row[9] is not None else False,
                'liberar_entrega': bool(row[10]) if row[10] is not None else False,
                'bloquear_receita': bool(row[11]) if row[11] is not None else False,
                'observacao': limpar_string(row[12]) if row[12] else None,
                'updated_at': datetime.now().isoformat()
            }
            tipos_dados.append(tipo)

        # UPSERT no Supabase (merge duplicates)
        headers_upsert = {
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Accept-Profile': 'api',
            'Content-Profile': 'api',
            'Prefer': 'resolution=merge-duplicates,return=representation'  # ← MUDANÇA AQUI
        }

        url = f"{SUPABASE_URL}/rest/v1/prime_tipos_processo"
        response = requests.post(url, headers=headers_upsert, json=tipos_dados, timeout=60)

        if response.status_code in [200, 201]:
            return {
                'inseridos': len(tipos_dados),
                'mensagem': f'{len(tipos_dados)} tipos sincronizados/atualizados'
            }
        else:
            logger.error(f"❌ Erro ao sincronizar tipos: {response.status_code}")
            return {'inseridos': 0, 'erro': f'HTTP {response.status_code}'}

    except Exception as e:
        logger.error(f"❌ Erro em sync_tipos_processo_novos: {e}")
        return {'inseridos': 0, 'erro': str(e)}
'''

print("\n📝 Código modificado para app.py:")
print("="*80)
print(codigo_modificado)
print("="*80)

# ============================================================================
# SOLUÇÃO 3: Sincronizar apenas quando necessário
# ============================================================================

print("\n" + "="*80)
print("SOLUÇÃO 3: Sincronizar tipos apenas quando necessário")
print("="*80)

print("""
📋 LÓGICA RECOMENDADA:

def sync_tipos_processo_novos():
    \"\"\"Sincroniza tipos de processo APENAS se houver mudanças\"\"\"
    
    # 1. Buscar total no Firebird
    total_firebird = COUNT(*) FROM FORMAFARMACEUTICA_PROCESSO_TIPO WHERE ATIVO = -1
    
    # 2. Buscar total no Supabase
    total_supabase = COUNT(*) FROM api.prime_tipos_processo
    
    # 3. Se forem iguais, NÃO sincronizar
    if total_firebird == total_supabase:
        return {'inseridos': 0, 'mensagem': 'Tipos já sincronizados'}
    
    # 4. Se diferentes, fazer UPSERT completo
    ...
    
📊 VANTAGENS:
   - Reduz carga no banco
   - Evita erros 409
   - Só sincroniza quando realmente necessário
   - Tipos de processo mudam raramente
""")

# ============================================================================
# RECOMENDAÇÃO FINAL
# ============================================================================

print("\n" + "="*80)
print("🎯 RECOMENDAÇÃO FINAL")
print("="*80)

print("""
✅ FAÇA NESTA ORDEM:

1️⃣ Adicionar UNIQUE CONSTRAINT no Supabase (SOLUÇÃO 1)
   - Garante que não haverá duplicatas
   - Permite UPSERT automático
   
2️⃣ Modificar app.py (SOLUÇÃO 2)
   - Alterar função sync_tipos_processo_novos()
   - Usar header 'Prefer': 'resolution=merge-duplicates'
   - Remover lógica de "último código"
   
3️⃣ Otimizar sincronização (SOLUÇÃO 3)
   - Verificar total antes de sincronizar
   - Só fazer UPSERT se houver diferença
   
📝 RESULTADO:
   - Sem erros HTTP 409
   - Sincronização eficiente
   - Tabela sempre atualizada
   - Logs limpos
""")

print("\n" + "="*80)
print("📁 PRÓXIMO PASSO:")
print("="*80)
print("""
1. Execute o script de verificação no Firebird:
   python verificar_cliente_9999999_firebird.py

2. Compare Firebird vs Supabase:
   python comparar_clientes_firebird_supabase.py

3. Após confirmar quais registros são inválidos:
   - Deletar APENAS os inválidos do Supabase
   - Aplicar as soluções 1, 2 e 3 acima para tipos_processo
   - Rebuild e deploy da imagem Docker
""")

print("\n")



