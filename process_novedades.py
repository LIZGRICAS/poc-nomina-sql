"""
POC - Procesamiento de Novedades de Horas Extras
Autor: Prueba Técnica Fullstack
Descripción: Script ETL que valida e inserta registros de horas extras
             desde un archivo CSV hacia una base de datos SQL Server.
             Los errores se persisten tanto en CSV local como en tabla BD.
"""

import pandas as pd
import pyodbc
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Carga .env si existe — en Docker las vars llegan por environment:
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

TIPOS_VALIDOS = {"HE_DIURNA", "HE_NOCTURNA", "HE_DOMINICAL", "HE_FESTIVA"}

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE  = LOG_DIR / f"errores_{TIMESTAMP}.csv"
APP_LOG   = LOG_DIR / f"ejecucion_{TIMESTAMP}.log"


# ─────────────────────────────────────────────
# LOGGING DE APLICACIÓN
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(APP_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# CONEXIÓN A BASE DE DATOS
# ─────────────────────────────────────────────

def get_connection():
    """Devuelve conexión a SQL Server con reintentos. Credenciales desde variables de entorno."""
    import time
    server   = os.environ.get("DB_SERVER",   "localhost")
    database = os.environ.get("DB_NAME",     "PruebaNomina")
    user     = os.environ.get("DB_USER",     "sa")
    password = os.environ.get("DB_PASSWORD", "")

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    for attempt in range(1, 6):
        try:
            return pyodbc.connect(conn_str, autocommit=False)
        except pyodbc.OperationalError as e:
            log.warning(f"Intento {attempt}/5 fallido: {e}. Reintentando en 10s...")
            time.sleep(10)
    return pyodbc.connect(conn_str, autocommit=False)  # último intento, propaga excepción


# ─────────────────────────────────────────────
# LECTURA DEL CSV
# ─────────────────────────────────────────────

def read_csv(filepath: str) -> pd.DataFrame:
    log.info(f"Leyendo archivo: {filepath}")
    df = pd.read_csv(filepath, dtype=str)
    df.columns = df.columns.str.strip().str.lower()
    log.info(f"Total de registros en CSV: {len(df)}")
    return df


# ─────────────────────────────────────────────
# VALIDACIÓN / REGLAS DE NEGOCIO
# ─────────────────────────────────────────────

def validate(df: pd.DataFrame):
    errores = []

    for idx, row in df.iterrows():
        motivos = []

        # Regla 1: documento no puede estar vacío
        doc = str(row.get("documento", "")).strip()
        if not doc or doc.lower() in ("nan", "none", ""):
            motivos.append("documento_empleado_vacio")
        else:
            if doc.endswith(".0"):
                doc = doc[:-2]
            df.at[idx, "documento"] = doc

        # Regla 2: cantidad_horas numérica y > 0
        horas_raw = str(row.get("cantidad_horas", "")).strip()
        if not horas_raw or horas_raw.lower() in ("nan", "none", ""):
            motivos.append("cantidad_horas_vacia")
        else:
            try:
                horas = float(horas_raw)
                if horas <= 0:
                    motivos.append(f"cantidad_horas_no_positiva ({horas_raw})")
            except (ValueError, TypeError):
                motivos.append(f"cantidad_horas_no_numerica ({horas_raw})")

        # Regla 3: tipo de hora extra válido
        tipo = str(row.get("tipo_he", "")).strip().upper()
        if not tipo or tipo.lower() in ("nan", "none", ""):
            motivos.append("tipo_hora_extra_vacio")
        elif tipo not in TIPOS_VALIDOS:
            motivos.append(f"tipo_hora_extra_invalido ({tipo})")

        if motivos:
            errores.append(idx)
            df.at[idx, "motivo_error"] = " | ".join(motivos)

    df_errores = df.loc[errores].copy()
    df_validos = df.drop(index=errores).drop(columns=["motivo_error"], errors="ignore")

    log.info(f"Registros validos  : {len(df_validos)}")
    log.info(f"Registros con error: {len(df_errores)}")
    return df_validos, df_errores


# ─────────────────────────────────────────────
# INSERCIÓN VÁLIDOS — TRANSACCIONAL
# ─────────────────────────────────────────────

INSERT_VALIDO = """
INSERT INTO Novedades_HorasExtras
    (DocumentoEmpleado, TipoHoraExtra, CantidadHoras, FechaReporte)
VALUES (?, ?, ?, ?)
"""

def insert_validos(df_validos, conn):
    if df_validos.empty:
        log.warning("Sin registros validos para insertar.")
        return 0

    cursor = conn.cursor()
    inserted = 0
    try:
        for _, row in df_validos.iterrows():
            cursor.execute(
                INSERT_VALIDO,
                str(row["documento"]).strip(),
                str(row["tipo_he"]).strip().upper(),
                float(row["cantidad_horas"]),
                str(row["fecha_reporte"]).strip(),
            )
            inserted += 1
        conn.commit()
        log.info(f"Transaccion exitosa: {inserted} registros insertados.")
    except Exception as exc:
        conn.rollback()
        log.error(f"Error en INSERT — ROLLBACK ejecutado: {exc}")
        raise
    finally:
        cursor.close()

    return inserted


# ─────────────────────────────────────────────
# INSERCIÓN ERRORES EN BD
# ─────────────────────────────────────────────

INSERT_ERROR = """
INSERT INTO Novedades_HorasExtras_Errores
    (DocumentoEmpleado, TipoHoraExtra, CantidadHoras, FechaReporte, MotivoError)
VALUES (?, ?, ?, ?, ?)
"""

def insert_errores_bd(df_errores, conn):
    if df_errores.empty:
        return
    cursor = conn.cursor()
    try:
        for _, row in df_errores.iterrows():
            cursor.execute(
                INSERT_ERROR,
                str(row.get("documento", "")).strip(),
                str(row.get("tipo_he", "")).strip(),
                str(row.get("cantidad_horas", "")).strip(),
                str(row.get("fecha_reporte", "")).strip(),
                str(row.get("motivo_error", "")).strip(),
            )
        conn.commit()
        log.info(f"{len(df_errores)} errores registrados en tabla BD.")
    except Exception as exc:
        conn.rollback()
        log.error(f"Error al insertar en tabla de errores: {exc}")
    finally:
        cursor.close()


# ─────────────────────────────────────────────
# REGISTRO DE ERRORES EN CSV
# ─────────────────────────────────────────────

def save_error_csv(df_errores):
    if df_errores.empty:
        log.info("Sin errores que registrar en CSV.")
        return
    df_errores.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
    log.info(f"Log de errores CSV guardado en: {LOG_FILE}")


# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────

def main(csv_path: str):
    log.info("=" * 60)
    log.info("Inicio del proceso de novedades de horas extras")
    log.info("=" * 60)

    df_raw = read_csv(csv_path)
    df_validos, df_errores = validate(df_raw)

    save_error_csv(df_errores)

    conn = get_connection()
    try:
        insert_validos(df_validos, conn)
        insert_errores_bd(df_errores, conn)
    finally:
        conn.close()

    log.info("=" * 60)
    log.info("Proceso finalizado.")
    log.info(f"  Insertados exitosamente : {len(df_validos)}")
    log.info(f"  Rechazados con error    : {len(df_errores)}")
    log.info("=" * 60)


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "novedades_extra.csv"
    main(csv_file)
