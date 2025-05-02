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


# --- COMANDI FRECCE ---
VELOCITA = 500

def muovi(motore, velocita):
    invia_comando(0x01, 0x01, 0x00, motore, velocita)

def stop(motore):
    invia_comando(0x01, 0x03, 0x00, motore, 0)

def stop_tutti():
    stop(0)
    stop(1)

# --- INTERFACCIA GRAFICA ---
root = tk.Tk()
root.title("Controllo Motori - TMCM-351")
frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

# --- BOTTONI ---
def crea_bottone(direzione, riga, colonna, on_press, on_release):
    btn = tk.Label(frame, text=direzione, font=("Arial", 24), width=4, height=2, relief="raised", bg="lightgray")
    btn.grid(row=riga, column=colonna, padx=5, pady=5)
    btn.bind("<ButtonPress-1>", on_press)
    btn.bind("<ButtonRelease-1>", on_release)
    return btn

# --- CALLBACKS ---
def press_up(e):    muovi(1, -VELOCITA)
def release_up(e):  stop(1)

def press_down(e):  muovi(1, VELOCITA)
def release_down(e):stop(1)

def press_left(e):  muovi(0, VELOCITA)
def release_left(e):stop(0)

def press_right(e): muovi(0, -VELOCITA)
def release_right(e):stop(0)

# --- CREA I BOTTONI ---
crea_bottone("↑", 0, 1, press_up, release_up)
crea_bottone("←", 1, 0, press_left, release_left)
crea_bottone("→", 1, 2, press_right, release_right)
crea_bottone("↓", 2, 1, press_down, release_down)

# --- FINESTRA ---
root.protocol("WM_DELETE_WINDOW", lambda: (stop_tutti(), root.destroy()))
root.mainloop()
