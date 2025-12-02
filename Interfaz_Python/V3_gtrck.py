import serial
import matplotlib.pyplot as plt
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import datetime
from tkinter.scrolledtext import ScrolledText
import matplotlib
import threading

# CONFIG SERIAL

device = 'COM8'
mySerial = serial.Serial(device, 9600, timeout=1)


# VARIABLES GLOBALES

temperaturas = []
medias = []
eje_x = []
i = 0
running = False
limite_alarma = 25.0
accion_actual = None
media_en_arduino = False

angulos = []
distancias = []

DateTime = datetime.datetime.now()
fecha_hora_actual = DateTime.strftime("%d-%m-%Y %H:%M")


# VARIABLES GROUNDTRACK

matplotlib.use('TkAgg')
x_vals = []
y_vals = []
R_EARTH = 6371000

plt.ion()
fig_gt, ax_gt = plt.subplots()
orbit_plot, = ax_gt.plot([], [], 'bo-', label='Satellite Orbit', markersize=2)
last_point_plot = ax_gt.scatter([], [], color='red', s=50, label='Last Point')

earth_circle = plt.Circle((0, 0), R_EARTH, color='orange', fill=False)
ax_gt.add_artist(earth_circle)

ax_gt.set_xlim(-7e6, 7e6)
ax_gt.set_ylim(-7e6, 7e6)
ax_gt.set_aspect('equal', 'box')
ax_gt.grid(True)
ax_gt.set_title("Satellite Orbit (North view)")

def draw_earth_slice(z):
    slice_radius = (R_EARTH**2 - z**2)**0.5 if abs(z) <= R_EARTH else 0
    return plt.Circle((0, 0), slice_radius, color='orange', fill=False, linestyle='--')

earth_slice = draw_earth_slice(0)
ax_gt.add_artist(earth_slice)


# FUNCIONES PRINCIPALES

def Iniciarclick():
    global running, temperaturas, eje_x, i
    if not running:
        running = True
        temperaturas.clear()
        medias.clear()
        eje_x.clear()
        i = 0
        update_plot()
    RegistrarEvento("Comando:", "iniciar graficas")

def Parar():
    mensaje = "Parar"
    mySerial.write(mensaje.encode('utf-8'))
    RegistrarEvento("Comando:", "parar transmision")

def Reanudar():
    mensaje = "Reanudar"
    mySerial.write(mensaje.encode('utf-8'))
    RegistrarEvento("Comando:", "reanudar transmision")

def CambiarPeriodo():
    global accion_actual
    accion_actual = "periodo"
    MensajeVar.set("Escribe el nuevo periodo:")
    ValorEntry.delete(0, END)
    RegistrarEvento("Comando:", "cambiar periodo")

def CambiarValorMaxTemp():
    global accion_actual
    accion_actual = "ValorTempMax"
    MensajeVar.set("Escribe el valor máximo:")
    ValorEntry.delete(0, END)
    RegistrarEvento("Comando:", "cambiar valor max temp")

def CambiarOrientacion():
    global accion_actual
    accion_actual = "orientacion"
    MensajeVar.set("Escribe la nueva orientacion:")
    ValorEntry.delete(0, END)
    RegistrarEvento("Comando:", "cambiar orientacion")

def CambiarModoControl():
    mensaje = "Cambio"
    mySerial.write(mensaje.encode('utf-8'))

def EscribirObservacion():
    global accion_actual
    accion_actual = "observacion"
    MensajeVar.set("Escribe la observacion:")
    ValorEntry.delete(0, END)

def CambiarMedia():
    global media_en_arduino
    media_en_arduino = not media_en_arduino
    estado = "Arduino" if media_en_arduino else "Python"
    RegistrarEvento("Comando:", f"Media en {estado}")
    mySerial.write(("MEDIA_ON\n" if media_en_arduino else "MEDIA_OFF\n").encode('utf-8'))

def EnviarValor():
    valor = ValorEntry.get()
    global limite_alarma

    if accion_actual == "periodo":
        mySerial.write(f"4 {valor}\n".encode('utf-8'))

    elif accion_actual == "orientacion":
        try:
            val = int(valor)
            if val == -1 or (0 <= val <= 180):
                mySerial.write(f"2 {val}\n".encode('utf-8'))
        except:
            MensajeVar.set("Número inválido")

    elif accion_actual == "ValorTempMax":
        try:
            limite_alarma = float(valor)
        except:
            MensajeVar.set("Número inválido")

    elif accion_actual == "observacion":
        RegistrarEvento("Observacion:", valor)

    MensajeVar.set("")
    ValorEntry.delete(0, END)

def RegistrarEvento(tipo, mensaje):
    with open("registro_eventos.txt", "a", encoding="utf-8") as f:
        f.write(f"{fecha_hora_actual} {tipo} {mensaje}\n")


# MOSTRAR REGISTRO

def MostrarRegistro():
    def aplicar_filtros():
        fecha_filtro = entry_data.get().strip()
        tipo_filtro = tipo_var.get()
        resultado = []
        try:
            with open("registro_eventos.txt", "r", encoding="utf-8") as f:
                lineas = f.readlines()
        except:
            text_area.insert("1.0", "No existe el fichero.")
            return

        for linea in lineas:
            if fecha_filtro and not linea.startswith(fecha_filtro):
                continue
            if tipo_filtro != "Cualquiera" and f"{tipo_filtro}:" not in linea:
                continue
            resultado.append(linea)

        text_area.config(state="normal")
        text_area.delete("1.0", END)
        text_area.insert("1.0", "".join(resultado) if resultado else "No hay resultados")
        text_area.config(state="disabled")

    vent = Toplevel(window)
    vent.title("Registro")
    frame = Frame(vent)
    frame.pack()

    Label(frame, text="Fecha (dd-mm-yyyy):").grid(row=0, column=0)
    entry_data = Entry(frame)
    entry_data.grid(row=0, column=1)

    Label(frame, text="Tipo:").grid(row=0, column=2)
    tipo_var = StringVar(value="Cualquiera")
    OptionMenu(frame, tipo_var, "Cualquiera", "Comando", "Alarma", "Observacion").grid(row=0, column=3)

    Button(frame, text="Filtrar", command=aplicar_filtros).grid(row=0, column=4)

    text_area = ScrolledText(vent, width=100, height=30)
    text_area.pack()


# UPDATE PLOT

def update_plot():
    global i, running, earth_slice

    if running:
        while mySerial.in_waiting > 0:
            linea = mySerial.readline().decode().strip()
            if not linea:
                continue
            temp = linea.split(" ")
            try:
                codigo = int(temp[0])
            except:
                continue

            # ---- TEMPERATURA ----
            if codigo == 1 and len(temp) >= 3:
                try:
                    temperatura = float(temp[2])
                    temperaturas.append(temperatura)
                    eje_x.append(i)
                    i += 1

                    if not media_en_arduino:
                        ult = temperaturas[-10:]
                        medias.append(sum(ult)/len(ult))

                        if len(medias) >= 3 and all(m > limite_alarma for m in medias[-3:]):
                            RegistrarEvento("Alarma:", "3 medias consecutivas > limite")

                except:
                    pass

            # ---- RADAR ----
            elif codigo == 2 and len(temp) >= 3:
                try:
                    angulos.append(float(temp[1]))
                    distancias.append(float(temp[2]))
                except:
                    pass

            # ---- GROUNDTRACK ----
            elif codigo == 4 and len(temp) >= 4:
                try:
                    x = float(temp[1])
                    y = float(temp[2])
                    z = float(temp[3])

                    x_vals.append(x)
                    y_vals.append(y)

                    orbit_plot.set_data(x_vals, y_vals)
                    last_point_plot.set_offsets([[x, y]])

                    earth_slice.remove()
                    earth_slice = draw_earth_slice(z)
                    ax_gt.add_artist(earth_slice)

                    plt.draw()
                    fig_gt.canvas.flush_events()

                except:
                    pass

        angulos[:] = angulos[-5:]
        distancias[:] = distancias[-5:]

        ax_temp.clear()
        ax_temp.set_xlim(0, max(100, i))
        ax_temp.set_ylim(15, 25)
        ax_temp.plot(eje_x, temperaturas, label='Temperatura')
        ax_temp.plot(eje_x, medias, label='Media últimos 10', color='orange')
        ax_temp.set_title('Temperatura y media en tiempo real')
        ax_temp.set_xlabel('Muestras')
        ax_temp.set_ylabel('Temperatura (°C)')
        ax_temp.legend()
        canvas_temp.draw()

        ax_radar.clear()
        ax_radar.set_title('Radar de Ultrasonidos')
        ax_radar.set_thetamin(0)
        ax_radar.set_thetamax(180)
        ax_radar.set_xlabel('Distancia (cm)', labelpad=-50)
        ax_radar.set_ylabel('Orientación sensor (grados)', labelpad=25)
        ax_radar.set_ylim(0, 100)
        ax_radar.set_xticks(np.deg2rad(np.arange(0, 181, 20)))
        ax_radar.set_xticklabels([f"{int(x)}°" for x in np.arange(0, 181, 20)])
        if len(angulos) > 1:
            radianes = np.deg2rad(np.array(angulos))
            ax_radar.plot(radianes, distancias, color="yellow") 
            ax_radar.plot([radianes[-1]], [distancias[-1]], "go", markersize=10)
            ax_radar.plot([0, radianes[-1]], [0, distancias[-1]], "g")
        canvas_radar.draw()

        window.after(500, update_plot)


# INTERFAZ

window = Tk()
window.geometry("1400x800")
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)
window.rowconfigure(3, weight=1)
window.rowconfigure(4, weight=1)
window.rowconfigure(5, weight=1)
window.rowconfigure(6, weight=1)
window.rowconfigure(7, weight=1)
window.rowconfigure(8, weight=1)
window.rowconfigure(9, weight=1)
window.rowconfigure(10, weight=1)
window.rowconfigure(11, weight=1)
window.rowconfigure(12, weight=1)
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=10)
window.columnconfigure(2, weight=10)
window.columnconfigure(3, weight=10)

# BOTONES
Button(window, text="Iniciar gráfica temp", bg='green', command=Iniciarclick).grid(row=0, column=0, sticky="nsew")
Button(window, text="Parar", bg='red', command=Parar).grid(row=1, column=0, sticky="nsew")
Button(window, text="Reanudar", bg='blue', fg="white", command=Reanudar).grid(row=2, column=0, sticky="nsew")
Button(window, text="Periodo", bg='orange', command=CambiarPeriodo).grid(row=3, column=0, sticky="nsew")
Button(window, text="Temp Máx", bg='purple', fg="white", command=CambiarValorMaxTemp).grid(row=4, column=0, sticky="nsew")
Button(window, text="Orientación", bg='yellow', command=CambiarOrientacion).grid(row=5, column=0, sticky="nsew")
Button(window, text="Modo sensor", bg='pink', command=CambiarModoControl).grid(row=6, column=0, sticky="nsew")
Button(window, text="Observación", bg='black', fg='white', command=EscribirObservacion).grid(row=7, column=0, sticky="nsew")
Button(window, text="Registro", bg='lightgray', command=MostrarRegistro).grid(row=8, column=0, sticky="nsew")
Button(window, text="Media Arduino/Python", bg='lightblue', command=CambiarMedia).grid(row=9, column=0, sticky="nsew")

# GRAFICA TEMPERATURA
GrafFrame = Frame(window)
GrafFrame.grid(row=0, column=1, rowspan=10, sticky="nsew")
fig_temp, ax_temp = plt.subplots(figsize=(6,4))
canvas_temp = FigureCanvasTkAgg(fig_temp, master=GrafFrame)
canvas_temp.get_tk_widget().pack(fill=BOTH, expand=1)

# RADAR
RadarFrame = Frame(window)
RadarFrame.grid(row=0, column=2, rowspan=10, sticky="nsew")
fig_rad, ax_radar = plt.subplots(subplot_kw={"projection": "polar"})
canvas_radar = FigureCanvasTkAgg(fig_rad, master=RadarFrame)
canvas_radar.get_tk_widget().pack(fill=BOTH, expand=1)

# GROUNDTRACK
GTFrame = Frame(window)
GTFrame.grid(row=0, column=3, rowspan=10, sticky="nsew")
canvas_gt = FigureCanvasTkAgg(fig_gt, master=GTFrame)
canvas_gt.get_tk_widget().pack(fill=BOTH, expand=1)

# ENTRADA DE TEXTO
MensajeVar = StringVar()
Label(window, textvariable=MensajeVar).grid(row=10, column=0, columnspan=3)
ValorEntry = Entry(window)
ValorEntry.grid(row=11, column=0, columnspan=3)
Button(window, text="Enviar", command=EnviarValor).grid(row=12, column=0, columnspan=3)

window.mainloop()
