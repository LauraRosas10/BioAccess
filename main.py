
import os
import time
import requests
from datetime import datetime
import subprocess

import dbmanager as db
import hardwaremanager as hw # Usaremos las funciones actualizadas de hw

# --- Configuración ---
IP_WEBCAM_URL = "http://10.14.58.230:8080/shot.jpg" # ¡¡¡CAMBIA ESTO!!!
PHOTOS_SAVE_DIR = db.PHOTOS_DIR_RELATIVE_TO_SCRIPT
TIEMPO_PUERTA_ABIERTA = 5 # Segundos que el servo permanecerá abierto

def mostrar_menu():
    print("\n--- Sistema de Asistencia por Consola ---")
    print("1. Verificar Acceso")
    print("2. Registrar Nuevo Usuario")
    print("3. Salir")
    while True:
        opcion = input("Seleccione una opción: ")
        if opcion in ['1', '2', '3']:
            return opcion
        else:
            print("Opción no válida. Intente de nuevo.")
            hw.lcd_mensaje("Opcion Invalida", "", delay_after=1.5, clear_first=True)


def verificar_acceso(): # Ya no necesita servo_pwm_instance como argumento
    print("\n--- Verificar Acceso ---")
    hw.lcd_mensaje("Ingrese clave:", "", clear_first=True)
    contrasena = input("Ingrese su contraseña: ")

    usuario = db.get_user_by_password(contrasena)

    if usuario:
        nombre = usuario['nombre']
        photo_path_relative = usuario['photo_path']
        photo_path_absolute = os.path.join(db.BASE_DIR, photo_path_relative)

        print(f"Acceso Concedido: {nombre}")
        hw.lcd_mensaje("Acceso OK:", nombre[:hw.LCD_COLS-10], clear_first=True) # Ajustar longitud

        if os.path.exists(photo_path_absolute):
            print(f"Mostrando foto: {photo_path_absolute}")
            try:
                proc = subprocess.Popen(['feh', '-F', '-Z', '--hide-pointer', photo_path_absolute])
                # No esperamos aquí, dejamos que el servo se mueva en paralelo
            except FileNotFoundError:
                print("Comando 'feh' no encontrado. Instálalo con 'sudo apt install feh'")
                hw.lcd_mensaje("Error: feh", "no instalado", delay_after=2)
            except Exception as e_img:
                print(f"Error al mostrar imagen con feh: {e_img}")
        else:
            print(f"Foto no encontrada en: {photo_path_absolute}")
            hw.lcd_mensaje("Foto no hallada", "", delay_after=2)

        # Mover servo
        hw.abrir_puerta_servo()
        
        # Esperar X segundos con la puerta abierta (y feh mostrando la foto)
        # Durante este tiempo, el usuario ve la foto y la puerta está abierta.
        print(f"Puerta abierta por {TIEMPO_PUERTA_ABIERTA} segundos...")
        start_time_abierto = time.time()
        mensaje_lcd_actual = 0
        mensajes_rotativos = [
            (f"Bienvenido", f"{nombre[:hw.LCD_COLS-0]}"),
            (f"Puerta Abierta", f"{TIEMPO_PUERTA_ABIERTA} seg...")
        ]
        
        while time.time() - start_time_abierto < TIEMPO_PUERTA_ABIERTA:
            # Mostrar mensajes rotativos en LCD
            l1, l2 = mensajes_rotativos[mensaje_lcd_actual % len(mensajes_rotativos)]
            hw.lcd_mensaje(l1, l2, clear_first=True) # Borra para cada mensaje nuevo
            mensaje_lcd_actual += 1
            time.sleep(1.5) # Tiempo entre cambios de mensaje en LCD

        # Cerrar feh si sigue abierto (feh -D <segundos> es otra opción)
        if 'proc' in locals() and proc.poll() is None: # Verificar si proc existe y sigue corriendo
            print("Cerrando visor de imágenes...")
            proc.terminate()
            proc.wait()
        
        hw.cerrar_puerta_servo()
        hw.lcd_mensaje("Puerta Cerrada", "", delay_after=1.5, clear_first=True)

    else:
        print("Acceso Denegado: Contraseña incorrecta.")
        hw.lcd_mensaje("Acceso Denegado", "Clave Erronea", delay_after=2, clear_first=True)
    
    hw.lcd_clear()


def registrar_usuario():
    print("\n--- Registrar Nuevo Usuario ---")
    hw.lcd_mensaje("Nuevo Registro", "Ingrese datos", clear_first=True)
    
    nombre = input("Ingrese el nombre del nuevo usuario: ")
    hw.lcd_mensaje("Nombre:", nombre[:hw.LCD_COLS-8], clear_first=True) # Ajustar longitud
    
    contrasena = input(f"Ingrese la contraseña para {nombre}: ")
    hw.lcd_mensaje(f"Clave p/ {nombre[:(hw.LCD_COLS-10)//2]}:", contrasena[:hw.LCD_COLS], clear_first=True) # Ajustar

    input(f"Asegúrate que IP Webcam esté activa en {IP_WEBCAM_URL}. Presiona Enter para tomar foto...")
    hw.lcd_mensaje("Tomando foto...", "Espere por favor", clear_first=True)

    try:
        response = requests.get(IP_WEBCAM_URL, timeout=15)
        response.raise_for_status()

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_nombre_archivo = "".join(c if c.isalnum() else "_" for c in nombre.split(' ')[0]) # Solo primer nombre
        photo_filename = f"{safe_nombre_archivo}_{timestamp_str}.jpg"
        
        photo_path_relative_to_main = os.path.join(PHOTOS_SAVE_DIR, photo_filename)
        photo_path_absolute_to_save = os.path.join(db.BASE_DIR, photo_path_relative_to_main)

        with open(photo_path_absolute_to_save, 'wb') as f:
            f.write(response.content)
        print(f"Foto guardada en: {photo_path_absolute_to_save}")
        hw.lcd_mensaje("Foto Guardada!", "", delay_after=1.5, clear_first=True)

        user_id = db.add_user(nombre, contrasena, photo_path_relative_to_main)
        if user_id:
            print(f"Usuario '{nombre}' registrado exitosamente.")
            hw.lcd_mensaje("Usuario", f"{nombre[:(hw.LCD_COLS-10)//2]} RegOK", delay_after=2, clear_first=True)
        else:
            print("Fallo al registrar el usuario en la base de datos.")
            hw.lcd_mensaje("Error al", "Registrar DB", delay_after=2, clear_first=True)
            if os.path.exists(photo_path_absolute_to_save):
                try: os.remove(photo_path_absolute_to_save); print("Foto temporal borrada.")
                except: pass
    except Exception as e:
        error_msg_short = str(e)[:hw.LCD_COLS*2-10] # Limitar para dos líneas
        hw.lcd_mensaje("Error Registro:", error_msg_short[:hw.LCD_COLS], delay_after=0)
        if len(error_msg_short) > hw.LCD_COLS:
             hw.lcd_mensaje(error_msg_short[:hw.LCD_COLS], error_msg_short[hw.LCD_COLS:], delay_after=2.5, clear_first=False)
        else:
            time.sleep(2.5)
        print(f"Error durante el registro: {e}")
    
    hw.lcd_clear()


def main():
    db.init_db()
    if not hw.setup_servo(): # Configura el servo y lo pone en cerrado
        print("Error crítico: No se pudo configurar el servo. Saliendo.")
        hw.lcd_mensaje("Error Servo", "Saliendo...", delay_after=3, clear_first=True)
        return # Salir si el servo no se puede inicializar

    if not hw.LCD_AVAILABLE: # Chequeo adicional si la LCD falló en su init
        print("Advertencia: LCD no está funcionando. La aplicación continuará con salida por consola.")
        # No es necesario salir, hw.lcd_mensaje ya tiene un fallback a print

    hw.lcd_mensaje("Sistema Listo", "Elija opcion", delay_after=2, clear_first=True)
    hw.lcd_clear()

    try:
        while True:
            opcion = mostrar_menu()
            if opcion == '1':
                verificar_acceso()
            elif opcion == '2':
                registrar_usuario()
            elif opcion == '3':
                print("Saliendo del sistema...")
                hw.lcd_mensaje("Adios! :)", "", delay_after=2, clear_first=True)
                break
            
            print("\nOperación completada.")
            hw.lcd_mensaje("Operacion OK", "Elija de nuevo", delay_after=2, clear_first=True)
            hw.lcd_clear()
            # input("\nPresiona Enter para continuar...") # Opcional, si quieres pausa explícita
            
    finally:
        hw.cleanup_gpio() # Detiene PWM, limpia GPIO
        hw.lcd_clear()
        print("Recursos liberados. Programa finalizado.")

if __name__ == "__main__":
    main()

