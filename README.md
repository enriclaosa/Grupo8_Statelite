GRUPO 8
Gala Jané, Enric Laosa, Aniol Castany

<img width="600" height="700" alt="image" src="https://github.com/user-attachments/assets/c2a60d96-9b3a-43fb-9a42-56948999b480" />


PROYECTO SISTEMA SATELITAL


INTRODUCCIÓN

En este proyecto hemos creado un sistema satelital simulado con unas placas de Arduino. Nuestro objetivo es aprender a programar en los lenguajes C y Python mediante este proyecto. Como estudiantes de ingeniería de satélites, es muy interesante poder programar el funcionamiento de un satélite, muy simplificado, y su estación de tierra en lenguajes que se usan actualmente para estos fines.


HARDWARE

Nuestro sistema consta de 2 placas Arduino UNO comunicadas mediante unas antenas LoRa. Una placa simula ser el satélite y la otra nuestra estación de tierra.
A continuación aclararemos los elementos del hardware para facilitar la comprensión.

En la placa satélite tenemos 2 sensores, 1 led, 1 servomotor y un joystick

Sensores:
1. El sensor de temperatura y humedad.
2. El sensor de ultrasonidos, que se encuentra montado en un servo y realiza un barrido que se muestra en forma de radar en la interfaz gráfica.

Led:
1. El led verde se ilumina cada vez que se transmiten datos a la estación de tierra.

Joystick:
1. Al activar desde la interfaz gráfica el modo de control manual, el servo dejará de hacer un barrido y se podrá mover manualmente usando el joystick.

Nuestro satélite envia datos de temperatura y humedad, además de la posición y distancia de los objetos que detecta con el sensor de ultrasonidos y el ángulo en el que se encuentra apuntando el servo.


En la placa de estación de tierra tenemos 3 leds y un buzzer.

Leds:
1. El led rojo se enciende cada vez que se reciben datos del satélite.
2. El led amarillo se enciende cuando la estación de tierra no recibe dato alguno durante 8 segundos.
3. El led azul cuando el sensor de temperatura y humedad ha tenido un fallo.

Buzzer:
1. Esta señal acústica de enciende durante un segundo cuando se detecta un fallo del sensor de ultrasonidos.

El Arduino de estación de tierra a parte de procesar los datos que se envían desde el satélite, también simula la orbita que seguiría un satélite real, para mostrar unos groundtracks en la interfaz gráfica.
El sistema satelital funciona con un kit de conexiones inalámbricas LoRa, así podemos separar la estación de tierra de nuestro satélite y todo funcionara con normalidad, ya que no depende de comunicación por cable.


SOFTWARE

El software está separado en 3 programas, el programa del satélite, de la estación de tierra y de la interfaz gráfica. El satélite y la estación de tierra estan programadas en C. La interfaz gráfica en Python.
Lo más relevante acerca de los códigos es el sistema que usamos para enviar datos. Para que se puedan procesar bien, los distintos tipos de datos empiezan por un número distinto para clasificarlos y también se envia el checksum, que descarta la línea de datos enviados si no es correcto.

Para procesar los datos, nuestro programa lee el primer número y luego cada valor separado por un espacio es un dato distinto que se envia.

En la estación de tierra usamos la siguiente configuración:

Con el número de clasificación 1: obtenemos la humedad y la temperatura.

Con el número de clasificación 2: obtenemos el ángulo al que esta apuntando el servo y la distancia que lee el sensor de ultrasonidos.

Con el número de clasificación 3: si anteriormente se ha ordenado que la media de las últimas 10 temperaturas se calcule en el satélite, se recibe por este codigo, en caso contrario, la media se calcula directamente en la interfaz y no se recibe nada con este código.

Con el número de clasificación 4: se reciben las coordenadas x, y, z necesarias para dibujar la órbita del satélite.

Para los datos que recibe el satélite usamos esta otra nomenclatura:

Con el número de clasifiación 1: el nuevo intervalo de transmisión de datos que ha elegido el usuario desde la interfaz (en segundos).

Con el número de clasifiación 2: El ángulo que tomará el servo. En la estación de tierra se debe insertar un ángulo entre 0º y 180º, y luego pulsar enviar. Así el sensor de ultrasonidos se quedará mirando fijamente a esa orientación. Para volver a ponerlo en modo barrido se debe enviar -1.


Instrucciones generales para la interfaz:
Una vez se ejecuta el programa, solo están activados los groundtracks, para encender la gráfica de temperatura y el radar hay que pulsar el botón que las inicia. El registro de eventos tiene integrado un calendario para escoger el dia del archivo y un selector de tipo para filtrar por distintas alarmas y comandos. En la parte inferior de la gráfica hay una barra de texto, que mediante distintos botones se podrá enviar información al satélite.


MODIFICACIONES VERSIÓN 4:

Para la versión final del proyecto se nos dieron algunas ideas y la libertad de añadir lo que quisieramos al sistema satelital. A continuación detallaremos lo que hemos añadido. También hemos optimizado y estructurado mejor el código para que sea más fácil de entender y te puedas mover mejor por este. Por otro lado, hemos cambiado ligeramente la apariencia de la interfaz gráfica para que sea más amigable y limpia.

Nuevas funcionalidades:
1. Modificación de la visualización de la órbita simulada: Anteriormente teníamos una esfera que simulaba la tierra y se dibujaba la órbita simulada alrededor de ella, lo cual hemos cambiado por unos groundtracks que muestran el mapamundi i se dibuja la trayectoria por donde pasa el satélite.
2. Mejora del radar: Hemos actualizado la vista del radar, el cual luce ahora mucho más profesional.
3. Calendario en el registro de eventos: En el registro de eventos, donde anteriormente para filtrar por fecha los eventos se tenía que escribir manualment la fecha, hemos implementado un calendario donde se puede elegir dicha fecha.
4. Control manual del servomotor con el sensor ultrasónico: Además de los dos modos ya establecidos anteriormente del servomotor (barrido automático y angulo determinado), hemos añadido un tercer modo de control, que se basa en el control manual del servomotor con un joystick. Para alternar entre este modo y los otros dos, utilizaremos el botón "Cambiar modo control sensor".
5. Modo simulación: cuando se activa el modo simulación, el programa no lee datos de Arduino, sino que reproduce un archivo CSV con datos preestablecidos. Lee cada fila del archivo, identifica si es temperatura, media, radar o posición del satélite, y actualiza los gráficos exactamente igual que si vinieran de Arduino en tiempo real. Esto permite ver cómo habría respondido el satélite y sus sensores sin necesidad de conectarlos.


Componentes que se perdieron durante la elaboración del proyecto:

<img width="592" height="262" alt="image" src="https://github.com/user-attachments/assets/7d6e8988-19da-43da-93f3-7aa8ebc89176" />
R.I.P. 🙏
