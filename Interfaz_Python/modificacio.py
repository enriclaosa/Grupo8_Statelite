import serial
import matplotlib.pyplot as plt
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import numpy as np
import datetime
from tkinter.scrolledtext import ScrolledText
import matplotlib
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from tkinter import ttk
from tkcalendar import DateEntry



# CONFIGURACIÓ SERIAL
device = 'COM5'  # Canvia pel teu port
mySerial = serial.Serial(device, 9600, timeout=2)

# VARIABLES GLOBALS
temperaturas = []
medias = []
eje_x = []
i = 0
running = False
limite_alarma = 25.0
accion_actual = None
media_en_arduino = False

radar_objects = []  # guarda (angle, distancia)
sweep_angle = 0
sweep_dir = 1  # 1 = avanç, -1 = enrere
sweep_speed = 2  # graus per actualització

DateTime = datetime.datetime.now()
fecha_hora_actual = DateTime.strftime("%d-%m-%Y %H:%M")

# VARIABLES GROUNDTRACK
matplotlib.use('TkAgg')
R_EARTH = 6371000  # Radio de la Tierra en metros
EARTH_ROTATION_RATE = 7.2921159e-5  # Velocidad de rotación de la Tierra (rad/s)
TIME_COMPRESSION = 90.0  # Factor de compresión temporal
ALTITUDE = 400000  # Altitud del satélite en metros
latitudes = []  # Lista de latitudes
longitudes = []  # Lista de longitudes
tiempo_inicio_orbita = None  # Tiempo de inicio para calcular rotación
CARTOPY_AVAILABLE = True


fig_gt = plt.Figure(figsize=(8, 6))

# Función para convertir coordenadas cartesianas (x, y, z) a latitud y longitud
def cartesian_to_geographic(x, y, z):
    """
    Convierte coordenadas cartesianas orbitales a coordenadas geográficas.
    Las coordenadas vienen del Arduino en el sistema orbital:
    - x = r * cos(angle) en el plano orbital
    - y = r * sin(angle) * cos(inclination) en el plano orbital  
    - z = r * sin(angle) * sin(inclination) perpendicular al plano
    
    Con inclination=0 y ecef=0, tenemos:
    - x = r * cos(angle)
    - y = r * sin(angle)
    - z = 0 (órbita ecuatorial)
    
    Para obtener el groundtrack correcto, necesitamos aplicar la transformación ECEF
    que el Arduino no está aplicando (porque ecef=0). Esto considera la rotación de la Tierra.
    """
    global tiempo_inicio_orbita
    
    # Inicializar el tiempo de inicio en el primer punto
    if tiempo_inicio_orbita is None:
        tiempo_inicio_orbita = datetime.datetime.now()
    
    # Calcular distancia desde el centro
    r = np.sqrt(x**2 + y**2 + z**2)
    
    if r == 0:
        return 0.0, 0.0
    
    # Calcular el tiempo transcurrido desde el inicio (en segundos reales)
    tiempo_actual = datetime.datetime.now()
    tiempo_transcurrido = (tiempo_actual - tiempo_inicio_orbita).total_seconds()
    
    # Aplicar la transformación ECEF que el Arduino no aplica (porque ecef=0)
    # La Tierra rota hacia el este, así que necesitamos rotar las coordenadas
    theta = EARTH_ROTATION_RATE * tiempo_transcurrido
    
    # Transformación ECEF: rotar las coordenadas x, y en el plano ecuatorial
    x_ecef = x * np.cos(theta) - y * np.sin(theta)
    y_ecef = x * np.sin(theta) + y * np.cos(theta)
    z_ecef = z  # z no cambia en la transformación ECEF
    
    # Calcular hipotenusa en el plano ecuatorial (x-y) después de la transformación
    hyp = np.sqrt(x_ecef**2 + y_ecef**2)
    
    # Calcular latitud: ángulo desde el plano ecuatorial hacia el polo norte
    lat_rad = np.arctan2(z_ecef, hyp)
    lat = np.degrees(lat_rad)
    
    # Calcular longitud: ángulo en el plano ecuatorial (x-y) después de la transformación ECEF
    lon_rad = np.arctan2(y_ecef, x_ecef)
    lon = np.degrees(lon_rad)
    
    # Normalizar longitud a rango [-180, 180]
    while lon > 180:
        lon -= 360
    while lon < -180:
        lon += 360
    
    return lat, lon

# Crear el plot del groundtrack
if CARTOPY_AVAILABLE:
    # Usar Cartopy para mapa realista
    ax_gt = fig_gt.add_subplot(111, projection=ccrs.PlateCarree())
    ax_gt.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax_gt.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=':')
    ax_gt.add_feature(cfeature.LAND, alpha=0.5, color='lightgray')
    ax_gt.add_feature(cfeature.OCEAN, alpha=0.5, color='lightblue')
    ax_gt.set_global()
    ax_gt.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle='--')
    # Usar línea suave para la trayectoria
    orbit_plot, = ax_gt.plot([], [], 'r-', linewidth=2.5, label='Trayectoria del Satélite', 
                             transform=ccrs.PlateCarree(), alpha=0.8, zorder=3)
    last_point_plot = ax_gt.scatter([], [], color='red', s=120, marker='o', 
                                     edgecolors='black', linewidths=2.5, 
                                     label='Posición Actual', transform=ccrs.PlateCarree(), zorder=5)
    ax_gt.set_title("Groundtrack del Satélite", fontsize=14, fontweight='bold')
else:
    # Versión alternativa sin Cartopy (mapa básico con proyección)
    ax_gt = fig_gt.add_subplot(111)
    # Crear un mapa básico con proyección simple
    # Dibujar "Tierra" como círculo
    earth_circle = plt.Circle((0, 0), 1, color='lightblue', alpha=0.4, zorder=0)
    ax_gt.add_patch(earth_circle)
    # Líneas de latitud (paralelos)
    for lat in range(-90, 91, 30):
        y = np.sin(np.radians(lat))
        ax_gt.plot([-1, 1], [y, y], 'k--', alpha=0.2, linewidth=0.5, zorder=1)
        if lat != 0:  # Etiquetar paralelos importantes
            ax_gt.text(1.05, y, f'{lat}°', va='center', fontsize=7, alpha=0.6)
    # Líneas de longitud (meridianos)
    for lon in range(-180, 181, 45):
        x = np.cos(np.radians(lon))
        y_start = -1
        y_end = 1
        ax_gt.plot([x, x], [y_start, y_end], 'k--', alpha=0.2, linewidth=0.5, zorder=1)
        if lon % 90 == 0:  # Etiquetar meridianos principales
            ax_gt.text(x, -1.1, f'{lon}°', ha='center', fontsize=7, alpha=0.6)
    
    # Línea del ecuador más destacada
    ax_gt.plot([-1, 1], [0, 0], 'b-', alpha=0.4, linewidth=1, zorder=1, label='Ecuador')
    
    ax_gt.set_xlim(-1.2, 1.2)
    ax_gt.set_ylim(-1.2, 1.2)
    ax_gt.set_aspect('equal', 'box')
    orbit_plot, = ax_gt.plot([], [], 'r-', linewidth=2.5, label='Trayectoria del Satélite', zorder=3)
    last_point_plot = ax_gt.scatter([], [], color='red', s=120, marker='o', 
                                     edgecolors='black', linewidths=2.5, 
                                     label='Posición Actual', zorder=5)
    ax_gt.set_xlabel('Longitud (proyección normalizada)', fontsize=9)
    ax_gt.set_ylabel('Latitud (proyección normalizada)', fontsize=9)
    ax_gt.set_title("Groundtrack del Satélite\n(Instala Cartopy para mapa realista)", 
                    fontsize=12, fontweight='bold')
    ax_gt.grid(True, alpha=0.2, zorder=1)
    ax_gt.legend(loc='upper right', fontsize=8, framealpha=0.9)

# FUNCIONS PRINCIPALS
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
    RegistrarEvento("Comando:", "parar transmision de datos")

def Reanudar():
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
    MensajeVar.set("Escribe la nueva orientacion del sensor (grados) (escribir -1 para volver a modo automatico:")
    ValorEntry.delete(0, END)
    RegistrarEvento("Comando:", "cambiar orientacion del sensor")

def CambiarModoControl():
    mensaje = "Cambio\n"  # incluir \n para que Arduino lo reciba completo
    mySerial.write(mensaje.encode('utf-8'))
    RegistrarEvento("Comando:", "activar control por joystick")

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
        try:
            limite_alarma = float(valor)
        except ValueError:
            MensajeVar.set("Introduce un número válido")
            return
    elif accion_actual == "observacion":
        RegistrarEvento("Observacion:", valor)

    MensajeVar.set("")
    ValorEntry.delete(0, END)

def RegistrarEvento(tipo, mensaje):
    fecha_hora_actual = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    with open("registro_eventos.txt", "a", encoding="utf-8") as f:
        f.write("{} {} {}\n".format(fecha_hora_actual, tipo, mensaje))

def MostrarRegistro():
    RegistroWindow = Toplevel(window)
    RegistroWindow.title("Registro filtrado")

    filtros_frame = ttk.Frame(RegistroWindow)
    filtros_frame.pack(pady=5, padx=5, fill="x")

    ttk.Label(filtros_frame, text="Fecha (dd-mm-yyyy):").grid(row=0, column=0, padx=5)
    entry_data = DateEntry(filtros_frame)
    entry_data.grid(row=0, column=1, padx=5)

    ttk.Label(filtros_frame, text="tipo de evento:").grid(row=0, column=2, padx=5)
    tipo_var = StringVar()
    tipo_var.set("Cualquiera")
    menu_tipo = ttk.OptionMenu(filtros_frame, tipo_var, "Cualquiera", "Comando", "Alarma", "Observacion")
    menu_tipo.grid(row=0, column=3, padx=5)

    text_area = ScrolledText(RegistroWindow, width=100, height=30)
    text_area.pack(expand=True, fill="both")
    text_area.config(state="disabled") 
    def aplicar_filtros():
        fecha_filtro = entry_data.get_date().strftime("%d-%m-%Y")
        tipo_filtro = tipo_var.get()
        resultado = []
        try:
            with open("registro_eventos.txt", "r", encoding="utf-8") as f:
                lineas = f.readlines()
        except FileNotFoundError:
            text_area.insert("1.0", "El fichero no existe.")
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

    aplicar_btn = ttk.Button(
    filtros_frame,
    text="Aplicar filtros",
    command=aplicar_filtros) 
    aplicar_btn.grid(row=0, column=4, padx=5)


# Función única para leer datos del puerto serial
def leer_datos_serial():
    global i, radar_objects
    while mySerial.in_waiting > 0:
        try:
            linea = mySerial.readline().decode('utf-8').rstrip()
            if not linea:  # Ignorar líneas vacías
                continue
                
            temp = linea.split(" ")
            if len(temp) < 2:  # Necesita al menos código y un dato
                continue
                
            try:
                codigo = int(temp[0])
            except (ValueError, IndexError):
                continue

            # TEMPERATURA (código 1)
            
            if codigo == 1 and len(temp) >= 3:
                try:
                    humedad = float(temp[1])
                    temperatura = float(temp[2])
                    temperaturas.append(temperatura)
                    eje_x.append(i)
                    i += 1
                except (ValueError, IndexError) as e:
                    print(f"Error procesando temperatura: {e}, línea: {linea}")
                    continue
            if not media_en_arduino:
                    ultimos_10 = temperaturas[-10:]
                    media = sum(ultimos_10)/len(ultimos_10) if len(ultimos_10) > 0 else temperatura
                    medias.append(media)
                    if len(medias) >= 3 and medias[-1] > limite_alarma and medias[-2] > limite_alarma and medias[-3] > limite_alarma:
                        RegistrarEvento("Alarma:", "tres medias de temperatura consecutivas por encima del limite!") 
                
        
            if media_en_arduino and codigo == 3 and len(temp) >= 2:
                try:
                    media = float(temp[1])
                    if len(medias) > 0:
                    # Filtrat exponencial: suavitza el salt entre valors consecutius
                        alpha = 0.2
                        media = alpha*media + (1-alpha)*medias[-1]
                    medias.append(media)
                    if len(medias) >= 3 and medias[-1] > limite_alarma and medias[-2] > limite_alarma and medias[-3] > limite_alarma:
                        RegistrarEvento("Alarma:", "tres medias de temperatura consecutivas por encima del limite!") 
                
                except ValueError:
                    continue
            
            # RADAR (código 2)
            elif codigo == 2 and len(temp) >= 3:
                try:
                    angulo = float(temp[1])
                    distancia = float(temp[2])
                    radar_objects.append((angulo, distancia))
                    if len(radar_objects) > 50:
                        radar_objects.pop(0)
                except (ValueError, IndexError) as e:
                    print(f"Error procesando radar: {e}, línea: {linea}")
                    continue

            # GROUNDTRACK (código 4)
            # Ahora el Arduino envía directamente latitud y longitud
            elif codigo == 4 and len(temp) >= 3:
                try:
                    # El Arduino ahora envía: código latitud longitud
                    lat = float(temp[1])
                    lon = float(temp[2])
                    
                    # Detectar cruce de la línea de fecha internacional (180°/-180°)
                    # Si hay un salto grande, insertar NaN para crear discontinuidad
                    if len(longitudes) > 0:
                        lon_prev = longitudes[-1]
                        # Calcular la diferencia más corta considerando el wrap-around
                        diff1 = lon - lon_prev  # Diferencia directa
                        diff2 = lon - lon_prev + 360 if lon_prev < 0 else lon - lon_prev - 360  # Diferencia con wrap
                        
                        # Usar la diferencia más pequeña en valor absoluto
                        if abs(diff2) < abs(diff1):
                            diff = diff2
                        else:
                            diff = diff1
                        
                        # Si el salto es mayor a 90 grados, es probable un cruce de la línea de fecha
                        # Insertar NaN para crear una discontinuidad en la línea
                        if abs(diff) > 90:
                            latitudes.append(np.nan)
                            longitudes.append(np.nan)
                    
                    latitudes.append(lat)
                    longitudes.append(lon)
                    
                    # Limitar el número de puntos para mantener el rendimiento
                    max_points = 2000  # Aumentado para mejor resolución de la curva
                    if len(latitudes) > max_points:
                        latitudes.pop(0)
                        longitudes.pop(0)
                    
                    # Actualizar el plot con todos los puntos para mostrar la curva completa
                    if CARTOPY_AVAILABLE:
                        # Usar set_data para actualizar toda la trayectoria
                        # NaN en los datos creará discontinuidades automáticamente
                        orbit_plot.set_data(longitudes, latitudes)
                        last_point_plot.set_offsets([[lon, lat]])
                    else:
                        # Para la versión sin cartopy, usar proyección más precisa
                        # Convertir lat/lon a coordenadas para el plot básico
                        # Manejar NaN correctamente
                        longitudes_norm = []
                        latitudes_norm = []
                        for l, la in zip(longitudes, latitudes):
                            if not np.isnan(l) and not np.isnan(la):
                                longitudes_norm.append(l/180.0)
                                latitudes_norm.append(np.sin(np.radians(la)))
                            else:
                                longitudes_norm.append(np.nan)
                                latitudes_norm.append(np.nan)
                        orbit_plot.set_data(longitudes_norm, latitudes_norm)
                        lon_norm = lon / 180.0
                        lat_norm = np.sin(np.radians(lat))
                        last_point_plot.set_offsets([[lon_norm, lat_norm]])
                    
                    canvas_GT.draw()
                except (ValueError, IndexError) as e:
                    print(f"Error procesando groundtrack: {e}, línea: {linea}")
                    continue
        except UnicodeDecodeError:
            # Ignorar errores de decodificación
            continue
        except Exception as e:
            print(f"Error inesperado leyendo serial: {e}")
            continue

def update_plot():
    # PLOTS TEMPERATURA (la lectura serial se hace en actualizar_radar_serial)
    ax.clear()
    ax.set_xlim(0, max(50, i))
    ax.set_ylim(15, 25)
    if len(eje_x) > 0 and len(temperaturas) > 0:
        ax.plot(eje_x, temperaturas, label='Temperatura', linewidth=2)
    if len(eje_x) > 0 and len(medias) > 0:
        min_len = min(len(eje_x), len(medias))
        ax.plot(eje_x[:min_len], medias[:min_len], label='Media últimos 10', color='orange', linewidth=2)
    ax.set_title('Temperatura y media en tiempo real')
    ax.set_xlabel('Muestras')
    ax.set_ylabel('Temperatura (°C)')
    ax.legend()
    canvas.draw()

    if running:
        window.after(500, update_plot)

# --------------------
# RADAR FUNCIONS
# --------------------
def actualizar_radar_serial():
    # Leer datos del puerto serial (única función que lee)
    leer_datos_serial()
    # Programar siguiente lectura
    window.after(20, actualizar_radar_serial)  # 50Hz lectura serial

def actualizar_radar_plot():
    global sweep_angle, sweep_dir
    ax_radar.clear()
    ax_radar.set_facecolor("black")
    ax_radar.set_theta_zero_location("E")
    ax_radar.set_theta_direction(1)
    ax_radar.grid(True, color="green", linestyle="--", linewidth=1.5)
    ax_radar.set_ylim(0, 80)
    ax_radar.set_yticks([0,20,40,60,80])
    ax_radar.set_yticklabels([str(x) for x in [0,20,40,60,80]], color="lime")
    
    angles = np.arange(0, 181, 45)
    ax_radar.set_xticks(np.deg2rad(angles))                       # CHANGED
    ax_radar.set_xticklabels([f"{a}°" for a in angles], color="lime")
    
    #ax_radar.set_xticklabels([f"{int(x)}°" for x in np.arange(0, 181, 45)], color="lime")
    
    # Sweep
    sweep_angle += sweep_dir*sweep_speed
    if sweep_angle>180:
        sweep_angle =180
        sweep_dir=-1
    elif sweep_angle<0:
        sweep_angle=0
        sweep_dir=1
    ax_radar.plot([np.deg2rad(sweep_angle), np.deg2rad(sweep_angle)], [0,100], color="lime", linewidth=2)

    # punts radar
    for ang, dist in radar_objects:
        if dist>100: dist=100
        ax_radar.plot(np.deg2rad(ang), dist, "ro", markersize=6, alpha=(0.5+0.5*np.sin(datetime.datetime.now().timestamp()*2)))  # parpelleig lent

    canvas_radar.draw()
    window.after(50, actualizar_radar_plot)  # refresc 20Hz

def actualizar_groundtrack_plot():
    """Actualiza periódicamente el plot del groundtrack para refrescar la visualización"""
    if len(latitudes) > 0 and len(longitudes) > 0:
        # Asegurar que la leyenda esté visible
        if CARTOPY_AVAILABLE:
            if not ax_gt.get_legend():
                ax_gt.legend(loc='upper left', fontsize=8, framealpha=0.9)
        else:
            if not ax_gt.get_legend():
                ax_gt.legend(loc='upper right', fontsize=8, framealpha=0.9)
        canvas_GT.draw()
    window.after(1000, actualizar_groundtrack_plot)  # Actualizar cada segundo


# INTERFICIE

window = Tk()

# ç estilo global botones
style = ttk.Style()
style.theme_use('clam')  
style.configure('TButton',
                font=('Segoe UI', 10),
                padding=6,
                relief='flat')  # sin borde 3D


window.geometry("2000x800")
#window.columnconfigure((0,1,2,3), weight=1)
window.rowconfigure(tuple(range(13)), weight=3)

window.columnconfigure(0, weight=1) # botones
window.columnconfigure(1, weight=3) # grafica temp
window.title("Interfície Gràfica Sensor Arduino") #titulo de la pestaña
window.columnconfigure(2, weight=3) # radar
window.columnconfigure(3, weight=4) # groundtrack


IniciarButton = ttk.Button(window, text="Iniciar gráfica temp",  command=Iniciarclick)
IniciarButton.grid(row=0, column=0, padx=5, pady=5, sticky=N + S + E + W)

PararButton = ttk.Button(window, text="Detener envío datos", command=Parar)
PararButton.grid(row=1, column=0, padx=5, pady=5, sticky=N + S + E + W)

ReanudarButton = ttk.Button(window, text="Reanudar envío datos", command=Reanudar)
ReanudarButton.grid(row=2, column=0, padx=5, pady=5, sticky=N + S + E + W)

CambiarPeriodoButton = ttk.Button(window, text="Cambiar periodo transmision", command=CambiarPeriodo)
CambiarPeriodoButton.grid(row=3, column=0, padx=5, pady=5, sticky=N+S+E+W)

CambiarValorMaxTempButton = ttk.Button(window, text="Cambiar valor máximo temperatura", command=CambiarValorMaxTemp)
CambiarValorMaxTempButton.grid(row=4, column=0, padx=5, pady=5, sticky=N+S+E+W)

CambiarOrientacionButton = ttk.Button(window, text="Cambiar orientacion sensor",  command=CambiarOrientacion)
CambiarOrientacionButton.grid(row=5, column=0, padx=5, pady=5, sticky=N+S+E+W)

CambiarModoControlButton = ttk.Button(window, text="Cambiar modo control sensor",  command=CambiarModoControl)
CambiarModoControlButton.grid(row=6, column=0, padx=5, pady=5, sticky=N+S+E+W)

EscribirObservacionButton = ttk.Button(window, text="Enviar observacion", command=EscribirObservacion)
EscribirObservacionButton.grid(row=7, column=0, padx=5, pady=5, sticky=N+S+E+W)

MostrarRegistroButton = ttk.Button(window, text="Mostrar registro de eventos", command=MostrarRegistro)
MostrarRegistroButton.grid(row=8, column=0, padx=5, pady=5, sticky=N+S+E+W)

MediaArduinoPythonButton = ttk.Button(window, text="Media Arduino/Python", command=CambiarMedia)
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
GraficaFrame.grid(row=0, column=1, rowspan=10, padx=5, pady=5, sticky=N+S+E+W)
fig, ax = plt.subplots(figsize=(6,4))
canvas = FigureCanvasTkAgg(fig, master=GraficaFrame)
canvas.get_tk_widget().pack(fill=BOTH, expand=1)

# RADAR
RadarFrame = Frame(window)
RadarFrame.grid(row=0, column=2, rowspan=10, padx=5, pady=5, sticky=N+S+E+W)
fig_radar = plt.figure()
ax_radar = fig_radar.add_subplot(111, projection='polar')
canvas_radar = FigureCanvasTkAgg(fig_radar, master=RadarFrame)
canvas_radar.get_tk_widget().pack(fill=BOTH, expand=1)

# GROUNDTRACK
GTFrame = Frame(window)
GTFrame.grid(row=0, column=3, rowspan=10, padx=5, pady=5, sticky=N+S+E+W)
canvas_GT = FigureCanvasTkAgg(fig_gt, master=GTFrame)
canvas_GT.get_tk_widget().pack(fill='both', expand=True)

# INICIA ACTUALITZACIONS
actualizar_radar_serial()
actualizar_radar_plot()
actualizar_groundtrack_plot()

window.mainloop()
