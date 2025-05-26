# /home/pi/proyecto_asistencia_consola/hardware_manager.py
import time

# --- Configuración de Hardware (AJUSTA SEGÚN TU SETUP) ---
SERVO_PIN = 18          # Pin GPIO (BCM) donde está conectado el servo
LCD_I2C_ADDRESS = 0x27  # Dirección I2C de tu LCD (común para 16x2, verifica con `i2cdetect -y 1`)
LCD_COLS = 16
LCD_ROWS = 2

# --- Ciclos de Trabajo para el Servo (AJUSTA PARA TU SERVO ESPECÍFICO) ---
# Estos valores son típicos para un SG90 a 50Hz. ¡CALIBRA LOS TUYOS!
DUTY_CYCLE_CERRADO = 2.5  # Para 0 grados
DUTY_CYCLE_ABIERTO = 7.5  # Para 90 grados (o la posición de "abierto" que desees)

# --- Importaciones de Librerías de Hardware ---
try:
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False) # Desactivar advertencias comunes de GPIO si reutilizas pines
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("ADVERTENCIA: Librería RPi.GPIO no encontrada. Servo y posiblemente LCD no funcionarán.")

try:
    from RPLCD.i2c import CharLCD
    # Asegúrate de que el 'expander' sea el correcto para tu módulo I2C LCD
    # PCF8574 es común. También podría ser MCP23008, etc.
    # El puerto es 1 para la mayoría de las Raspberry Pi modernas.
    lcd = CharLCD(i2c_expander='PCF8574', address=LCD_I2C_ADDRESS, port=1,
                  cols=LCD_COLS, rows=LCD_ROWS, dotsize=8,
                  charmap='A02', auto_linebreaks=True)
    LCD_AVAILABLE = True
    print("LCD conectada y configurada con RPLCD.")
except ImportError:
    LCD_AVAILABLE = False
    print("ADVERTENCIA: Librería RPLCD.i2c no encontrada. LCD no funcionará.")
    lcd = None
except Exception as e_lcd_init: # Captura otros errores de inicialización de LCD
    LCD_AVAILABLE = False
    print(f"ADVERTENCIA: Error al inicializar LCD: {e_lcd_init}. LCD no funcionará.")
    lcd = None


# --- Variables Globales para Hardware ---
servo_pwm_global = None

# --- Funciones del Servo ---
def setup_servo():
    global servo_pwm_global
    if not GPIO_AVAILABLE:
        print("GPIO no disponible, no se puede configurar el servo.")
        return False
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        servo_pwm_global = GPIO.PWM(SERVO_PIN, 50) # 50Hz
        servo_pwm_global.start(0) # Iniciar con ciclo de trabajo 0 (inactivo)
        # Mover a la posición inicial (cerrado) para asegurar
        time.sleep(0.5) # Pequeña pausa antes de mover
        servo_pwm_global.ChangeDutyCycle(DUTY_CYCLE_CERRADO)
        time.sleep(1)
        servo_pwm_global.ChangeDutyCycle(0) # Detener pulso para evitar jitter
        print("Servo configurado y en posición cerrada.")
        return True
    except Exception as e_servo_setup:
        print(f"Error al configurar servo: {e_servo_setup}")
        servo_pwm_global = None # Asegurar que es None si falla
        return False


def mover_servo_a_posicion(duty_cycle):
    """Mueve el servo al ciclo de trabajo especificado."""
    if not servo_pwm_global or not GPIO_AVAILABLE:
        print(f"[SERVO_SIM] Moviendo a duty cycle: {duty_cycle}%")
        return
    
    print(f"Moviendo servo a duty cycle: {duty_cycle:.2f}%")
    # GPIO.output(SERVO_PIN, True) # No necesario si el PWM ya está corriendo
    servo_pwm_global.ChangeDutyCycle(duty_cycle)
    time.sleep(1) # Tiempo para que el servo complete el movimiento
    servo_pwm_global.ChangeDutyCycle(0) # Detener la señal para evitar jitter y consumo


def abrir_puerta_servo():
    print("Abriendo puerta (servo)...")
    mover_servo_a_posicion(DUTY_CYCLE_ABIERTO)

def cerrar_puerta_servo():
    print("Cerrando puerta (servo)...")
    mover_servo_a_posicion(DUTY_CYCLE_CERRADO)


def cleanup_gpio():
    global servo_pwm_global
    if GPIO_AVAILABLE:
        if servo_pwm_global:
            servo_pwm_global.stop()
            print("PWM del servo detenido.")
        GPIO.cleanup()
        print("GPIO limpiado.")

# --- Funciones de la LCD ---
def lcd_mensaje(linea1="", linea2="", clear_first=True, delay_after=0):
    if not lcd or not LCD_AVAILABLE:
        print(f"[LCD_SIM] L1: {linea1}") # Mensaje simulado si LCD no está
        print(f"[LCD_SIM] L2: {linea2}")
        if delay_after > 0:
            time.sleep(delay_after)
        return
    
    try:
        if clear_first:
            lcd.clear()
        
        lcd.cursor_pos = (0, 0)
        lcd.write_string(linea1[:LCD_COLS]) # Limitar a las columnas de la LCD
        
        if linea2:
            lcd.cursor_pos = (1, 0)
            lcd.write_string(linea2[:LCD_COLS])
        
        if delay_after > 0:
            time.sleep(delay_after)

    except Exception as e_lcd:
        print(f"Error al escribir en LCD: {e_lcd}")
        # Podrías intentar reinicializar la LCD aquí si es un error común

def lcd_clear():
    if lcd and LCD_AVAILABLE:
        try:
            lcd.clear()
        except Exception as e_lcd_clear:
            print(f"Error al limpiar LCD: {e_lcd_clear}")
    else:
        print("[LCD_SIM] Pantalla borrada (simulado).")


if __name__ == '__main__':
    print("Probando hardware_manager con código funcional esperado...")
    
    # Prueba de LCD
    if LCD_AVAILABLE:
        lcd_mensaje("Probando LCD...", "Linea 2 de prueba", delay_after=2)
        lcd_clear()
        lcd_mensaje("LCD OK!", "", delay_after=1)
    else:
        print("LCD no disponible para prueba.")

    # Prueba de Servo
    if setup_servo(): # Esto también inicializa servo_pwm_global
        try:
            print("Probando servo: Abriendo")
            abrir_puerta_servo()
            time.sleep(1) # Mantener abierto
            
            print("Probando servo: Cerrando")
            cerrar_puerta_servo()
            time.sleep(1)
        finally:
            cleanup_gpio() # Esto detendrá el PWM y limpiará GPIO
    else:
        print("Servo no disponible o error en setup para prueba.")
    
    print("Prueba de hardware_manager finalizada.")