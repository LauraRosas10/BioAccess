# /home/pi/proyecto_asistencia_consola/db_manager_consola.py
import sqlite3
import os
from datetime import datetime

# --- Definición de Rutas ---
# BASE_DIR es el directorio donde se encuentra este script (db_manager_consola.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH es la ruta completa al archivo de la base de datos.
DB_PATH = os.path.join(BASE_DIR, 'asistencia_consola.db')
# PHOTOS_DIR_RELATIVE_TO_SCRIPT es el nombre de la carpeta de fotos,
# que se espera esté al mismo nivel que el script principal (main_consola.py).
# Esta ruta se almacena en la base de datos.
PHOTOS_DIR_RELATIVE_TO_SCRIPT = 'static_photos'
# PHOTOS_DIR_ABSOLUTE es la ruta absoluta a la carpeta de fotos, usada para crearla.
PHOTOS_DIR_ABSOLUTE = os.path.join(BASE_DIR, PHOTOS_DIR_RELATIVE_TO_SCRIPT)


def get_db_connection():
    """Establece y devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    # conn.row_factory = sqlite3.Row permite acceder a las columnas por nombre
    # (ej. fila['nombre']) en lugar de solo por índice (ej. fila[0]).
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa la base de datos.
    Crea la carpeta de fotos si no existe.
    Crea la tabla 'usuarios' si no existe.
    """
    # Crear el directorio para las fotos si aún no existe.
    if not os.path.exists(PHOTOS_DIR_ABSOLUTE):
        os.makedirs(PHOTOS_DIR_ABSOLUTE)
        print(f"Directorio de fotos creado: {PHOTOS_DIR_ABSOLUTE}")

    conn = get_db_connection()
    cursor = conn.cursor()
    # Crear la tabla 'usuarios'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            contrasena TEXT NOT NULL UNIQUE, -- La contraseña es ÚNICA para buscar por ella.
            photo_path TEXT NOT NULL UNIQUE, -- La ruta a la foto de perfil también es ÚNICA.
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # El constraint UNIQUE en 'contrasena' significa que no puede haber dos usuarios
    # con la misma contraseña. Esto simplifica la búsqueda en `get_user_by_password`.
    # Si quisieras permitir contraseñas duplicadas, deberías quitar UNIQUE de 'contrasena'
    # y la lógica de `get_user_by_password` tendría que manejar múltiples resultados.

    conn.commit() # Guardar los cambios (creación de la tabla)
    conn.close()  # Cerrar la conexión
    print(f"Base de datos '{DB_PATH}' inicializada/verificada.")

def add_user(nombre, contrasena, photo_path_relative_to_script_dir):
    """
    Añade un nuevo usuario a la base de datos.
    'photo_path_relative_to_script_dir' debe ser la ruta relativa
    desde donde se ejecuta main_consola.py (ej: 'static_photos/imagen.jpg').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (nombre, contrasena, photo_path) VALUES (?, ?, ?)",
            (nombre, contrasena, photo_path_relative_to_script_dir)
        )
        conn.commit()
        print(f"Usuario '{nombre}' añadido con foto '{photo_path_relative_to_script_dir}'.")
        return cursor.lastrowid # Devuelve el ID del usuario recién insertado
    except sqlite3.IntegrityError as e:
        # Manejar errores si se viola una restricción UNIQUE (contraseña o ruta de foto)
        if "UNIQUE constraint failed: usuarios.contrasena" in str(e):
            print(f"Error: La contraseña '{contrasena}' ya está en uso.")
        elif "UNIQUE constraint failed: usuarios.photo_path" in str(e):
            print(f"Error: La ruta de la foto '{photo_path_relative_to_script_dir}' ya está en uso.")
        else:
            print(f"Error de integridad al añadir usuario: {e}")
        return None # Indicar que la inserción falló
    except Exception as e:
        print(f"Error general al añadir usuario: {e}")
        return None
    finally:
        conn.close()

def get_user_by_password(contrasena_ingresada):
    """
    Busca un usuario por su contraseña.
    Como la contraseña tiene una restricción UNIQUE, esto devolverá
    como máximo un usuario (o None si no se encuentra).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, photo_path, fecha_registro FROM usuarios WHERE contrasena = ?", (contrasena_ingresada,))
    user_data = cursor.fetchone() # fetchone() obtiene la primera fila o None si no hay resultados
    conn.close()
    return user_data # Devuelve el objeto Row de SQLite (similar a un diccionario) o None

# Esta sección se ejecuta solo si corres `python3 db_manager_consola.py` directamente.
# Es útil para crear la base de datos y la tabla la primera vez sin correr todo el programa.
if __name__ == '__main__':
    print("Inicializando la base de datos directamente desde db_manager_consola.py...")
    init_db()
    print("Base de datos lista.")
