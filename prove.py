def invia_comando(indirizzo, comando, tipo, motore, valore=0):
    pacchetto = struct.pack('>BBBBi', indirizzo, comando, tipo, motore, valore)
    checksum = calcola_checksum(pacchetto)
    pacchetto += struct.pack('B', checksum)
    try:
        ser.write(pacchetto)
    except serial.SerialException as e:
        print(f"Errore nell'invio del comando {hex(comando)}:", e)
    time.sleep(0.005)

#Set corrente iniziale usando SAP
invia_comando(0x01, 0x05, 0x06, 0x00, 1050)
invia_comando(0x01, 0x05, 0x06, 0x01, 1050)

#muovi motori usando MVP
invia_comando(0x01, 0x04, 0x01, 0x00, step_az)
invia_comando(0x01, 0x04, 0x01, 0x01, step_el) 

#leggi posizione motori usando GAP
invia_comando(0x01, 0x06, 0x01, 0x00, value)
invia_comando(0x01, 0x06, 0x01, 0x01, value) 

#scrivi posizione motori usando SAP
invia_comando(0x01, 0x05, 0x01, 0x00, value)
invia_comando(0x01, 0x05, 0x01, 0x01, value)