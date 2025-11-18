import serial
import matplotlib.pyplot as plt
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import numpy as np
from mpl_toolkits.basemap import Basemap


device = 'COM5'  # Cambiar por el puerto correspondiente
mySerial = serial.Serial(device, 9600, timeout=1)


# Variables globales para guardar datos
temperaturas = []
medias = []
eje_x = []
i = 0
running = False
limite_alarma = 25.0  # Límite de temperatura para la alarma
accion_actual = None
angulos = []
distancias = []

# Groundtrack variables
orbits = [[]]
orbit_lines = []
lat_vals = []
lon_vals = []
max_orbits = 5
sat_point = None
groundtrack_enabled = False

# Definiciones para los groundtracks

def ecef_to_geodetic(x, y, z): # Convierte coordenadas esféricas a 2D
    lon = np.degrees(np.arctan2(y, x))
    hyp = np.sqrt(x*x + y*y)
    lat = np.degrees(np.arctan2(z, hyp))
    return lat, lon

def crossed_dateline(lon_old, lon_new): # Hace el salto de línea cuando se llega a los 180º
    return abs(lon_new - lon_old) > 300

def MostrarGroundtracks():
    global groundtrack_enabled, groundtrack_fig, groundtrack_ax, groundtrack_canvas
    groundtrack_enabled = True

    global m, sat_point, orbit_lines, orbits #Listas para guardar las orbitas
    orbits = [[]]
    orbit_lines = []

    # Características del mapa de fondo
    m = Basemap(projection='mill', lon_0=0, ax=groundtrack_ax)
    m.drawcoastlines()
    m.drawparallels(np.arange(-90,90,30))
    m.drawmeridians(np.arange(-180,180,60))
    m.drawmapboundary(fill_color='aqua')
    m.fillcontinents(color='coral',lake_color='aqua')

    # Marca la posición del satélite con un punto rojo
    sat_point = m.scatter([], [], s=60, c='red', zorder=5)

    # CÓDIGO XYZ PARA GROUNDTRACKS ---> codigo = 4
    while mySerial.in_waiting > 0:
        linea = mySerial.readline().decode('utf-8').rstrip()
        print(linea)
        temp = linea.split(" ")
        try:
            codigo = int(temp[0])
        except ValueError:
            continue
        if codigo == 4 and len(temp) >= 4:
            try:
                x = float(temp[1])
                y = float(temp[2])
                z = float(temp[3])

                if groundtrack_enabled:
                    lat, lon = ecef_to_geodetic(x, y, z)

                    current_orbit = orbits[-1]

                    if len(current_orbit) > 0:
                        lon_prev, lat_prev = current_orbit[-1]
                        if crossed_dateline(lon_prev, lon):
                            orbits.append([])
                            orbit_lines.append(m.plot([], [], 'bo-', markersize=3)[0])

                            if len(orbits) > max_orbits:
                                orbits.pop(0)
                                old_line = orbit_lines.pop(0)
                                old_line.remove()
                            current_orbit = orbits[-1]

                    current_orbit.append((lon, lat))

                    if len(orbit_lines) < len(orbits):
                        orbit_lines.append(m.plot([], [], 'bo-', markersize=3)[0])

                    for idx, orbit in enumerate(orbits):
                        if len(orbit) > 1:
                            lons, lats = zip(*orbit)
                            xm, ym = m(lons, lats)
                            orbit_lines[idx].set_data(xm, ym)

                    x_sat, y_sat = m(lon, lat)
                    sat_point.set_offsets([[x_sat, y_sat]])

                    groundtrack_canvas.draw()
            except ValueError:
                pass

def Reanudar():    # Envia el mensaje para reanudar el envio
    mensaje = "Reanudar"
    mySerial.write(mensaje.encode('utf-8'))

def Parar():   # Envia el mensaje para detener el envio
    mensaje = "Parar"
    mySerial.write(mensaje.encode('utf-8'))

def update_plot():
    global i, running
    if running:
        while mySerial.in_waiting > 0:
            linea = mySerial.readline().decode('utf-8').rstrip()
            print(linea)
            temp = linea.split(" ")
            try:
                  codigo = int(temp[0])
            except ValueError:
                  continue  # Ignorar líneas mal formateadas
            if codigo == 1 and len(temp) >= 3:  # Temperatura y humedad
                try:
                    humedad = float(temp[1])
                    temperatura = float(temp[2])
                    temperaturas.append(temperatura)
                    eje_x.append(i)
                    i += 1
                    
                    ultimos_10 = temperaturas[-10:] # Últimas 10 temperaturas
                    media = sum(ultimos_10) / len(ultimos_10)
                    medias.append(media)

                    # detección de alarma
                    if len(medias) >= 3:
                        if medias[-1] > limite_alarma and medias[-2] > limite_alarma and medias[-3] > limite_alarma:
                            print("Tres medias consecutivas por encima del límite!")
                except ValueError:
                    # Si no se puede convertir, ignorar la línea
                    pass
            if codigo == 2 and len(temp) >= 3:
                try:
                    angulo = float(temp[1])
                    distancia = float(temp[2])
                    angulos.append(angulo)
                    distancias.append(distancia)
                except ValueError:
                    pass
        # Limitamos a últimos 5 datos
        angulos[:] = angulos[-5:]  # Limit 5 últims
        distancias[:] = distancias[-5:]  # Limit 5 últims
        
        ax.clear()
        ax.set_xlim(0, max(100, i))
        ax.set_ylim(20, 30)  # Limites de temperatura
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
            radianes = np.deg2rad(np.array(angulos))  # convertir grados a radianes
            ax_radar.plot(radianes, distancias, color="yellow") 
            ax_radar.plot([radianes[-1]], [distancias[-1]], "go", markersize=10)
            ax_radar.plot([0, radianes[-1]], [0, distancias[-1]], "g")
        canvas_radar.draw()

        # Llama a sí mismo después de 500 ms para actualizar la gráfica
        window.after(500, update_plot)

def Iniciarclick():
    global running, temperaturas, eje_x, i
    if not running:
        running = True
        temperaturas.clear()
        medias.clear()
        eje_x.clear()
        i = 0
        update_plot()

def Detenerclick():
    global running
    running = False

def CambiarPeriodo():
    global accion_actual
    accion_actual = "periodo"
    MensajeVar.set("Escribe el nuevo periodo de transmision (segundos):")
    ValorEntry.delete(0, END)

def CambiarOrientacion():
    global accion_actual
    accion_actual = "orientacion"
    MensajeVar.set("Escribe la nueva orientacion del sensor (grados):")
    ValorEntry.delete(0, END)

def CambiarValorMaxTemp():
    global accion_actual
    accion_actual = "ValorTempMax"
    MensajeVar.set("Escribe el valor máximo de la temperatura (grados centígrados):")
    ValorEntry.delete(0,END)

def CambiarModoControl():
    mensaje = "Cambio"
    mySerial.write(mensaje.encode('utf-8'))

def EnviarValor():
    valor = ValorEntry.get()
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

    # Despues de enviar, vacia la barra y el mensaje
    MensajeVar.set("")
    ValorEntry.delete(0, END)

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
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=10)
window.columnconfigure(2, weight=10)

# Elementos de la interfaz

#   BOTONES
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

MostrarGroundtracksButton = Button(window, text="Mostrar Groundtracks", bg="lightblue", command=MostrarGroundtracks)
MostrarGroundtracksButton.grid(row=7, column=0, padx=5, pady=5, sticky=N+S+E+W)

#   GRÁFICAS
# Temperatura
GraficaFrame = Frame(window)
GraficaFrame.grid(row=0, column=1, rowspan=8, padx=5, pady=5, sticky=N + S + E + W)
fig, ax = plt.subplots(figsize=(6,4))
canvas = FigureCanvasTkAgg(fig, master=GraficaFrame)
canvas.get_tk_widget().pack(fill=BOTH, expand=1)
#Groundtrack
GroundtrackFrame = Frame(window)
GroundtrackFrame.grid(row=0, column=2, rowspan=8, padx=5, pady=5, sticky=N+S+E+W)
groundtrack_fig = plt.figure(figsize=(6,4))
groundtrack_ax = groundtrack_fig.add_subplot(111)
groundtrack_canvas = FigureCanvasTkAgg(groundtrack_fig, master=GroundtrackFrame)
groundtrack_canvas.get_tk_widget().pack(fill=BOTH, expand=1)
#Radar
RadarFrame = Frame(window)
RadarFrame.grid(row=0, column=2, rowspan=8, padx=5, pady=5, sticky=N + S + E + W)
fig_radar = plt.figure()
ax_radar = fig_radar.add_subplot(111, projection='polar')
canvas_radar = FigureCanvasTkAgg(fig_radar, master=RadarFrame)
canvas_radar.get_tk_widget().pack(fill=BOTH, expand=1)

#   INTRODUCCIÓN DATOS
# Barra valor y mensaje debajo de la grafica
MensajeVar = StringVar()
MensajeLabel = Label(window, textvariable=MensajeVar, anchor=W)
MensajeLabel.grid(row=8, column=0, columnspan = 3, padx=5, pady=2, sticky=N+S+E+W)

ValorEntry = Entry(window)
ValorEntry.grid(row=9, column=0, columnspan = 3, padx=5, pady=2, sticky=N+S+E+W)

EnviarButton = Button(window, text="Envia", bg="gray", command=EnviarValor)
EnviarButton.grid(row=10, column=0, columnspan = 3, padx=5, pady=2, sticky=N+S+E+W)

window.mainloop()