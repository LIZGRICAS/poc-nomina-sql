<div align="center">

# 🧾 POC — Procesamiento de Novedades de Horas Extras

**Pipeline ETL en Python** que automatiza la recepción, validación e inserción de registros de horas extras desde un archivo CSV hacia **SQL Server**, aplicando reglas de negocio estrictas y trazabilidad completa de errores.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-red?logo=microsoftsqlserver&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Estado](https://img.shields.io/badge/Estado-POC%20funcional-brightgreen)

</div>

---

## 📋 Tabla de contenido

- [🧾 POC — Procesamiento de Novedades de Horas Extras](#-poc--procesamiento-de-novedades-de-horas-extras)
  - [📋 Tabla de contenido](#-tabla-de-contenido)
  - [📌 Descripción](#-descripción)
  - [📁 Estructura del proyecto](#-estructura-del-proyecto)
  - [🐳 Inicio rápido con Docker](#-inicio-rápido-con-docker)
  - [🛠️ Instalación manual](#️-instalación-manual)
  - [📏 Reglas de negocio](#-reglas-de-negocio)
  - [📊 Resultados sobre el CSV de prueba](#-resultados-sobre-el-csv-de-prueba)
    - [Desglose de errores detectados](#desglose-de-errores-detectados)
  - [🧩 Modelo de datos](#-modelo-de-datos)
  - [� Transaccionalidad](#-transaccionalidad)
  - [📤 Salidas generadas](#-salidas-generadas)
  - [🚀 Visión a futuro — Arquitectura objetivo](#-visión-a-futuro--arquitectura-objetivo)
    - [Diagrama conceptual](#diagrama-conceptual)
    - [Escalabilidad — cientos de miles de registros](#escalabilidad--cientos-de-miles-de-registros)
    - [Multi-tenant — cientos de clientes](#multi-tenant--cientos-de-clientes)
    - [Extensibilidad — nuevos tipos de novedad](#extensibilidad--nuevos-tipos-de-novedad)
    - [Integración vía API — reemplazar el CSV](#integración-vía-api--reemplazar-el-csv)
    - [Skeleton FastAPI + microservicios](#skeleton-fastapi--microservicios)
  - [🔐 Seguridad](#-seguridad)

---

## 📌 Descripción

El módulo legacy de horas extras permite la entrada de datos sucios: horas negativas, tipos de recargo inventados y valores de texto donde deberían ir números. Esto rompe el procesamiento masivo de nómina.

Esta POC resuelve el problema con un pipeline que:

1. **Lee** el archivo CSV automáticamente.
2. **Valida** cada registro contra las reglas de negocio.
3. **Inserta** los registros limpios en SQL Server dentro de una transacción atómica.
4. **Registra** los rechazados con su motivo de fallo, tanto en CSV local como en tabla de BD.

---

## 📁 Estructura del proyecto

```
poc-nomina/
│
├── process_novedades.py        ← 🔧 Script ETL principal
├── errores_table.sql           ← DDL tabla de errores en BD
├── prueba-tecnica.sql          ← DDL tabla destino (provista)
│
├── init/                       ← Scripts de inicialización automática (Docker)
│   ├── 01_create_db.sql
│   └── 02_create_tables.sql
│
├── Dockerfile                  ← Imagen del ETL
├── docker-compose.yml          ← Orquestación completa (SQL Server + ETL)
│
├── requirements.txt
├── .env.example                ← Plantilla de variables de entorno
│
└── logs/                       ← Generados en cada ejecución
    ├── errores_YYYYMMDD_HHMMSS.csv
    └── ejecucion_YYYYMMDD_HHMMSS.log
```

---

## 🐳 Inicio rápido con Docker

> La forma más rápida de ver la demo completa. **No requiere instalar Python ni SQL Server manualmente.**

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd poc-nomina

# 2. Levantar todo el entorno
docker compose up --build
```

Docker se encarga de:
- ✅ Levantar **SQL Server 2022**
- ✅ Crear la base de datos `PruebaNomina` y sus tablas automáticamente
- ✅ Ejecutar el **ETL** al finalizar la inicialización
- ✅ Dejar los logs en la carpeta `./logs/` de tu máquina

---

## 🛠️ Instalación manual

**Prerrequisitos**
- Python 3.10+
- SQL Server con la base de datos `PruebaNomina` creada (ver `prueba-tecnica.sql`)
- [ODBC Driver 17 para SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

**Pasos**

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales
cp .env.example .env
# → Editar .env con los datos reales de conexión

# Ejecutar el ETL
python process_novedades.py novedades_extra.csv
```

**Variables de entorno** (`.env`)

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `DB_SERVER` | Host del servidor SQL | `localhost` |
| `DB_NAME` | Nombre de la base de datos | `PruebaNomina` |
| `DB_USER` | Usuario SQL | `sa` |
| `DB_PASSWORD` | Contraseña SQL | *(requerida)* |

---

## 📏 Reglas de negocio

Todos los registros pasan por las siguientes validaciones antes de ser insertados:

| Código de error | Regla |
|-----------------|-------|
| `documento_empleado_vacio` | El campo `documento` no puede ser nulo o vacío |
| `cantidad_horas_vacia` | El campo `cantidad_horas` no puede ser nulo |
| `cantidad_horas_no_numerica` | Debe ser un número — `"cinco"` es inválido |
| `cantidad_horas_no_positiva` | Debe ser estrictamente mayor a `0` |
| `tipo_hora_extra_vacio` | El tipo de hora no puede ser nulo |
| `tipo_hora_extra_invalido` | Solo se permiten: `HE_DIURNA` · `HE_NOCTURNA` · `HE_DOMINICAL` · `HE_FESTIVA` |

---

## 📊 Resultados sobre el CSV de prueba

El archivo `novedades_extra.csv` contiene **60 registros** con datos intencionalmente sucios.

| Estado | Registros |
|--------|-----------|
| ✅ Válidos e insertados en BD | **42** |
| ❌ Rechazados con error | **18** |

### Desglose de errores detectados

| Motivo | Cantidad |
|--------|----------|
| Documento vacío | 3 |
| Tipo de hora inválido (`HE_INVENTADA`, `HE_OTRACOSA`, `HE_ERROR`, vacío) | 5 |
| Horas negativas o iguales a cero | 7 |
| Horas no numéricas (`"cinco"`, `"tres"`) | 2 |
| Horas vacías (`NaN`) | 2 |

---

## 🧩 Modelo de datos

```
┌────────────────────────────────────────────┐
│        Novedades_HorasExtras              │
├────────────────────────────────────────────┤
│ Id (PK)                                   │
│ DocumentoEmpleado                         │
│ TipoHoraExtra                             │
│ CantidadHoras                             │
│ FechaProcesamiento                        │
│ EstadoValidacion                          │
└────────────────────────────────────────────┘
                 │
                 │ 1:N (lógico, no FK obligatoria)
                 ▼
┌────────────────────────────────────────────┐
│   Novedades_HorasExtras_Errores           │
├────────────────────────────────────────────┤
│ Id (PK)                                   │
│ DocumentoEmpleado                         │
│ TipoHoraExtra                             │
│ CantidadHoras                             │
│ MotivoError                               │
│ FechaProcesamiento                        │
│ NovedadId (FK opcional)                  │
└────────────────────────────────────────────┘
```
---
## 🔒 Transaccionalidad

Los 42 registros válidos se insertan en **una única transacción atómica**.

```
BEGIN TRANSACTION
  INSERT registro_1 ✓
  INSERT registro_2 ✓
  ...
  INSERT registro_42 ✓
COMMIT  ← solo si todos fueron exitosos
```

Si cualquier `INSERT` falla → `ROLLBACK` completo. **Nunca queda un lote parcialmente insertado.**

---

## 📤 Salidas generadas

Cada ejecución produce tres salidas:

```
📦 Base de datos
   └── Novedades_HorasExtras        → 42 registros limpios
   └── Novedades_HorasExtras_Errores → 18 registros rechazados con motivo

📄 logs/errores_TIMESTAMP.csv       → Respaldo local de registros rechazados
📋 logs/ejecucion_TIMESTAMP.log     → Trazado completo de la ejecución
```

---

## 🚀 Visión a futuro — Arquitectura objetivo

> El entregable actual es un **script Python puro**. Esta sección describe cómo evolucionarlo sin rehacer nada desde cero.

### Diagrama conceptual

```
┌───────────────────────────────┐
│   Power Automate / Blob Trigger│
│  · Detecta CSV en SharePoint   │
│  · Llama API REST              │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│      API Gateway (FastAPI)    │
│  · POST /api/novedades        │
│  · Autenticación OAuth2       │
└──────┬──────────┬─────────────┘
       │          │           │
       ▼          ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Ingesta  │ │Validación│ │   Logging    │
│ Lee CSV  │ │ Reglas   │ │ Errores      │
│ Parsea   │ │ negocio  │ │ Auditoría    │
└──────────┘ └──────────┘ └──────────────┘
       │          │           │
       └──────────┴───────────┘
                  │
                  ▼
┌───────────────────────────────┐
│     Azure SQL Database        │
│  · Novedades_HorasExtras      │
│  · Novedades_HorasExtras_Err  │
└───────────────────────────────┘
```

### Escalabilidad — cientos de miles de registros

- Reemplazar el loop row-by-row por `cursor.executemany()` con `fast_executemany=True`.
- Para volúmenes extremos: **Azure Data Factory** con Dataflow o **Azure Databricks**.
- Arquitectura serverless con **Azure Functions** para escalar automáticamente por demanda.

### Multi-tenant — cientos de clientes

- Parametrizar el pipeline con `tenant_id`: cada cliente tiene su carpeta/bucket de entrada y su schema destino.
- En la nube: un **Azure Blob trigger** por contenedor (`/clients/{tenant_id}/inbox/`).
- Añadir campo `ClienteId` en las tablas para separación lógica de datos.

### Extensibilidad — nuevos tipos de novedad

- Las validaciones actuales son configurables: cada tipo de novedad define sus reglas en un diccionario, no en código duro.
- Una tabla `TiposNovedad` en BD permite agregar incapacidades, bonos o vacaciones **sin redespliegues**.

### Integración vía API — reemplazar el CSV

- Exponer el motor de validación como `POST /api/novedades` (FastAPI).
- El payload JSON reemplaza al CSV; la lógica de validación e inserción es **idéntica**.
- Autenticación por cliente con **OAuth2** vía Azure API Management.

### Skeleton FastAPI + microservicios

```
project-root/
│
├── app/
│   ├── main.py                  # API Gateway (FastAPI)
│   ├── config.py                # Configuración multi-tenant y env vars
│   ├── dependencies.py          # Conexiones compartidas (SQL, auth)
│   │
│   ├── routers/
│   │   ├── ingest.py            # POST /csv — subir y leer archivo
│   │   ├── validate.py          # POST /validar — reglas de negocio
│   │   └── errors.py            # GET /errores — consultar rechazados
│   │
│   ├── services/
│   │   ├── ingest_service.py    # Parsing CSV / JSON
│   │   ├── validate_service.py  # Motor de validación
│   │   ├── logging_service.py   # Registro de errores y auditoría
│   │   └── sql_service.py       # Inserción transaccional
│   │
│   ├── models/
│   │   ├── schemas.py           # Pydantic (request / response)
│   │   └── db_models.py         # SQLAlchemy (tablas)
│   │
│   ├── utils/
│   │   ├── tenant_utils.py      # Manejo multi-tenant
│   │   ├── csv_utils.py         # Funciones de parsing
│   │   └── error_utils.py       # Generación de mensajes de error
│   │
│   └── tests/
│       ├── test_ingest.py
│       ├── test_validate.py
│       └── test_logging.py
│
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔐 Seguridad

| Práctica | Implementación |
|----------|---------------|
| Sin credenciales en código | Todas las contraseñas se leen de variables de entorno (`.env`) |
| `.env` fuera del repo | `.gitignore` incluye `.env`; solo se sube `.env.example` |
| Revisión del código generado con IA | Cada sección fue validada manualmente y probada con dry-run contra el CSV real antes de conectar a BD |
| Transacciones atómicas | Ningún lote queda parcialmente insertado ante fallos |

---

<div align="center">

Desarrollado como parte de la prueba técnica para **Desarrollador Fullstack** — [gigha.com.co](https://gigha.com.co)

</div>
#   p o c - n o m i n a - s q l  
 