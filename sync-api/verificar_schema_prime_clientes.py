#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar schema da tabela prime_clientes no Supabase
Data: 27/10/2025
"""

import requests
import os

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('VITE_SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Configure SUPABASE_URL e SUPABASE_KEY")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Accept-Profile': 'api'
}

print("="*80)
print("VERIFICANDO SCHEMA: api.prime_clientes")
print("="*80)

# Fazer uma query que retorna 1 registro para ver os campos
url = f"{SUPABASE_URL}/rest/v1/prime_clientes"
response = requests.get(
    url,
    headers=headers,
    params={'select': '*', 'limit': 1}
)

if response.status_code == 200:
    dados = response.json()
    if dados:
        print("\nCAMPOS DISPONIVEIS na tabela prime_clientes:")
        print("-"*80)
        
        campos = list(dados[0].keys())
        campos.sort()
        
        for i, campo in enumerate(campos, 1):
            valor_exemplo = dados[0][campo]
            tipo = type(valor_exemplo).__name__
            print(f"{i:2}. {campo:<30} (tipo: {tipo}, exemplo: {str(valor_exemplo)[:30]})")
        
        print("\n" + "="*80)
        print("CAMPOS QUE O CODIGO PYTHON ESTA TENTANDO INSERIR:")
        print("="*80)
        
        campos_codigo = [
            'codigo_cliente_original',
            'nome',
            'cpf_cnpj',
            'email',
            'telefone',
            'endereco_logradouro',
            'endereco_numero',
            'endereco_cidade',
            'endereco_estado',
            'endereco_cep',
            'data_nascimento',
            'sexo',
            'ativo',
            'updated_at'
        ]
        
        print("\nCampos no codigo Python:")
        for campo in campos_codigo:
            if campo in campos:
                print(f"  OK  {campo}")
            else:
                print(f"  ERRO {campo} <- NAO EXISTE NA TABELA!")
        
        print("\n" + "="*80)
        print("CAMPOS NA TABELA QUE NAO ESTAO NO CODIGO:")
        print("="*80)
        
        campos_faltando = [c for c in campos if c not in campos_codigo]
        if campos_faltando:
            for campo in campos_faltando:
                print(f"  -> {campo}")
        else:
            print("  (nenhum)")
            
    else:
        print("\nTabela vazia, nao foi possivel verificar campos")
else:
    print(f"\nErro ao consultar Supabase: {response.status_code}")
    print(response.text)

print("\n")



