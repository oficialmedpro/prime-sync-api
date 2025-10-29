# ✅ CHECKLIST DE DEPLOY - API SYNC

**Data:** 28/10/2025  
**Arquivo:** `sync-api/app.py`

---

## 📋 PRÉ-REQUISITOS

Antes de fazer deploy, confirme:

- [x] Script de correção executado com sucesso
- [x] Validação mostra dados corretos no Supabase
- [x] API `app.py` já está corrigida (busca 3 tabelas + totalizadores)
- [ ] Teste local da API funcionando

---

## 🔧 MUDANÇAS NA API (Já implementadas)

### ✅ Função `sync_clientes_novos()` - Linhas 125-298

**O que foi corrigido:**

1. **Busca telefones** da tabela `CADASTRO_TELEFONE` (linhas 162-184)
2. **Busca endereços** da tabela `CADASTRO_ENDERECO` (linhas 186-206)
3. **Calcula totalizadores** da tabela `ATENDIMENTO_A1` (linhas 208-244)
4. **Combina os 4 dados** antes de inserir (linhas 248-298)

**Resultado:** Clientes novos vêm com telefone, endereço e totalizadores completos!

---

## 🚀 PROCESSO DE DEPLOY

### Opção A: Deploy Manual (se você tem acesso ao servidor)

```bash
# 1. Conectar ao servidor onde a API roda
ssh usuario@servidor

# 2. Ir para o diretório da API
cd /caminho/para/sync-api

# 3. Fazer backup do arquivo atual
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S)

# 4. Atualizar o arquivo (git pull ou upload manual)
git pull origin main
# OU
# Fazer upload do app.py via FTP/SCP

# 5. Reiniciar o serviço
sudo systemctl restart sync-api
# OU
pm2 restart sync-api
# OU
supervisorctl restart sync-api

# 6. Verificar logs
tail -f /var/log/sync-api.log
# OU
pm2 logs sync-api
```

---

### Opção B: Deploy Automático (CI/CD)

Se você usa GitHub Actions / GitLab CI / etc:

```bash
# 1. Commit das mudanças
git add sync-api/app.py
git commit -m "fix: buscar telefones e enderecos de tabelas relacionadas"

# 2. Push para repositório
git push origin main

# 3. Pipeline automático fará o deploy
# Acompanhar em: https://github.com/seu-repo/actions
```

---

### Opção C: Deploy em Container (Docker)

```bash
# 1. Rebuild da imagem
docker build -t sync-api:latest .

# 2. Parar container antigo
docker stop sync-api

# 3. Remover container antigo
docker rm sync-api

# 4. Iniciar novo container
docker run -d --name sync-api \
  --restart always \
  -p 8000:8000 \
  sync-api:latest

# 5. Verificar logs
docker logs -f sync-api
```

---

## 🧪 TESTES APÓS DEPLOY

### 1. Teste de Health Check
```bash
curl http://seu-servidor:porta/health
# Deve retornar: {"status": "ok"}
```

### 2. Teste de Sincronização Manual
```bash
curl -X POST http://seu-servidor:porta/sync/clientes
# Deve retornar quantidade de clientes sincronizados
```

### 3. Verificar Logs
```bash
# Procurar por erros
tail -f /var/log/sync-api.log | grep "ERROR"

# Verificar se está buscando das 3 tabelas
tail -f /var/log/sync-api.log | grep "CADASTRO_TELEFONE\|CADASTRO_ENDERECO"
```

### 4. Executar Validação
```bash
cd sync-api
python validacao_rapida.py
# Deve mostrar: [OK] TUDO CERTO!
```

---

## ⚠️ ROLLBACK (se der problema)

### Se algo der errado após deploy:

```bash
# 1. Restaurar backup
cp app.py.backup.XXXXXXXX_XXXXXX app.py

# 2. Reiniciar serviço
sudo systemctl restart sync-api

# 3. Verificar se voltou ao normal
curl http://seu-servidor:porta/health
```

---

## 📊 MONITORAMENTO PÓS-DEPLOY

### Primeiras 24 horas:

- [ ] Verificar logs a cada 2 horas
- [ ] Executar validação 3x (manhã, tarde, noite)
- [ ] Conferir dashboard se telefones estão aparecendo
- [ ] Verificar se totalizadores estão corretos

### Primeira semana:

- [ ] Validação diária
- [ ] Conferir se clientes novos vêm completos
- [ ] Monitorar erros de sincronização
- [ ] Validar com usuários finais

---

## 🎯 CRITÉRIOS DE SUCESSO

O deploy será considerado sucesso quando:

- ✅ Clientes novos sincronizam com telefone
- ✅ Clientes novos sincronizam com endereço
- ✅ Totalizadores são calculados corretamente
- ✅ Nelson Moreno (37479) aparece com dados completos
- ✅ Sem erros nos logs por 24h
- ✅ Frontend mostra clientes "Com Histórico" com dados completos

---

## 📞 CONTATOS DE SUPORTE

**Em caso de problemas:**

1. Verificar documentação: `DOCUMENTACAO_FIREBIRD_COMPLETA.md`
2. Executar validação: `python validacao_rapida.py`
3. Conferir logs: `/var/log/sync-api.log`
4. Rollback se necessário (ver acima)

---

## 📝 COMANDOS ÚTEIS

```bash
# Ver status do serviço
systemctl status sync-api

# Ver últimas 100 linhas do log
tail -n 100 /var/log/sync-api.log

# Contar clientes sincronizados hoje
grep "clientes sincronizados" /var/log/sync-api.log | grep "$(date +%Y-%m-%d)" | wc -l

# Ver erros de hoje
grep "ERROR\|ERRO" /var/log/sync-api.log | grep "$(date +%Y-%m-%d)"
```

---

**Última atualização:** 28/10/2025  
**Responsável:** [Seu Nome]  
**Status:** ✅ Pronto para deploy


