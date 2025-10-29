#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import fdb

# Códigos de clientes sem telefone no Supabase
codigos = [20601, 34142, 30156, 30157, 30243, 30872, 30940, 30990, 30991, 31120]

FIREBIRD_HOST = 'db.primesoftware.com.br'
FIREBIRD_DB = 'oficialmed1250'
FIREBIRD_USER = 'OFICIALMED'
FIREBIRD_PASS = 'Lt-@=waIh))Ql3~'

conn = fdb.connect(
    host=FIREBIRD_HOST,
    database=FIREBIRD_DB,
    user=FIREBIRD_USER,
    password=FIREBIRD_PASS,
    charset='UTF8'
)

cursor = conn.cursor()

print("="*80)
print("VERIFICANDO SE CLIENTES SEM TELEFONE NO SUPABASE TÊM NO FIREBIRD")
print("="*80)

codigos_str = ','.join(map(str, codigos))

cursor.execute(f"""
    SELECT 
        CT.CODIGO_CADASTRO,
        C.NOMECLIENTE,
        CT.TELEFONEPREFIXO,
        CT.TELEFONE
    FROM CADASTRO_TELEFONE CT
    INNER JOIN CLIENTE C ON C.CODIGO = CT.CODIGO_CADASTRO
    WHERE CT.TIPO_CADASTRO = 1
    AND CT.CODIGO_CADASTRO IN ({codigos_str})
    AND CT.TELEFONE IS NOT NULL
""")

clientes_com_tel_fb = cursor.fetchall()

print(f"\nAnalisados: {len(codigos)} clientes")
print(f"TÊM telefone no Firebird: {len(clientes_com_tel_fb)}")
print(f"NÃO TÊM telefone no Firebird: {len(codigos) - len(clientes_com_tel_fb)}")

if clientes_com_tel_fb:
    print(f"\n[ERRO] {len(clientes_com_tel_fb)} clientes COM telefone no Firebird mas SEM no Supabase:")
    for row in clientes_com_tel_fb:
        tel = (str(row[2] or '') + str(row[3] or '')).strip()
        print(f"   - {row[0]}: {row[1]} - Tel: {tel}")
else:
    print(f"\n[OK] Todos os {len(codigos)} clientes NÃO TÊM telefone nem no Firebird!")
    print("Sincronização está CORRETA!")

conn.close()
print("="*80)


