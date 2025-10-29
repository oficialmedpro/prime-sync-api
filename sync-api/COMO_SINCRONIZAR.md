# 🚀 Como Sincronizar (Guia para IA)

## Status Atual (27/10/2025)
- **Total Firebird**: 651.809 registros
- **Total Supabase**: 643.349 registros
- **Faltam**: 8.460 registros (1.3%)
- **Sincronizado**: 98.7% ✓

## Comandos Rápidos

### 1️⃣ Sincronizar AGORA (todos os pendentes)
```bash
cd "C:\Banco de Dados Prime\sync-api"
python sincronizar_agora.py
```
**Tempo**: ~5-10 minutos (50 chamadas x 10s = 8-10 min)

### 2️⃣ Verificar Status Atual
```bash
python comparar_firebird_supabase.py
```
**Saída esperada**:
```
TOTAL GERAL: 651,809 (Firebird) vs 643,349 (Supabase) = 98.7%
```

### 3️⃣ Chamar /sync uma vez
```bash
curl -X POST https://sincro.oficialmed.com.br/sync
```

### 4️⃣ Ver logs do serviço
```bash
docker service logs prime-sync-api_prime-sync-api --tail 100
```

---

## Como Garantir que NÃO Acumule de Novo

### ✅ Cronjob está configurado para rodar a cada 15 minutos
**Localização**: Docker Stack (Portainer)  
**Frequência**: 0 * * * * (a cada hora no /sync endpoint)

### ✅ API sincroniza incrementalmente
- Busca `MAX(codigo)` do Supabase
- Só pega registros NOVOS do Firebird
- Não repete

### ✅ Monitorar Acúmulo

Executar semanalmente:
```bash
python comparar_firebird_supabase.py
```

Se % cair abaixo de 95%, chamar:
```bash
python sincronizar_agora.py
```

---

## Tabelas Sincronizadas

| Tabela | Status | Pendentes |
|--------|--------|-----------|
| Clientes | ✓ 100% | 0 |
| Pedidos | 98.6% | 233 |
| Fórmulas | 98.7% | 433 |
| Fórmulas Itens | 98.7% | 4.616 |
| Rastreabilidade | 98.5% | 3.182 |
| Tipos Processo | ✓ 100% | 0 |

---

## Troubleshooting

### Erro: "Connection refused"
- Verificar se API está rodando: `docker ps | grep prime-sync`
- Reiniciar: `docker service update prime-sync-api --force-update`

### Erro: "Firebird connection timeout"
- Verificar banco: ping db.primesoftware.com.br
- Variáveis de ambiente: docker inspect prime-sync-api

### Acúmulo rápido (caiu 10% em 1 dia)
- Chamar `sincronizar_agora.py`
- Verificar logs da API
- Verificar volume de novos registros no Prime

---

## Automação Futura

Para não precisar chamar manualmente:

```python
# Adicionar ao app.py
@app.route('/sync-tudo', methods=['POST'])
def sync_tudo():
    """Sincroniza até zerar os pendentes"""
    while True:
        resultado = sincronizar_todos()
        if resultado['total'] == 0:
            break
    return {'status': 'completo'}
```

Depois basta: `curl -X POST https://sincro.oficialmed.com.br/sync-tudo`



