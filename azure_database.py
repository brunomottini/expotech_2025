import pyodbc
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


# Settings
SERVER = os.environ.get("SQL_SERVER")
DATABASE = os.environ.get("SQL_DATABASE")
USERNAME = os.environ.get("SQL_USERNAME")
PASSWORD = os.environ.get("SQL_PASSWORD")

# Conexion
connectionString = f"Driver={{ODBC Driver 17 for SQL Server}};SERVER={SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"


# Función de conexión para manejar errores de conexión
def connect_db():
    try:
        return pyodbc.connect(connectionString)
    except pyodbc.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


def load_table_to_dataframe(table_name):
    """
    Carga los datos de una tabla desde la base de datos y los devuelve como un DataFrame de pandas.

    Args:
        table_name (str): El nombre de la tabla a consultar.

    Returns:
        pd.DataFrame | None: Un DataFrame con los datos de la tabla,
        o None si ocurre un error.
    """
    # Conectar a la base de datos
    conn = connect_db()
    if conn is None:
        print(
            "No se pudo establecer conexión con la base de datos para cargar la tabla."
        )
        return None

    try:
        cursor = conn.cursor()

        # Crear consulta SQL para seleccionar toda la tabla
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        # Debugging: verificar datos recuperados
        print("Rows:", rows)
        print("Columns:", columns)

        # Limpiar los datos para manejar valores vacíos
        cleaned_rows = [
            tuple(value if value != "" else None for value in row) for row in rows
        ]

        # Convertir las filas en un DataFrame de pandas
        df = pd.DataFrame(cleaned_rows, columns=columns)
        print("Datos cargados exitosamente desde la tabla.")

        return df

    except Exception as e:
        print(f"Error al cargar los datos de la tabla '{table_name}': {e}")
        return None

    finally:
        if conn:
            conn.close()
