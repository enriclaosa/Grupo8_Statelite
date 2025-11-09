import serial
import matplotlib.pyplot as plt
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

device = 'COM3'
mySerial = serial.Serial(device, 9600, timeout=1)


# Variables globales para guardar datos
temperaturas = []
eje_x = []
i = 0
running = False

# Estado para controlar que tipo de valor introducir
accion_actual = None  # Puede ser "periodo" o "orientacion"

def Reanudar():    # Envia el mensaje para reanudar el envio
    mensaje = "Reanudar\n"
    mySerial.write(mensaje.encode('utf-8'))

def Parar():   # Envia el mensaje para detener el envio
    mensaje = "Parar\n"
    mySerial.write(mensaje.encode('utf-8'))

def update_plot():
    global i, running
    if running:
        while mySerial.in_waiting > 0:
            linea = mySerial.readline().decode('utf-8').rstrip()
            print(linea)
            temp = linea.split(" ")
            if len(temp) > 1:
                try:
                    temperatura = float(temp[1])
                    temperaturas.append(temperatura)
                    eje_x.append(i)
                    i += 1
                except ValueError:
                    # Si no se puede convertir, ignorar la línea
                    pass

        ax.clear()
        ax.set_xlim(0, max(100, i))
        ax.set_ylim(20, 30)  # Limites de temperatura
        ax.plot(eje_x, temperaturas, label='Temperatura')
        ax.set_title('Temperatura en tiempo real')
        ax.set_xlabel('Muestras')
        ax.set_ylabel('Temperatura (°C)')
        ax.legend()
        canvas.draw()
        # Llama a sí mismo después de 500 ms para actualizar la gráfica
        window.after(500, update_plot)

def Iniciarclick():
    global running, temperaturas, eje_x, i
    if not running:
        running = True
        temperaturas.clear()
        eje_x.clear()
        i = 0
        update_plot()

def Detenerclick():
    global running
    running = False

def BotonCambiarPeriodo():
    global accion_actual
    accion_actual = "periodo"
    MensajeVar.set("Escribe el nuevo periodo de transmision (segundos):")
    ValorEntry.delete(0, END)

def BotonCambiarOrientacion():
    global accion_actual
    accion_actual = "orientacion"
    MensajeVar.set("Escribe la nueva orientacion del sensor (grados):")
    ValorEntry.delete(0, END)

def EnviarValor():
    valor = ValorEntry.get()
    if accion_actual == "periodo":
        mensaje = f"1 {valor}\n"
        mySerial.write(mensaje.encode('utf-8'))
    elif accion_actual == "orientacion":
        mensaje = f"2 {valor}\n"
        mySerial.write(mensaje.encode('utf-8'))

    # Despues de enviar, vacia la barra y el mensaje
    MensajeVar.set("")
    ValorEntry.delete(0, END)

# INTERFAZ

window = Tk()
window.geometry("800x500")
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)
window.rowconfigure(3, weight=1)
window.rowconfigure(4, weight=1)
window.rowconfigure(5, weight=1)
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=10)

# Elementos de la interfaz

PararButton = Button(window, text="Detener envío datos", bg='red', fg="black", command=Parar)
PararButton.grid(row=0, column=0, padx=5, pady=5, sticky=N + S + E + W)

IniciarButton = Button(window, text="Iniciar gráfica temp", bg='green', fg="black", command=Iniciarclick)
IniciarButton.grid(row=1, column=0, padx=5, pady=5, sticky=N + S + E + W)

ReanudarButton = Button(window, text="Reanudar envío datos", bg='blue', fg="white", command=Reanudar)
ReanudarButton.grid(row=2, column=0, padx=5, pady=5, sticky=N + S + E + W)

CambiarPeriodoButton = Button(window, text="Cambiar periodo transmision", bg='orange', fg="black", command=BotonCambiarPeriodo)
CambiarPeriodoButton.grid(row=3, column=0, padx=5, pady=5, sticky=N+S+E+W)

CambiarOrientacionButton = Button(window, text="Cambiar orientacion sensor", bg='purple', fg="white", command=BotonCambiarOrientacion)
CambiarOrientacionButton.grid(row=4, column=0, padx=5, pady=5, sticky=N+S+E+W)

GraficaFrame = Frame(window)
GraficaFrame.grid(row=0, column=1, rowspan=5, padx=5, pady=5, sticky=N + S + E + W)

fig, ax = plt.subplots(figsize=(6,4))
canvas = FigureCanvasTkAgg(fig, master=GraficaFrame)
canvas.get_tk_widget().pack(fill=BOTH, expand=1)

# Barra valor y mensaje debajo de la grafica
MensajeVar = StringVar()
MensajeLabel = Label(window, textvariable=MensajeVar, anchor=W)
MensajeLabel.grid(row=5, column=1, padx=5, pady=2, sticky=N+S+E+W)

ValorEntry = Entry(window)
ValorEntry.grid(row=6, column=1, padx=5, pady=2, sticky=N+S+E+W)

EnviarButton = Button(window, text="Envia", bg="gray", command=EnviarValor)
EnviarButton.grid(row=7, column=1, padx=5, pady=2, sticky=N+S+E+W)

window.mainloop()
