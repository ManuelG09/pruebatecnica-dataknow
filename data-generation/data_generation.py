"""
Generador de datos sintéticos - Escenario B
Prueba técnica de Ingeniero de Datos - DataKnow
Autor: Manuel Alejandro Gomez Paredes

Generar las 7 tablas fuente segun documentacion

SUPUESTO DOCUMENTADO: el enunciado no incluye una tabla de centros de
distribución entre las fuentes oficiales, pero el contexto de negocio
menciona 3 CD regionales (Bogotá, Ciudad de México, Santiago de Chile)
usados para calcular tiempo de reabastecimiento. Se añade el campo
'centro_distribucion' en MSTR_TIENDAS, asignado por país, como proxy
simplificado de esa relación logística.
"""

import os
import json
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yaml
from faker import Faker


# 1. CARGA DE CONFIGURACIÓN Y SEMILLA

with open("config.yaml", "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

SEED = CFG["seed"]
random.seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)
fake = Faker("es_CO")
Faker.seed(SEED)

VOL = CFG["volumenes"]
FECHA_FIN = datetime.strptime(CFG["fecha_fin"], "%Y-%m-%d")
FECHA_INICIO = FECHA_FIN - timedelta(days=CFG["dias_historico"])
PCT_NULOS = CFG["pct_nulos"]

OUTPUT_DIR = "output"
os.makedirs(f"{OUTPUT_DIR}/csv", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/parquet", exist_ok=True)

PAISES = ["Colombia", "Mexico", "Chile", "Peru", "Ecuador"]
CATEGORIAS_N1 = [
    "Alimentos y bebidas", "Cuidado personal e higiene", "Hogar y limpieza",
    "Electronica y tecnologia", "Ropa y calzado basico", "Bebes y maternidad",
]
TIPOS_TIENDA = ["Hipermercado", "Supermercado de barrio", "Tienda de conveniencia"]
CANALES = ["Tienda fisica", "Ecommerce", "Marketplace"]
TIPOS_PAGO = ["Efectivo", "Tarjeta debito", "Tarjeta credito", "Billetera digital"]

# Asignación de centro de distribución por país
CENTROS_DISTRIBUCION = {
    "Colombia": "CD Bogota",
    "Mexico": "CD Ciudad de Mexico",
    "Chile": "CD Santiago de Chile",
    "Peru": "CD Bogota",       
    "Ecuador": "CD Bogota",
# Se hace la cobertura desde el CD más cercano disponible    
}


def inject_nulls(df, columns, frac=PCT_NULOS):
    """Introduce ~frac% de nulos en columnas no críticas (calidad de datos real)."""
    for col in columns:
        n = int(len(df) * frac)
        idx = rng.choice(df.index, size=n, replace=False)
        df.loc[idx, col] = np.nan
    return df


def save(df, name):
    df.to_csv(f"{OUTPUT_DIR}/csv/{name}.csv", index=False)
    df.to_parquet(f"{OUTPUT_DIR}/parquet/{name}.parquet", index=False)
    print(f"  {name}: {len(df):,} registros -> CSV y Parquet")


# 2. MSTR_PROVEEDORES

def gen_proveedores():
    n = VOL["MSTR_PROVEEDORES"]
    df = pd.DataFrame({
        "id_proveedor": range(1, n + 1),
        "razon_social": [fake.company() for _ in range(n)],
        "pais_origen": rng.choice(PAISES, n),
        "tiempo_repo_dias": rng.integers(1, 15, n),
        "calificacion_calidad": np.round(np.clip(rng.normal(4.0, 0.6, n), 1, 5), 1),
        "activo": rng.choice([True, False], n, p=[0.9, 0.1]),
    })
    df = inject_nulls(df, ["calificacion_calidad"])
    save(df, "MSTR_PROVEEDORES")
    return df


# 3. MSTR_ARTICULOS

def gen_articulos(proveedores_ids):
    n = VOL["MSTR_ARTICULOS"]
    cat_n1 = rng.choice(CATEGORIAS_N1, n)
    df = pd.DataFrame({
        "art_id": range(1, n + 1),
        "cod_barra": [fake.ean13() for _ in range(n)],
        "desc_art": [f"{fake.word().capitalize()} {fake.word()}" for _ in range(n)],
        "id_categ_n1": cat_n1,
        "id_categ_n2": [f"{c[:4]}-{rng.integers(1,4)}" for c in cat_n1],
        "id_categ_n3": [f"{c[:4]}-{rng.integers(1,4)}-{rng.integers(1,3)}" for c in cat_n1],
        "id_proveedor": rng.choice(proveedores_ids, n),
        "precio_lista": np.round(rng.uniform(2000, 250000, n), -2),
        "peso_kg": np.round(rng.uniform(0.05, 20, n), 2),
        "unid_medida": rng.choice(["UN", "KG", "LT"], n, p=[0.7, 0.2, 0.1]),
        "activo": rng.choice([True, False], n, p=[0.92, 0.08]),
        "fec_alta": [FECHA_INICIO + timedelta(days=int(d)) for d in rng.integers(0, 200, n)],
    })
    df = inject_nulls(df, ["peso_kg"])
    save(df, "MSTR_ARTICULOS")
    return df


# 4. MSTR_TIENDAS (incluye centro_distribucion - supuesto documentado)

def gen_tiendas():
    n = VOL["MSTR_TIENDAS"]
    paises = rng.choice(PAISES, n, p=[0.4, 0.25, 0.15, 0.12, 0.08])
    df = pd.DataFrame({
        "id_tienda": range(1, n + 1),
        "nom_tienda": [f"RetailMax {fake.city()}" for _ in range(n)],
        "tipo_tienda": rng.choice(TIPOS_TIENDA, n, p=[0.3, 0.5, 0.2]),
        "id_ciudad": [fake.city() for _ in range(n)],
        "id_pais": paises,
        "centro_distribucion": [CENTROS_DISTRIBUCION[p] for p in paises],
        "metros_cuadrados": rng.integers(150, 8000, n),
        "activo": rng.choice([True, False], n, p=[0.95, 0.05]),
        "fec_apertura": [FECHA_INICIO - timedelta(days=int(d)) for d in rng.integers(0, 3000, n)],
    })
    save(df, "MSTR_TIENDAS")
    return df


# 5. CRM_MIEMBROS

def gen_miembros():
    n = VOL["CRM_MIEMBROS"]
    df = pd.DataFrame({
        "id_miembro": range(1, n + 1),
        "fec_registro": [FECHA_INICIO - timedelta(days=int(d)) for d in rng.integers(0, 1500, n)],
        "id_ciudad": [fake.city() for _ in range(n)],
        "genero": rng.choice(["F", "M", "No informado"], n, p=[0.52, 0.45, 0.03]),
        "rango_edad": rng.choice(["18-25", "26-35", "36-45", "46-60", "60+"], n, p=[0.15, 0.3, 0.28, 0.18, 0.09]),
        "canal_pref": rng.choice(CANALES, n, p=[0.55, 0.35, 0.10]),
        "activo": rng.choice([True, False], n, p=[0.85, 0.15]),
        "fec_ultima_compra": [FECHA_FIN - timedelta(days=int(d)) for d in rng.integers(0, 400, n)],
    })
    df = inject_nulls(df, ["rango_edad", "genero"])
    save(df, "CRM_MIEMBROS")
    return df


# 6. TRANS_VENTAS (con concentración en horarios pico)

def gen_ventas(miembros_ids, tiendas_ids, articulos_df):
    n = VOL["TRANS_VENTAS"]
    art_ids = articulos_df["art_id"].values
    precios = articulos_df.set_index("art_id")["precio_lista"]

    dias = rng.integers(0, 365, n)
    fechas = [FECHA_INICIO + timedelta(days=int(d)) for d in dias]

    horas_pico = rng.choice([12, 13, 14, 18, 19, 20], n, p=[0.15, 0.15, 0.15, 0.2, 0.2, 0.15])
    ruido = rng.integers(-1, 2, n)
    horas = np.clip(horas_pico + ruido, 8, 21)
    minutos = rng.integers(0, 60, n)

    art_sel = rng.choice(art_ids, n)
    precio_unit = np.round(precios.loc[art_sel].values * rng.uniform(0.95, 1.05, n), -1)
    qty = rng.integers(1, 6, n)
    descuento = np.where(rng.random(n) < 0.25, np.round(rng.uniform(0.05, 0.3, n), 2), 0.0)

    id_miembro = rng.choice(list(miembros_ids), n).astype(object)
    mask_anon = rng.random(n) < 0.10  # 10% compras sin miembro identificado
    id_miembro[mask_anon] = None

    df = pd.DataFrame({
        "id_trans": range(1, n + 1),
        "id_miembro": id_miembro,
        "id_tienda": rng.choice(tiendas_ids, n),
        "art_id": art_sel,
        "fec_trans": fechas,
        "hra_trans": [f"{h:02d}:{m:02d}:00" for h, m in zip(horas, minutos)],
        "qty_vendida": qty,
        "precio_unitario_venta": precio_unit,
        "descuento_aplicado": descuento,
        "tipo_pago": rng.choice(TIPOS_PAGO, n, p=[0.15, 0.35, 0.4, 0.1]),
        "canal_venta": rng.choice(CANALES, n, p=[0.55, 0.35, 0.1]),
    })
    df = inject_nulls(df, ["descuento_aplicado"])
    return df


# 7. INV_STOCK_DIARIO

def gen_stock(articulos_ids, tiendas_ids):
    n = VOL["INV_STOCK_DIARIO"]
    dias = rng.integers(0, 365, n)
    fechas = [FECHA_INICIO + timedelta(days=int(d)) for d in dias]
    stock_min = rng.integers(5, 50, n)

    df = pd.DataFrame({
        "id_snapshot": range(1, n + 1),
        "art_id": rng.choice(articulos_ids, n),
        "id_tienda": rng.choice(tiendas_ids, n),
        "fec_snapshot": fechas,
        "stock_fisico": rng.integers(0, 500, n),
        "stock_transito": rng.integers(0, 100, n),
        "stock_reservado": rng.integers(0, 30, n),
        "stock_minimo_config": stock_min,
        "stock_maximo_config": stock_min + rng.integers(50, 300, n),
    })
    df = inject_nulls(df, ["stock_transito"])
    save(df, "INV_STOCK_DIARIO")
    return df


# 8. POST_DEVOLUCIONES (referencia transacciones reales)

def gen_devoluciones(ventas_df):
    n = VOL["POST_DEVOLUCIONES"]
    muestra = ventas_df.sample(n=n, random_state=SEED, replace=False)
    motivos = ["Producto defectuoso", "Talla incorrecta", "No cumple expectativas", "Error en pedido", "Producto vencido"]

    df = pd.DataFrame({
        "id_devolucion": range(1, n + 1),
        "id_trans_origen": muestra["id_trans"].values,
        "art_id": muestra["art_id"].values,
        "id_tienda": muestra["id_tienda"].values,
        "fec_devolucion": [pd.Timestamp(f) + timedelta(days=int(d)) for f, d in
                            zip(muestra["fec_trans"], rng.integers(1, 20, n))],
        "qty_devuelta": rng.integers(1, 3, n),
        "motivo_cod": rng.choice(motivos, n, p=[0.25, 0.2, 0.25, 0.2, 0.1]),
        "canal_devolucion": rng.choice(CANALES, n, p=[0.6, 0.3, 0.1]),
        "estado_devolucion": rng.choice(["Aprobada", "Rechazada", "En proceso"], n, p=[0.7, 0.1, 0.2]),
        "vr_reembolso": np.round(muestra["precio_unitario_venta"].values * rng.uniform(0.8, 1.0, n), -2),
    })
    save(df, "POST_DEVOLUCIONES")
    return df


# 9. ANOMALÍAS INTENCIONALES (documentadas para el README)

def inject_anomalias(ventas_df):
    log = {}
    cfg_an = CFG["anomalias"]

    # Anomalía 1: transacciones duplicadas exactas
    dup = ventas_df.sample(frac=cfg_an["pct_duplicados"], random_state=SEED)
    ventas_df = pd.concat([ventas_df, dup], ignore_index=True)
    log["duplicados_exactos"] = len(dup)

    # Anomalía 2: fechas fuera de rango (posteriores a la fecha fin del histórico)
    idx_fecha = rng.choice(ventas_df.index, size=int(len(ventas_df) * cfg_an["pct_fechas_fuera_rango"]), replace=False)
    ventas_df.loc[idx_fecha, "fec_trans"] = FECHA_FIN + timedelta(days=30)
    log["fechas_fuera_de_rango"] = len(idx_fecha)

    # Anomalía 3: integridad referencial rota (art_id que no existe en MSTR_ARTICULOS)
    idx_ref = rng.choice(ventas_df.index, size=int(len(ventas_df) * cfg_an["pct_integridad_rota"]), replace=False)
    ventas_df.loc[idx_ref, "art_id"] = 999999
    log["integridad_referencial_rota"] = len(idx_ref)

    with open(f"{OUTPUT_DIR}/anomalias_documentadas.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"  Anomalías inyectadas: {log}")
    return ventas_df


# MAIN

def main():
    print(f"Generando datos sintéticos RetailMax (seed={SEED})...\n")

    proveedores = gen_proveedores()
    articulos = gen_articulos(proveedores["id_proveedor"].values)
    tiendas = gen_tiendas()
    miembros = gen_miembros()

    print("\nGenerando TRANS_VENTAS (puede tardar unos segundos)...")
    ventas = gen_ventas(miembros["id_miembro"].values, tiendas["id_tienda"].values, articulos)
    ventas = inject_anomalias(ventas)
    save(ventas, "TRANS_VENTAS")

    gen_stock(articulos["art_id"].values, tiendas["id_tienda"].values)
    gen_devoluciones(ventas)

    print("\nGeneración completa. Archivos en /output/csv y /output/parquet")


if __name__ == "__main__":
    main()