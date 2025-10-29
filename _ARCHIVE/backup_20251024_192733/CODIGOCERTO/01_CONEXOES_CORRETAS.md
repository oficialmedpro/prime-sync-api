# 🔌 CONEXÕES CORRETAS - FIREBIRD E SUPABASE

## 📋 Resumo das Configurações Validadas

### ✅ Firebird (Banco Principal - Prime Software)
```python
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}
```

**Status:** ✅ **CONECTADO E FUNCIONANDO**
- Host: `db.primesoftware.com.br`
- Database: `oficialmed1250`
- Usuário: `OFICIALMED`
- Senha: `Lt-@=waIh))Ql3~`
- Charset: `UTF8`

### ✅ Supabase (Banco de Destino)
```python
SUPABASE_CONFIG = {
    'url': 'https://agdffspstbxeqhqtltvb.supabase.co',
    'service_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA',
    'schema': 'api'
}
```

**Status:** ✅ **CONECTADO E FUNCIONANDO**
- URL: `https://agdffspstbxeqhqtltvb.supabase.co`
- Schema: `api`
- Service Key: Configurada e validada

## 🔧 Arquivos de Configuração Atualizados

### 1. `config_supabase.py`
```python
# Firebird Configuration (CREDENCIAIS CORRETAS)
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}
```

### 2. `exportar_firebird_supabase_final.py`
```python
# Firebird (CREDENCIAIS CORRETAS)
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}
```

### 3. `exportar_para_supabase_completo.py`
```python
# Firebird (usando credenciais do .env)
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}
```

### 4. `teste_conexoes.py`
```python
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}
```

### 5. `teste_conexao.py`
```python
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}
```

## 🧪 Teste de Conexão

### Script de Teste: `teste_conexao_correta.py`
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de conexão com Firebird e Supabase usando as credenciais corretas
"""

import fdb
import requests
from supabase import create_client

# Configurações corretas
FIREBIRD_CONFIG = {
    'host': 'db.primesoftware.com.br',
    'database': 'oficialmed1250',
    'user': 'OFICIALMED',
    'password': 'Lt-@=waIh))Ql3~',
    'charset': 'UTF8'
}

SUPABASE_URL = "https://agdffspstbxeqhqtltvb.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnZGZmc3BzdGJ4ZXFocXRsdHZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDQ1MzY2NiwiZXhwIjoyMDY2MDI5NjY2fQ.grInwGHFAH2WYvYerwfHkUsM08wXCJASg4CPMD2cTaA"

def testar_firebird():
    """Testa conexão com Firebird"""
    print("🔌 Testando conexão com Firebird...")
    
    try:
        conn = fdb.connect(
            host=FIREBIRD_CONFIG['host'],
            database=FIREBIRD_CONFIG['database'],
            user=FIREBIRD_CONFIG['user'],
            password=FIREBIRD_CONFIG['password'],
            charset=FIREBIRD_CONFIG['charset']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM CLIENTE WHERE ATIVO = -1")
        count = cursor.fetchone()[0]
        
        print(f"✅ Firebird conectado! {count} clientes ativos encontrados")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar no Firebird: {e}")
        return False

def testar_supabase():
    """Testa conexão com Supabase"""
    print("🔌 Testando conexão com Supabase...")
    
    try:
        # Teste via requests
        headers = {
            'apikey': SUPABASE_SERVICE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
            'Content-Type': 'application/json',
            'Accept-Profile': 'api',
            'Content-Profile': 'api'
        }
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/prime_clientes?select=id&limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Supabase conectado via API!")
            return True
        else:
            print(f"❌ Erro na API Supabase: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao conectar no Supabase: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testando conexões...")
    
    firebird_ok = testar_firebird()
    supabase_ok = testar_supabase()
    
    if firebird_ok and supabase_ok:
        print("\n🎉 Todas as conexões estão funcionando!")
    else:
        print("\n❌ Alguma conexão falhou!")
```

## 📝 Notas Importantes

1. **Credenciais Removidas:** Todas as configurações antigas/incorretas foram removidas dos arquivos
2. **Porta Removida:** O parâmetro `port` foi removido da conexão Firebird (não necessário)
3. **Charset UTF8:** Configurado para garantir compatibilidade com caracteres especiais
4. **Validação:** Ambas as conexões foram testadas e estão funcionando corretamente

## 🔄 Próximos Passos

1. ✅ Conexões validadas
2. ✅ Configurações atualizadas
3. ✅ Scripts de teste funcionando
4. 🔄 Pronto para exportação de dados
