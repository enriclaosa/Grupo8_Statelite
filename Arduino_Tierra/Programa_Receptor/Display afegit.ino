#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)

const int led_rec = 2;                // LED rojo: indica recepción de datos
const int led_fallo_datostemp = 3;   // LED azul: indica fallo en datos de temperatura
const int led_timeout = 4;          // LED amarillo: indica timeout (5s sin datos)
const int buzzer = 7;          

const unsigned long led_on_interval = 500; // Duración que permanece encendido el LED de recepción
unsigned long led_rec_off_time = 0;        // Tiempo para apagar el LED de recepción
bool led_rec_on = false;

unsigned long last_message_time = 0;       // Última vez que se recibió dato
const unsigned long timeout_interval = 8000;  // Timeout en milisegundos

float temperatura = 0; // nuevo: variables para almacenar datos
float humedad = 0;
int distancia = 0;
bool falloDHT = false;
bool falloDistancia = false;

unsigned long buzzer_on_time = 0;          // para limitar duración del pitido
const unsigned long buzzer_duration = 1000; // 1 segundo de duración
bool buzzer_active = false;                // Estado del buzzer

const int segPins[7] = {2, 3, 4, 5, 6, 7, 8};

// Función para activar el buzzer por 1 segundo
void activarBuzzer() {
  digitalWrite(buzzer, HIGH);
  buzzer_on_time = millis() + buzzer_duration;
  buzzer_active = true;
}

//checksum
bool comprobarChecksum(String ConChecksum, String &dataSinChecksum) {
  int separador = ConChecksum.indexOf('|');

  if (separador == -1) return false;   // No hay checksum
  dataSinChecksum = ConChecksum.substring(0, separador);

  int recibido = ConChecksum.substring(separador + 1).toInt();
  int calculado = 0;
  for (int i = 0; i < dataSinChecksum.length(); i++) {
    calculado += dataSinChecksum[i];
  }
  return calculado == recibido;
}


const double G = 6.67430e-11;  // Gravitational constant (m^3 kg^-1 s^-2)
const double M = 5.97219e24;   // Mass of Earth (kg)
const double R_EARTH = 6371000;  // Radius of Earth (meters)
const double ALTITUDE = 400000;  // Altitude of satellite above Earth's surface (meters)
const double EARTH_ROTATION_RATE = 7.2921159e-5;  // Earth's rotational rate (radians/second)
const unsigned long MILLIS_BETWEEN_UPDATES = 1000; // Time in milliseconds between each orbit simulation update
const double  TIME_COMPRESSION = 90.0; // Time compression factor (90x)

// Variables Orbita
unsigned long nextUpdate; // Time in milliseconds when the next orbit simulation update should occur
double real_orbital_period;  // Real orbital period of the satellite (seconds)
double r;  // Total distance from Earth's center to satellite (meters)

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);

  pinMode(led_rec, OUTPUT);
  digitalWrite(led_rec, LOW);

  pinMode(led_fallo_datostemp, OUTPUT);
  digitalWrite(led_fallo_datostemp, LOW);

  pinMode(led_timeout, OUTPUT);
  digitalWrite(led_timeout, LOW);

  pinMode(buzzer, OUTPUT);
  digitalWrite(buzzer, LOW);

  last_message_time = millis(); // Inicializar temporizador

  nextUpdate = MILLIS_BETWEEN_UPDATES;
  r = R_EARTH + ALTITUDE;
  real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));
  // Display amb un 8
  for (int i = 0; i < 7; i++) {
    pinMode(segPins[i], OUTPUT);
  }

  // Nombre 8 -> tots els segments ON
  for (int i = 0; i < 7; i++) {
    digitalWrite(segPins[i], HIGH);  // càtode comú: HIGH encén el segment
  }
}

void loop() {
  String mensaje = "";
  if (Serial.available()){
    mensaje = Serial.readStringUntil('\n');
    mensaje.trim();
    mySerial.println(mensaje);
  }

  if (mySerial.available()) {
    String ConChecksum = mySerial.readStringUntil('\n');
    String data; // Leer hasta salto de línea
    Serial.println(ConChecksum); // O ConChecksum??

     if (!comprobarChecksum(ConChecksum, data)) {
        Serial.println("ERROR: checksum incorrecto, descartado");
        return;
     }
    last_message_time = millis(); // Actualizar tiempo de último mensaje

    //NUEVO Procesar códigos
    int fin = data.indexOf(' ', 0);
    int codigo = 0;
    int inicio = fin + 1;

    if (fin != -1) {
      codigo = data.substring(0, fin).toInt();
    } else {
      codigo = data.toInt();
    }

    if (codigo == 1) { // Código 1: Temperatura y Humedad
      fin = data.indexOf(' ', inicio);
      if (fin == -1) fin = data.length();
      String tempStr = data.substring(inicio, fin);
      String humStr = data.substring(fin + 1);
      temperatura = tempStr.toFloat();
      humedad = humStr.toFloat();
      falloDHT = false;

    

    digitalWrite(led_rec, HIGH);
    led_rec_on = true;
    led_rec_off_time = millis() + led_on_interval;
    digitalWrite(led_fallo_datostemp, LOW);

      digitalWrite(led_rec, HIGH);  // LED recepción datos on (igual que antes)
      led_rec_on = true;
      led_rec_off_time = millis() + led_on_interval;
      digitalWrite(led_fallo_datostemp, LOW);
    }
    
    else if (codigo == 2) { // Código 2: Distancia
      int fin2 = data.indexOf(' ', inicio);
      int angulo = 0;
      int dist = 0;
      if (fin2 != -1) {
        angulo = data.substring(inicio, fin2).toInt();
        distancia = data.substring(fin2 + 1).toInt();
      }
      
      // --- Detección de fallo del sensor ---
      if (distancia <= 0 || distancia > 400) {
        if (!falloDistancia) {
          falloDistancia = true;
          // Activar buzzer por 1 segundo usando la función auxiliar
          activarBuzzer();
        }
      } else {
        falloDistancia = false;
        // No apagar el buzzer aquí, se apagará automáticamente después de 1 segundo
      }
    }
    else if (codigo == 3) { // Código 3: Fallo DHT
        falloDHT = true;
        digitalWrite(led_fallo_datostemp, HIGH);
      }
    else {
      // Verificar palabra "Fallo" en la cadena recibida (case sensitive)
      if (data.indexOf("Fallo") >= 0) {
        digitalWrite(led_fallo_datostemp, HIGH);
      } else {
        digitalWrite(led_fallo_datostemp, LOW);
        // LED recepción datos ON y programar apagado
        digitalWrite(led_rec, HIGH);
        led_rec_on = true;
        led_rec_off_time = millis() + led_on_interval;
      }
    }
  }  // Cierre del if (mySerial.available())
  
  // Apagar LED recepción después del intervalo
  if (led_rec_on && millis() >= led_rec_off_time && digitalRead(led_fallo_datostemp) == LOW) {
    digitalWrite(led_rec, LOW);
    led_rec_on = false;
  }

  // Apagar buzzer después de 1 segundo, independientemente de la condición que lo activó
  if (buzzer_active && millis() >= buzzer_on_time) {
    digitalWrite(buzzer, LOW);
    buzzer_active = false;
  }

  // Controlar LED timeout: si pasaron más de 8 segundos sin datos
  if (millis() - last_message_time > timeout_interval) {
    digitalWrite(led_timeout, HIGH);
  } else {
    digitalWrite(led_timeout, LOW);
  }

  //Llama a la función de la orbita
  unsigned long currentTime = millis();
  if(currentTime>nextUpdate) {
    // Usar inclinación de 45 grados para que la órbita no sea ecuatorial
    // Esto hará que el groundtrack muestre curvas sinusoidales en lugar de una línea recta
    double inclination_deg = 45.0;  // Inclinación en grados
    double inclination_rad = inclination_deg * PI / 180.0;  // Convertir a radianes
    simulate_orbit(currentTime, inclination_rad, 1);  // ecef=1 para aplicar transformación ECEF
    nextUpdate = currentTime + MILLIS_BETWEEN_UPDATES;
  }
}

// FUNCIÓN SIMULACIÓN ORBITA
void simulate_orbit(unsigned long millis, double inclination, int ecef) {
    double time = (millis / 1000.0) * TIME_COMPRESSION;  // Real orbital time (en segundos)
    double angle = 2 * PI * (time / real_orbital_period);  // Angle in radians
    double x = r * cos(angle);  // X-coordinate (meters)
    double y = r * sin(angle) * cos(inclination);  // Y-coordinate (meters)
    double z = r * sin(angle) * sin(inclination);  // Z-coordinate (meters)

    // Aplicar transformación ECEF para considerar la rotación de la Tierra
    double theta = EARTH_ROTATION_RATE * time;
    double x_ecef = x * cos(theta) - y * sin(theta);
    double y_ecef = x * sin(theta) + y * cos(theta);
    double z_ecef = z;  // z no cambia en la transformación ECEF

    // Convertir coordenadas ECEF a latitud y longitud
    double hyp = sqrt(x_ecef * x_ecef + y_ecef * y_ecef);
    double lat_rad = atan2(z_ecef, hyp);
    double lon_rad = atan2(y_ecef, x_ecef);
    
    double lat = lat_rad * 180.0 / PI;  // Convertir a grados
    double lon = lon_rad * 180.0 / PI;  // Convertir a grados
    
    // Normalizar longitud a rango [-180, 180]
    while (lon > 180.0) lon -= 360.0;
    while (lon < -180.0) lon += 360.0;

    // Envia datos al python: código 4, latitud, longitud
    Serial.print("4 ");
    Serial.print(lat, 6);  // 6 decimales de precisión
    Serial.print(" ");
    Serial.println(lon, 6);
}
