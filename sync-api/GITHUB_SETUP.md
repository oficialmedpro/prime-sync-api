# 🐙 Setup GitHub - Instruções Completas

## Passo 1: Criar Repositório no GitHub (2 min)

### 1.1 Acessar GitHub
1. Vá para: https://github.com/new
2. Ou: GitHub → Seu perfil → Repositories → **New**

### 1.2 Configurar Repositório
```
Repository name: prime-sync-api
Description: API de sincronização incremental Firebird -> Supabase
Visibility: ⚪ Private (recomendado para produção)
           ⚪ Public (apenas se quiser código aberto)

❌ NÃO marque: "Add a README file"
❌ NÃO marque: "Add .gitignore"
❌ NÃO marque: "Choose a license"
```

**Motivo**: Já temos esses arquivos localmente!

### 1.3 Clicar em "Create repository"

---

## Passo 2: Obter Token do Docker Hub (3 min)

### 2.1 Acessar Docker Hub
1. Vá para: https://hub.docker.com/settings/security
2. Ou: Docker Hub → Account Settings → Security → **Access Tokens**

### 2.2 Criar Token
1. Clique em **New Access Token**
2. **Access Token Description**: `GitHub Actions - prime-sync-api`
3. **Access permissions**: `Read, Write, Delete`
4. Clique em **Generate**

### 2.3 Copiar Token
⚠️ **IMPORTANTE**: Copie o token agora! Ele aparece apenas UMA VEZ.

```
Exemplo: dckr_pat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Salve em local seguro temporariamente (precisaremos no próximo passo).

---

## Passo 3: Adicionar Secret no GitHub (2 min)

### 3.1 Acessar Secrets
No seu repositório recém-criado:
1. Clique em **Settings** (aba superior)
2. No menu lateral: **Secrets and variables** → **Actions**
3. Clique em **New repository secret**

### 3.2 Criar Secret
```
Name: DOCKER_HUB_TOKEN
Secret: [cole o token do Docker Hub que você copiou]
```

### 3.3 Salvar
Clique em **Add secret**

---

## Passo 4: Fazer Push do Código (1 min)

### 4.1 Adicionar Remote

No seu terminal/PowerShell, execute:

```bash
cd "C:\Banco de Dados Prime\sync-api"

# Adicionar remote (substitua 'oficialmedpro' pelo seu username se diferente)
git remote add origin https://github.com/oficialmedpro/prime-sync-api.git

# Verificar remote
git remote -v
```

### 4.2 Fazer Push

```bash
# Push para GitHub
git push -u origin master
```

**Ou se seu branch for 'main':**
```bash
# Renomear branch para main (se necessário)
git branch -M main

# Push para GitHub
git push -u origin main
```

**Login GitHub:**
Se pedir login, use:
- Username: `seu-username-github`
- Password: **Personal Access Token** (não é sua senha!)

**Como gerar Personal Access Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → Marcar: `repo`, `workflow`
3. Copiar token e usar como senha

---

## Passo 5: Verificar Build Automático (2 min)

### 5.1 Acompanhar GitHub Actions

1. No seu repositório GitHub, clique na aba **Actions**
2. Você verá o workflow "Build and Push Docker Image" rodando
3. Clique nele para ver detalhes

**Status:**
- 🟡 Amarelo: Rodando (~2-3 minutos)
- ✅ Verde: Sucesso!
- ❌ Vermelho: Erro (ver logs)

### 5.2 Verificar Docker Hub

1. Acesse: https://hub.docker.com/r/oficialmedpro/prime-sync-api
2. Deve aparecer a nova imagem com tag `latest`
3. Timestamp deve ser recente (agora)

---

## Passo 6: Comandos Úteis

### Ver status do Git
```bash
cd "C:\Banco de Dados Prime\sync-api"
git status
```

### Ver histórico de commits
```bash
git log --oneline
```

### Ver remotes configurados
```bash
git remote -v
```

### Fazer mudanças futuras
```bash
# 1. Editar arquivo
code app.py

# 2. Adicionar mudanças
git add .

# 3. Commit
git commit -m "feat: adicionar nova funcionalidade"

# 4. Push (GitHub Actions fará build automaticamente)
git push
```

---

## Estrutura Final do Repositório

```
prime-sync-api/
├── .github/
│   └── workflows/
│       └── docker-build.yml       # ✅ GitHub Actions workflow
├── .gitignore                      # ✅ Ignora arquivos sensíveis
├── app.py                          # ✅ API Flask
├── Dockerfile                      # ✅ Build da imagem Docker
├── requirements.txt                # ✅ Dependências Python
├── docker-compose.yml              # ✅ Teste local
├── stack-portainer.yml             # ✅ Deploy em produção
├── supabase-cronjob.sql            # ✅ Cronjob Supabase
├── .env.example                    # ✅ Template de configuração
├── README.md                       # ✅ Documentação principal
├── DEPLOY.md                       # ✅ Guia de deploy
├── GUIA_RAPIDO.md                  # ✅ Início rápido
├── ESTRUTURA.md                    # ✅ Arquitetura
├── SECRETS.md                      # ✅ Configuração de secrets
└── GITHUB_SETUP.md                 # ✅ Este arquivo
```

---

## Checklist Completo

### GitHub
- [ ] Repositório criado (private ou public)
- [ ] Token do Docker Hub gerado
- [ ] Secret `DOCKER_HUB_TOKEN` adicionado no GitHub
- [ ] Código commitado localmente (`git commit`)
- [ ] Remote adicionado (`git remote add origin`)
- [ ] Push realizado (`git push`)

### Verificação
- [ ] GitHub Actions executou com sucesso (aba Actions, ✅ verde)
- [ ] Imagem disponível no Docker Hub: `oficialmedpro/prime-sync-api:latest`
- [ ] Tag `latest` com timestamp recente

### Próximos Passos
- [ ] Seguir `DEPLOY.md` para configurar Portainer
- [ ] Criar secrets no Portainer (ver `SECRETS.md`)
- [ ] Deploy stack no Portainer
- [ ] Configurar cronjob no Supabase

---

## Troubleshooting

### Erro: "remote origin already exists"
```bash
# Remover remote antigo
git remote remove origin

# Adicionar novamente
git remote add origin https://github.com/oficialmedpro/prime-sync-api.git
```

### Erro: "Permission denied"
Use Personal Access Token como senha, não sua senha do GitHub:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Marcar: `repo`, `workflow`
4. Usar token como senha ao fazer push

### GitHub Actions falha no build
1. Verificar se secret `DOCKER_HUB_TOKEN` está correto
2. Verificar se token do Docker Hub tem permissões: `Read, Write, Delete`
3. Ver logs detalhados na aba Actions → Clique no workflow falhado

### Imagem não aparece no Docker Hub
1. Aguardar GitHub Actions terminar (pode demorar 2-3 min)
2. Verificar se o username é `oficialmedpro` (ou ajustar no workflow)
3. Verificar logs do GitHub Actions

---

## URLs Importantes

- **Repositório**: https://github.com/oficialmedpro/prime-sync-api
- **Actions**: https://github.com/oficialmedpro/prime-sync-api/actions
- **Docker Hub**: https://hub.docker.com/r/oficialmedpro/prime-sync-api
- **Criar Token Docker**: https://hub.docker.com/settings/security
- **Personal Access Token**: https://github.com/settings/tokens

---

**Criado**: 23/10/2025
**Versão**: 1.0.0
**Tempo estimado**: ~10 minutos
**Próximo passo**: Seguir `DEPLOY.md`
