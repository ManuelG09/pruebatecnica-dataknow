# Proyecto RetailMax - Arquitectura Lakehouse & Medallion en Azure

Este repositorio contiene la solución técnica de ingeniería de datos para el ecosistema **RetailMax**, implementando la arquitectura **Medallion (Bronze, Silver, Gold)** utilizando servicios administrados de **Microsoft Azure** y **Azure Data Factory**.

---

## 1. Arquitectura de la Solución

## 🏗️ 1. Arquitectura de la Solución

* **Origen Transaccional:** Generador Python con semilla determinista (`seed=42`) cargado a Azure SQL Database.
* **Orquestación:** Pipeline parametrizado en Azure Data Factory (`pl_ingesta_bronze`) con iteración `ForEach`.
* **Almacenamiento Medallion:** Azure Data Lake Storage Gen2 organizado en tres capas:
  * 🥉 **Bronze:** Almacenamiento crudo en formato Parquet.
  * 🥈 **Silver:** Limpieza de datos, reglas de calidad y tratamiento de PII.
  * 🥇 **Gold:** Modelo dimensional DWH y segmentación RFM.

---

## 📊 2. Generación Sintética de Datos (Semilla Fija)

Se implementó un motor en Python (`data-generation/data_generation.py`) utilizando una semilla determinista (`seed=42`) para asegurar **reproducibilidad total**.

### Métricas de Volumen Generado
* **`MSTR_PROVEEDORES`**: 800 registros (CSV y Parquet)
* **`MSTR_ARTICULOS`**: 5,000 registros (CSV y Parquet)
* **`MSTR_TIENDAS`**: 150 registros (CSV y Parquet)
* **`CRM_MIEMBROS`**: 50,000 registros (CSV y Parquet)
* **`TRANS_VENTAS`**: 1,003,000 registros
* **`INV_STOCK_DIARIO`**: 750,000 registros
* **`POST_DEVOLUCIONES`**: 50,000 registros

### Inyección Controlada de Anomalías (`anomalias_documentadas.json`)
Para validar el comportamiento de las capas de calidad en Azure, se inyectaron las siguientes imperfecciones
* **Duplicados exactos**: 3,000 registros
* **Fechas fuera de rango**: 1,003 registros
* **Integridad referencial rota**: 1,003 registros


---

## ☁️ 3. Infraestructura Cloud (Azure)

Se aprovisionaron los recursos mediante convención de nomenclatura estándar (`rg-`, `str`, `sql-`, `adf-`)

* **Resource Group**: `rg-prueba-retailmax-dataknow`
* **Storage Account (ADLS Gen2)**: `strpruebaretail_1788666721367` (con Namespace Jerárquico habilitado)
* **Azure SQL Server / Database**: `sqlserver-retailmax-v2` / `sql-db-retailmax`
* **Azure Data Factory**: `adf-prueba-retailmax`


### Configuración del Data Lake (Contenedores)
Se crearon contenedores aislados para garantizar control de acceso granular (RBAC) y gestión de ciclo de vida:
1. **`bronze`**: Almacenamiento crudo en formato Parquet.
2. **`silver`**: Capa depurada y libre de anomalías.
3. **`gold`**: Tablas analíticas y dimensiones.

---

## 🔄 4. Orquestación e Ingesta (Azure Data Factory)

Para garantizar escalabilidad, se diseñó un **Pipeline Dirigido por Metadatos** (`pl_ingesta_bronze`) utilizando un enfoque recursivo en lugar de duplicar actividades:

* **Dataset Parametrizado SQL (`ds_sql_source`)**: Recibe la variable del nombre de tabla en ejecución.
* **Dataset Parametrizado Parquet (`ds_datalake_bronze`)**: Escribe directamente en el contenedor Bronze.
* **Control `ForEach`**: Itera sobre la lista de las 7 tablas origen ejecutando una única actividad `Copy Activity` reutilizable (`cp_tabla_bronze`).


---

## 📁 5. Estructura del Repositorio

```text
├── data-generation/
│   ├── config.yaml
│   └── data_generation.py
├── evidence/
│   ├── 1_Generacion_Data.png
│   ├── 2_Grupo_Recursos.png
│   ├── 3_Contenedores.png
│   ├── 4_Ingesta_Bronze.png
|   └── 5_Pipeline.png
├── pipelines/
│   ├── pl_ingesta_bronze.json
│   └──  pl_transformacion_silver.json 
├── .gitignore
├── test_connection.py
└── README.md