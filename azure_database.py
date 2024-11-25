import pyodbc

SERVER = "visnaidatabase.database.windows.net"
DATABASE = "visnaidemodatabase"
USERNAME = "visnaidatabase"
PASSWORD = "Visnai2024"


# Conexion
connectionString = f"Driver={{ODBC Driver 17 for SQL Server}};SERVER={SERVER},1433;DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"


# Función de conexión para manejar errores de conexión
def connect_db():
    try:
        return pyodbc.connect(connectionString)
    except pyodbc.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


# Crear tabla QUIERO_ME_CONTACTEN
def create_table_expo25_contacto_persona():
    try:
        with connect_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE expo25_contacto_persona (
                        id_contacto INT IDENTITY(1,1) PRIMARY KEY,      -- Identificador único del contacto
                        fecha_registro DATETIME DEFAULT GETDATE(),      -- Fecha de registro, valor por defecto la fecha actual
                        nombre_contacto NVARCHAR(100) NOT NULL,         -- Nombre de la persona a contactar
                        nombre_empresa NVARCHAR(100) NULL,             -- Nombre de la empresa (opcional)
                        mail_contacto NVARCHAR(150) NOT NULL,           -- Correo electrónico de contacto
                        numero_contacto NVARCHAR(15) NOT NULL,          -- Número de teléfono de contacto                        
                        motivo_contacto NVARCHAR(MAX) NOT NULL          -- Descripción del motivo de contacto
                    )
                    """
                )
                conn.commit()
                print("Tabla 'expo25_contacto_persona' creada exitosamente.")
    except pyodbc.Error as e:
        print(f"Error al crear la tabla 'expo25_contacto_persona': {e}")


# # Crear todas las tablas
# create_table_expo25_contacto_persona()
