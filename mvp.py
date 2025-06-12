import tkinter as tk
import serial
import struct
import time

# --- CONFIGURAZIONE SERIALE ---
porta_seriale = 'COM3'
baudrate = 38400
timeout = 1

try:
    ser = serial.Serial(porta_seriale, baudrate, timeout=timeout)
    time.sleep(0.5)
    print("Connessione seriale stabilita.")
except serial.SerialException as e:
    print("Errore nella connessione seriale:", e)
    exit()

# --- FUNZIONI ---
def calcola_checksum(data):
    return sum(data) & 0xFF

def invia_comando(indirizzo, comando, tipo, motore, valore=0):
    pacchetto = struct.pack('>BBBBi', indirizzo, comando, tipo, motore, valore)
    checksum = calcola_checksum(pacchetto)
    pacchetto += struct.pack('B', checksum)
    try:
        ser.write(pacchetto)
    except serial.SerialException as e:
        print(f"Errore nell'invio del comando {hex(comando)}:", e)
    time.sleep(0.005)

invia_comando(indirizzo=0x01, comando=0x05, tipo=0x06, motore=0x00, valore=1050)        #corrente motori
invia_comando(indirizzo=0x01, comando=0x05, tipo=0x06, motore=0x01, valore=1050)
# Parametri motori microstep
invia_comando(0x01, 0x05, 140, 0x00, 6)
invia_comando(0x01, 0x05, 140, 0x01, 6)

time.sleep(0.1)


invia_comando(0x01, 0x04, 0x01, 0x01, -1*12800)


