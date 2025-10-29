#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste: Descobrir campos corretos da tabela prime_clientes
Estratégia: Tentar inserir e ver o erro
"""

import requests
import os
from datetime import datetime

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('VITE_SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Configure SUPABASE_URL e SUPABASE_KEY")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api',
    'Content-Profile': 'api',
    'Prefer': 'return=representation'
}

print("="*80)
print("TESTE: Descobrir campos da tabela prime_clientes")
print("="*80)

# 1. Primeiro, buscar 1 registro existente para ver os campos
print("\n1. Buscando 1 registro existente...")
url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
response = requests.get(
    url,
    headers=headers,
    params={'select': '*', 'limit': 1}
)

if response.status_code == 200:
    dados = response.json()
    if dados:
        print("   OK - Registro encontrado!")
        print("\n   CAMPOS DISPONIVEIS:")
        campos_existentes = list(dados[0].keys())
        campos_existentes.sort()
        
        for campo in campos_existentes:
            valor = dados[0][campo]
            print(f"      - {campo:<30} = {valor}")
        
        # 2. Criar dict com APENAS os campos que existem
        print("\n" + "="*80)
        print("2. Montando cliente de teste com campos corretos...")
        print("="*80)
        
        cliente_teste = {}
        
        # Mapear campos
        if 'codigo_cliente_original' in campos_existentes:
            cliente_teste['codigo_cliente_original'] = 99999998  # Código de teste
        
        if 'nome' in campos_existentes:
            cliente_teste['nome'] = 'TESTE SYNC API'
        
        if 'cpf_cnpj' in campos_existentes:
            cliente_teste['cpf_cnpj'] = '00000000000'
        
        if 'email' in campos_existentes:
            cliente_teste['email'] = 'teste@oficialmed.com.br'
        
        if 'telefone' in campos_existentes:
            cliente_teste['telefone'] = '11999999999'
        
        if 'endereco_logradouro' in campos_existentes:
            cliente_teste['endereco_logradouro'] = 'Rua Teste'
        
        if 'endereco_numero' in campos_existentes:
            cliente_teste['endereco_numero'] = '123'
        
        if 'endereco_cidade' in campos_existentes:
            cliente_teste['endereco_cidade'] = 'São Paulo'
        
        if 'endereco_estado' in campos_existentes:
            cliente_teste['endereco_estado'] = 'SP'
        
        if 'endereco_cep' in campos_existentes:
            cliente_teste['endereco_cep'] = '01234567'
        
        if 'data_nascimento' in campos_existentes:
            cliente_teste['data_nascimento'] = '1990-01-01'
        
        if 'sexo' in campos_existentes:
            cliente_teste['sexo'] = 'M'
        
        if 'ativo' in campos_existentes:
            cliente_teste['ativo'] = True
        
        if 'updated_at' in campos_existentes:
            cliente_teste['updated_at'] = datetime.now().isoformat()
        
        print("\n   Cliente de teste montado:")
        for k, v in cliente_teste.items():
            print(f"      {k} = {v}")
        
        print("\n" + "="*80)
        print("CAMPOS QUE O CODIGO PYTHON DEVE USAR:")
        print("="*80)
        print("\ncliente = {")
        for campo in cliente_teste.keys():
            print(f"    '{campo}': valor,")
        print("}")
        
    else:
        print("   Tabela vazia!")
else:
    print(f"   ERRO: {response.status_code}")
    print(f"   {response.text}")

print("\n")




