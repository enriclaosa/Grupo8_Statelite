import serial
import matplotlib.pyplot as plt
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import numpy as np
import datetime
from tkinter.scrolledtext import ScrolledText
import matplotlib

device = 'COM5'  # Cambiar por el puerto correspondiente
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
fig_gt = plt.Figure()
ax_gt = fig_gt.add_subplot(111)
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

def Parar():   # Envia el mensaje para detener el envio
    mensaje = "Parar"
    mySerial.write(mensaje.encode('utf-8'))
    RegistrarEvento("Comando:", "parar transmision de datos")

def Reanudar():    # Envia el mensaje para reanudar el envio
    mensaje = "Reanudar"
    mySerial.write(mensaje.encode('utf-8'))
    RegistrarEvento("Comando:", "reanudar transmision de datos")

def CambiarPeriodo():
    global accion_actual
    accion_actual = "periodo"
    MensajeVar.set("Escribe el nuevo periodo de transmision (segundos):")
    ValorEntry.delete(0, END)
    RegistrarEvento("Comando:", "cambiar periodo de transmisión de datos")

def CambiarValorMaxTemp():
    global accion_actual
    accion_actual = "ValorTempMax"
    MensajeVar.set("Escribe el valor máximo de la temperatura (grados centígrados):")
    ValorEntry.delete(0,END)
    RegistrarEvento("Comando:", "cambiar valor maximo de la temperatura")

def CambiarOrientacion():
    global accion_actual
    accion_actual = "orientacion"
    MensajeVar.set("Escribe la nueva orientacion del sensor (grados):")
    ValorEntry.delete(0, END)
    RegistrarEvento("Comando:", "cambiar orientacion del sensor")

def CambiarModoControl():
    mensaje = "Cambio"
    mySerial.write(mensaje.encode('utf-8'))

def EscribirObservacion():
    global accion_actual
    accion_actual = "observacion"
    MensajeVar.set("Escribe la observacion deseada:")
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
        mensaje = f"4 {valor}\n"
        mySerial.write(mensaje.encode('utf-8'))
    elif accion_actual == "orientacion":
        try:
            valor_int = int(valor)
            if valor_int == -1 or (0 <= valor_int <= 180):
                mensaje = f"2 {valor_int}\n"
                mySerial.write(mensaje.encode('utf-8'))
        except ValueError:
            MensajeVar.set("Introduce un número válido")
            return
    elif accion_actual == "ValorTempMax":
        limite_alarma = valor
    elif accion_actual == "observacion":
        RegistrarEvento("Observacion:", valor)

    # Despues de enviar, vacia la barra y el mensaje
    MensajeVar.set("")
    ValorEntry.delete(0, END)

def RegistrarEvento(tipo, mensaje):
    with open("registro_eventos.txt", "a", encoding="utf-8") as f:
        f.write("{} {} {}\n".format(fecha_hora_actual, tipo, mensaje))

def MostrarRegistro():
    def aplicar_filtros():
        fecha_filtro = entry_data.get().strip()
        tipo_filtro = tipo_var.get()
        resultado = []
        try:
            with open("registro_eventos.txt", "r", encoding="utf-8") as f:
                lineas = f.readlines()
        except FileNotFoundError:
            #text_area.config(state="normal")
            #text_area.delete("1.0", END)
            text_area.insert("1.0", "El fichero no existe.")
            #text_area.config(state="disabled")
            return

        for linea in lineas:
            # Filtro por fecha
            if fecha_filtro:
                if not linea.startswith(fecha_filtro):
                    continue

            # Filtro per tipo
            if tipo_filtro != "Cualquiera":
                if f"{tipo_filtro}:" not in linea:
                    continue

            resultado.append(linea)

        # Mostrar resultado
        text_area.config(state="normal")
        text_area.delete("1.0", END)
        if resultado:
            text_area.insert("1.0", "".join(resultado))
        else:
            text_area.insert("1.0", "No hay resultados.")
        text_area.config(state="disabled")

    RegistroWindow = Toplevel(window)
    RegistroWindow.title("Registro filtrado")

    filtros_frame = Frame(RegistroWindow)
    filtros_frame.pack(pady=5, padx=5, fill="x")

    Label(filtros_frame, text="Fecha (dd-mm-yyyy):").grid(row=0, column=0, padx=5)
    entry_data = Entry(filtros_frame)
    entry_data.grid(row=0, column=1, padx=5)

    Label(filtros_frame, text="tipo de evento:").grid(row=0, column=2, padx=5)
    tipo_var = StringVar()
    tipo_var.set("Cualquiera")
    menu_tipo = OptionMenu(filtros_frame, tipo_var, "Cualquiera", "Comando", "Alarma", "Observacion")
    menu_tipo.grid(row=0, column=3, padx=5)

    Button(filtros_frame, text="Aplicar filtros", command=aplicar_filtros).grid(row=0, column=4, padx=5)

    text_area = ScrolledText(RegistroWindow, width=100, height=30)
    text_area.pack(expand=True, fill="both")
    text_area.config(state="disabled")

def update_plot():
    global i, running, earth_slice
    if running:
        while mySerial.in_waiting > 0:
            linea = mySerial.readline().decode('utf-8').rstrip()
            print(linea)
            temp = linea.split(" ")
            try:
                  codigo = int(temp[0])
            except ValueError:
                  continue  # Ignorar líneas mal formateadas
            
            #TEMPERATURA
            if codigo == 1 and len(temp) >= 3:  # Temperatura y humedad
                try:
                    humedad = float(temp[1])
                    temperatura = float(temp[2])
                    temperaturas.append(temperatura)
                    eje_x.append(i)
                    i += 1
                    
                    if not media_en_arduino:
                        ultimos_10 = temperaturas[-10:] # Últimas 10 temperaturas
                        media = sum(ultimos_10) / len(ultimos_10)
                        medias.append(media)
                    if media_en_arduino:
                        media = float(temp[3])
                    # detección de alarma
                    if len(medias) >= 3:
                        if medias[-1] > limite_alarma and medias[-2] > limite_alarma and medias[-3] > limite_alarma:
                            RegistrarEvento("Alarma:", "tres medias de temperatura consecutivas por encima del limite!")
                except ValueError:
                    pass

            #RADAR
            if codigo == 2 and len(temp) >= 3:
                try:
                    angulo = float(temp[1])
                    distancia = float(temp[2])
                    angulos.append(angulo)
                    distancias.append(distancia)
                except ValueError:
                    pass
            
            #GROUNDTRACK
            if codigo == 4 and len(temp) >= 4:
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

        ax.clear()
        ax.set_xlim(0, max(100, i))
        ax.set_ylim(15, 25)
        ax.plot(eje_x, temperaturas, label='Temperatura')
        ax.plot(eje_x, medias, label='Media últimos 10', color='orange')
        ax.set_title('Temperatura y media en tiempo real')
        ax.set_xlabel('Muestras')
        ax.set_ylabel('Temperatura (°C)')
        ax.legend()
        canvas.draw()

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
window.geometry("1800x800")
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
IniciarButton = Button(window, text="Iniciar gráfica temp", bg='green', fg="black", command=Iniciarclick)
IniciarButton.grid(row=0, column=0, padx=5, pady=5, sticky=N + S + E + W)

PararButton = Button(window, text="Detener envío datos", bg='red', fg="black", command=Parar)
PararButton.grid(row=1, column=0, padx=5, pady=5, sticky=N + S + E + W)

ReanudarButton = Button(window, text="Reanudar envío datos", bg='blue', fg="white", command=Reanudar)
ReanudarButton.grid(row=2, column=0, padx=5, pady=5, sticky=N + S + E + W)

CambiarPeriodoButton = Button(window, text="Cambiar periodo transmision", bg='orange', fg="black", command=CambiarPeriodo)
CambiarPeriodoButton.grid(row=3, column=0, padx=5, pady=5, sticky=N+S+E+W)

CambiarValorMaxTempButton = Button(window, text="Cambiar valor máximo temperatura", bg='purple', fg="white", command=CambiarValorMaxTemp)
CambiarValorMaxTempButton.grid(row=4, column=0, padx=5, pady=5, sticky=N+S+E+W)

CambiarOrientacionButton = Button(window, text="Cambiar orientacion sensor", bg='yellow', fg="black", command=CambiarOrientacion)
CambiarOrientacionButton.grid(row=5, column=0, padx=5, pady=5, sticky=N+S+E+W)

CambiarModoControlButton = Button(window, text="Cambiar modo control sensor", bg='pink', fg='black', command=CambiarModoControl)
CambiarModoControlButton.grid(row=6, column=0, padx=5, pady=5, sticky=N+S+E+W)

EscribirObservacionButton = Button(window, text="Enviar observacion", bg='black', fg='white', command=EscribirObservacion)
EscribirObservacionButton.grid(row=7, column=0, padx=5, pady=5, sticky=N+S+E+W)

MostrarRegistroButton = Button(window, text="Mostrar registro de eventos",bg='lightgray', fg='black', command=MostrarRegistro)
MostrarRegistroButton.grid(row=8, column=0, padx=5, pady=5, sticky=N+S+E+W)

MediaArduinoPythonButton = Button(window, text="Media Arduino/Python",bg='lightblue', fg='black', command=CambiarMedia)
MediaArduinoPythonButton.grid(row=9, column=0, padx=5, pady=5, sticky=N+S+E+W)

#MENSAJE PARA EL USUARIO
MensajeVar = StringVar()
MensajeLabel = Label(window, textvariable=MensajeVar, anchor=W)
MensajeLabel.grid(row=10, column=0, columnspan = 4, padx=5, pady=2, sticky=N+S+E+W)

# ENTRADA DE TEXTO
ValorEntry = Entry(window)
ValorEntry.grid(row=11, column=0, columnspan = 4, padx=5, pady=2, sticky=N+S+E+W)

# BOTÓN ENVIAR
EnviarButton = Button(window, text="Envia", bg="gray", command=EnviarValor)
EnviarButton.grid(row=12, column=0, columnspan = 4, padx=5, pady=2, sticky=N+S+E+W)

# GRAFICA TEMPERATURA
GraficaFrame = Frame(window)
GraficaFrame.grid(row=0, column=1, rowspan=10, padx=5, pady=5, sticky=N + S + E + W)
fig, ax = plt.subplots(figsize=(6,4))
canvas = FigureCanvasTkAgg(fig, master=GraficaFrame)
canvas.get_tk_widget().pack(fill=BOTH, expand=1)

# RADAR
RadarFrame = Frame(window)
RadarFrame.grid(row=0, column=2, rowspan=10, padx=5, pady=5, sticky=N + S + E + W)
fig_radar = plt.figure()
ax_radar = fig_radar.add_subplot(111, projection='polar')
canvas_radar = FigureCanvasTkAgg(fig_radar, master=RadarFrame)
canvas_radar.get_tk_widget().pack(fill=BOTH, expand=1)

# GROUNDTRACK
GTFrame = Frame(window)
GTFrame.grid(row=0, column=3, rowspan=10, padx=5, pady=5, sticky=N + S + E + W)
canvas_GT = FigureCanvasTkAgg(fig_gt, master=GTFrame)
canvas_GT.get_tk_widget().pack(fill='both', expand=True)

window.mainloop()
