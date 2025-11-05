# 📖 INSTRUÇÕES COMPLETAS - Render.com

## ✅ O QUE JÁ ESTÁ PRONTO:

1. ✅ `app.py` - API Flask básica (precisa adicionar todas as funções de sincronização)
2. ✅ `requirements.txt` - Dependências Python
3. ✅ `atualizar_supabase.sql` - SQL para atualizar o pg_cron do Supabase
4. ✅ `README.md` - Instruções de configuração

## 🔧 PRÓXIMOS PASSOS:

### 1. Copiar todas as funções de sincronização

O `app.py` atual tem apenas `sync_clientes_novos()` básica. Você precisa copiar do `sync-api/app.py` original:

- `sync_clientes_novos()` (completa)
- `sync_pedidos_novos()`
- `sync_formulas_novas()`
- `sync_formulas_itens_novos()`
- `sync_rastreabilidade_nova()`
- `sync_tipos_processo_novos()`
- `sync_missing_clientes()`
- `sync_missing_pedidos()`

### 2. Criar serviço no Render.com

Siga as instruções do `README.md`

### 3. Atualizar Supabase

Execute o SQL do arquivo `atualizar_supabase.sql` no Supabase

## ⚠️ IMPORTANTE:

- O `app.py` atual é uma versão simplificada
- Você precisa copiar TODAS as funções do `sync-api/app.py` original
- O módulo `auditoria.py` não está sendo usado (pode remover ou adaptar)

## 🎯 RESULTADO FINAL:

- ✅ Render.com executa a sincronização
- ✅ pg_cron do Supabase chama o Render a cada 30 minutos
- ✅ Tudo funciona automaticamente!

