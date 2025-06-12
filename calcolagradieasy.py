import math
import time
import struct
import serial
from datetime import datetime
from astral import Observer
from astral.sun import azimuth, elevation
from datetime import datetime
import pytz

# === CONFIGURAZIONE ===
LAT = 43.765833    # es. 43°45'57"N
LON = 11.220556    # es. 11°13'14"E
ELEVATION = 45     # metri

GEAR_RATIO = 1/8      # se usi riduttori mettilo qui (1 se diretto)
STEPS_PER_DEGREE = 6400 / 360   # steps per grado di rotazione

TARGET_AZIMUTH = 229    # direzione fissa verso il bersaglio (in gradi)
TARGET_DISTANCE = 10    # metri
TARGET_HEIGHT = -1.5    # m (rispetto allo specchio)

TIMEZONE = "Europe/Rome"  # fuso orario locale

# === SERIAL SETUP ===
ser = serial.Serial('COM3', 38400, timeout=1)  # cambia la porta se necessario

# === FUNZIONI ===
def calcola_checksum(pacchetto):
    return sum(pacchetto) & 0xFF

def invia_comando(indirizzo, comando, tipo, motore, valore=0):
    pacchetto = struct.pack('>BBBBi', indirizzo, comando, tipo, motore, valore)
    checksum = calcola_checksum(pacchetto)
    pacchetto += struct.pack('B', checksum)
    try:
        ser.write(pacchetto)
    except serial.SerialException as e:
        print(f"Errore nell'invio del comando {hex(comando)}:", e)
    time.sleep(0.005)

def get_sun_position():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)

    observer = Observer(latitude=LAT, longitude=LON, elevation=ELEVATION)
    az = azimuth(observer, now)
    el = elevation(observer, now)
    return az, el

def calcola_specchio(azimuth_sun, elevation_sun):
    # Calcolo dei vettori
    # Vettore Sole -> Specchio
    vec_sun = [
        math.cos(math.radians(elevation_sun)) * math.sin(math.radians(azimuth_sun)),
        math.cos(math.radians(elevation_sun)) * math.cos(math.radians(azimuth_sun)),
        math.sin(math.radians(elevation_sun))
    ]
    
    # Vettore Specchio -> Bersaglio
    dz = TARGET_HEIGHT
    dx = TARGET_DISTANCE
    az_tgt_rad = math.radians(TARGET_AZIMUTH)
    vec_target = [
        math.cos(az_tgt_rad),
        math.sin(az_tgt_rad),
        dz / math.sqrt(dx**2 + dz**2)
    ]
    
    # Normalizzazione dei vettori
    len_sun = math.sqrt(sum([c**2 for c in vec_sun]))
    vec_sun = [c / len_sun for c in vec_sun]
    
    len_target = math.sqrt(sum([c**2 for c in vec_target]))
    vec_target = [c / len_target for c in vec_target]
    
    # Calcolo normale specchio = bisettrice tra i due vettori
    normal = [
        (vec_sun[0] + vec_target[0]) / 2,
        (vec_sun[1] + vec_target[1]) / 2,
        (vec_sun[2] + vec_target[2]) / 2
    ]
    len_normal = math.sqrt(sum([c**2 for c in normal]))
    normal = [c / len_normal for c in normal]
    
    # Conversione in angoli (azimut, elevazione)
    azimuth_mirror = math.degrees(math.atan2(normal[0], normal[1])) % 360
    elevation_mirror = math.degrees(math.asin(normal[2]))
    
    return azimuth_mirror, elevation_mirror

def angoli_to_steps(angolo, steps_per_degree):
    return int(round(angolo * steps_per_degree * GEAR_RATIO))

# === MAIN LOOP ===
def main():
    # Configura microstep e corrente motori
    invia_comando(0x01, 0x05, 0x00, 140, 5)  # microstep motore 0
    invia_comando(0x01, 0x05, 0x00, 141, 5)  # microstep motore 1
    invia_comando(0x01, 0x05, 0x06, 0x00, 1050)  # corrente motore 0
    invia_comando(0x01, 0x05, 0x06, 0x01, 1050)  # corrente motore 1

    az_sun, el_sun = get_sun_position()
    print(f"Sole - Azimuth: {az_sun:.2f}°, Elevation: {el_sun:.2f}°")

    az_mirror, el_mirror = calcola_specchio(az_sun, el_sun)
    print(f"Specchio - Azimuth: {az_mirror:.2f}°, Elevation: {el_mirror:.2f}°")

    # Converti in step
    step_az = angoli_to_steps(az_mirror, STEPS_PER_DEGREE)
    step_el = angoli_to_steps(el_mirror, STEPS_PER_DEGREE)

    print(f"Invio comandi - Step AZ: {step_az}, Step EL: {step_el}")

    # Muovi motori
    invia_comando(0x01, 0x04, 0x01, 0x00, -step_az)
    invia_comando(0x01, 0x04, 0x01, 0x01, -step_el)

if __name__ == "__main__":
    main()
