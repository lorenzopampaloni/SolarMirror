import tkinter as tk
import serial
import struct
import time
import math

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

# --- FUNZIONI COMUNICAZIONE ---
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

def muovi(motore, velocita):
    invia_comando(0x01, 0x01, 0x00, motore, int(velocita))

def stop(motore):
    invia_comando(0x01, 0x03, 0x00, motore, 0)

def stop_tutti():
    stop(0)
    stop(1)

# Corrente iniziale motori
invia_comando(indirizzo=0x01, comando=0x05, tipo=0x06, motore=0x00, valore=1050)
invia_comando(indirizzo=0x01, comando=0x05, tipo=0x06, motore=0x01, valore=1050)

# --- INTERFACCIA GRAFICA ---
root = tk.Tk()
root.title("Joystick Motori - TMCM-351")

canvas_size = 300
joystick_radius = 120
knob_radius = 20

VELOCITA_MAX = 500  # Impostazione iniziale
VELOCITA = tk.IntVar(value=VELOCITA_MAX)

canvas = tk.Canvas(root, width=canvas_size, height=canvas_size, bg="white")
canvas.pack(pady=10)

center_x = center_y = canvas_size // 2
knob = canvas.create_oval(center_x - knob_radius, center_y - knob_radius,
                          center_x + knob_radius, center_y + knob_radius,
                          fill="gray")

# Disegna il cerchio di riferimento
canvas.create_oval(center_x - joystick_radius, center_y - joystick_radius,
                   center_x + joystick_radius, center_y + joystick_radius,
                   outline="black")

# --- JOYSTICK HANDLER ---
def aggiorna_velocita(x, y):
    dx = x - center_x
    dy = y - center_y
    distanza = math.hypot(dx, dy)
    
    if distanza > joystick_radius:
        angolo = math.atan2(dy, dx)
        dx = joystick_radius * math.cos(angolo)
        dy = joystick_radius * math.sin(angolo)
        x = center_x + dx
        y = center_y + dy

    canvas.coords(knob, x - knob_radius, y - knob_radius, x + knob_radius, y + knob_radius)

    # Normalizzazione
    norm_x = dx / joystick_radius
    norm_y = dy / joystick_radius

    # Mappa alla velocità
    vel_x = VELOCITA.get() * norm_x
    vel_y = VELOCITA.get() * norm_y

    muovi(0, -vel_x)  # motore X
    muovi(1, vel_y)   # motore Y

def reset_joystick(e=None):
    canvas.coords(knob, center_x - knob_radius, center_y - knob_radius,
                  center_x + knob_radius, center_y + knob_radius)
    stop_tutti()

def mouse_drag(event):
    aggiorna_velocita(event.x, event.y)

canvas.bind("<B1-Motion>", mouse_drag)
canvas.bind("<ButtonRelease-1>", reset_joystick)

# --- SLIDER VELOCITÀ ---
tk.Label(root, text="Velocità massima", font=("Arial", 12)).pack()
tk.Scale(root, from_=100, to=1000, variable=VELOCITA, orient="horizontal", length=250).pack()

# --- CHIUSURA SICURA ---
root.protocol("WM_DELETE_WINDOW", lambda: (stop_tutti(), root.destroy()))
root.mainloop()
