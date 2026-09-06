import pandas as pd
from sqlalchemy import create_engine, event
from dotenv import load_dotenv
import os
import urllib.parse
import time

load_dotenv()

params = urllib.parse.quote_plus(
    f"DRIVER={os.getenv('DB_DRIVER')};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)

tablas = {
    "MSTR_PROVEEDORES": "data-generation/output/parquet/MSTR_PROVEEDORES.parquet",
    "MSTR_ARTICULOS": "data-generation/output/parquet/MSTR_ARTICULOS.parquet",
    "MSTR_TIENDAS": "data-generation/output/parquet/MSTR_TIENDAS.parquet",
    "CRM_MIEMBROS": "data-generation/output/parquet/CRM_MIEMBROS.parquet",
    "TRANS_VENTAS": "data-generation/output/parquet/TRANS_VENTAS.parquet",
    "INV_STOCK_DIARIO": "data-generation/output/parquet/INV_STOCK_DIARIO.parquet",
    "POST_DEVOLUCIONES": "data-generation/output/parquet/POST_DEVOLUCIONES.parquet",
}

for nombre_tabla, ruta_archivo in tablas.items():
    inicio = time.time()
    print(f"Cargando {nombre_tabla}...")

    df = pd.read_parquet(ruta_archivo)

    df.to_sql(
        name=nombre_tabla,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=5000
    )

    duracion = time.time() - inicio
    print(f"  -> {len(df)} filas cargadas en {duracion:.1f}s")

print("Carga completa de las 7 tablas.")