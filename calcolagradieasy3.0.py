import math
import time
import struct
import serial
from datetime import datetime
from astral import Observer
from astral.sun import azimuth, elevation
import keyboard
import pytz

# === CONFIGURAZIONE ===
LAT = 43.765833
LON = 11.220556
ELEVATION = 45

GEAR_RATIO_AZ = 1 / 40   # esempio: azimut ha riduzione 1:8
GEAR_RATIO_EL = 1 / 24  # esempio: elevazione ha riduzione 1:30
STEPS_PER_DEGREE = 12800 / 360  # passi motore per grado senza riduzione


TARGET_AZIMUTH = 229
TARGET_DISTANCE = 10
TARGET_HEIGHT = -1.5

TIMEZONE = "Europe/Rome"

# === SERIAL SETUP ===
ser = serial.Serial('COM3', 38400, timeout=1)

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
    vec_sun = [
        math.cos(math.radians(elevation_sun)) * math.sin(math.radians(azimuth_sun)),
        math.cos(math.radians(elevation_sun)) * math.cos(math.radians(azimuth_sun)),
        math.sin(math.radians(elevation_sun))
    ]
    dz = TARGET_HEIGHT
    dx = TARGET_DISTANCE
    az_tgt_rad = math.radians(TARGET_AZIMUTH)
    vec_target = [
        math.cos(az_tgt_rad),
        math.sin(az_tgt_rad),
        dz / math.sqrt(dx**2 + dz**2)
    ]
    vec_sun = [c / math.sqrt(sum(v**2 for v in vec_sun)) for c in vec_sun]
    vec_target = [c / math.sqrt(sum(v**2 for v in vec_target)) for c in vec_target]
    normal = [(a + b) / 2 for a, b in zip(vec_sun, vec_target)]
    normal = [c / math.sqrt(sum(v**2 for v in normal)) for c in normal]
    azimuth_mirror = math.degrees(math.atan2(normal[0], normal[1])) % 360
    elevation_mirror = math.degrees(math.asin(normal[2]))
    return azimuth_mirror, elevation_mirror

def angoli_to_steps(angolo, tipo):
    if tipo == 'az':
        return int(round(angolo * STEPS_PER_DEGREE * GEAR_RATIO_AZ))
    elif tipo == 'el':
        return int(round(angolo * STEPS_PER_DEGREE * GEAR_RATIO_EL))
    else:
        raise ValueError("Tipo di motore non valido: usare 'az' o 'el'")


# === MAIN LOOP ===
def main_loop():
    # Setup iniziale motori (solo alla prima esecuzione)
    invia_comando(0x01, 0x05, 0x00, 140, 6)
    invia_comando(0x01, 0x05, 0x00, 141, 6)
    invia_comando(0x01, 0x05, 0x06, 0x00, 1050)
    invia_comando(0x01, 0x05, 0x06, 0x01, 1050)

    # Stato iniziale
    prima_volta = True
    step_az_prec = 0
    step_el_prec = 0

    n = 1
    intervallo_in_secondi = 60

    print(f"Lo script si avvierà e ripeterà ogni {intervallo_in_secondi} secondi.")
    print("Premi Ctrl+C o 'q' per fermarlo.")

    try:
        while True:
            az_sun, el_sun = get_sun_position()
            print(f"\nSole - Azimuth: {az_sun:.2f}°, Elevation: {el_sun:.2f}°")

            az_mirror, el_mirror = calcola_specchio(az_sun, el_sun)
            print(f"Specchio - Azimuth: {az_mirror:.2f}°, Elevation: {el_mirror:.2f}°")

            step_az = angoli_to_steps(az_mirror, 'az')
            step_el = angoli_to_steps(el_mirror, 'el')


            if prima_volta:
                # Solo registra la posizione
                print("Prima esecuzione: salvo la posizione iniziale.")
                prima_volta = False
            else:
                delta_az = step_az - step_az_prec
                delta_el = step_el - step_el_prec
                print(f"Correzione - ΔAZ: {delta_az} steps, ΔEL: {delta_el} steps")

                # Invia solo lo spostamento incrementale
                invia_comando(0x01, 0x04, 0x01, 0x00, -delta_az)
                invia_comando(0x01, 0x04, 0x01, 0x01, -delta_el)

            # Aggiorna stato precedente
            step_az_prec = step_az
            step_el_prec = step_el

            print(f"\nRipetizione n: {n}")
            n += 1

            for i in range(intervallo_in_secondi, 0, -1):
                print(f"Prossima esecuzione tra {i} secondi...", end="\r")
                time.sleep(1)
                if keyboard.is_pressed('q'):
                    print("\nTasto 'Q' premuto. Script interrotto.")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\nScript fermato.")

# === ESECUZIONE ===
if __name__ == "__main__":
    main_loop()
