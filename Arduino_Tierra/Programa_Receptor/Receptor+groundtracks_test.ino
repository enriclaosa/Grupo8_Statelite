#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)

const int led_rec = 8;                // LED rojo: indica recepción de datos
const int led_fallo_datostemp = 6;   // LED azul: indica fallo en datos de temperatura
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
const unsigned long buzzer_duration = 500; // 0.5 s

// Constantes Orbitas
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

  // Variables Orbita
  nextUpdate = MILLIS_BETWEEN_UPDATES;
  r = R_EARTH + ALTITUDE;
  real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));
}

void loop() {
  if (Serial.available()) {
    String mensaje = Serial.readStringUntil('\n');
    mensaje.trim();
    mySerial.println(mensaje);
  }

  if (mySerial.available()) {
    String data = mySerial.readStringUntil('\n'); // Leer hasta salto de línea
    Serial.println(data);

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
          digitalWrite(buzzer, HIGH);
          buzzer_on_time = millis() + buzzer_duration;
        }
      } else {
        falloDistancia = false;
        digitalWrite(buzzer, LOW);
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
  }
  // Apagar LED recepción después del intervalo
  if (led_rec_on && millis() >= led_rec_off_time && digitalRead(led_fallo_datostemp) == LOW) {
    digitalWrite(led_rec, LOW);
    led_rec_on = false;
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
    simulate_orbit(currentTime, 0, 0);
    nextUpdate = currentTime + MILLIS_BETWEEN_UPDATES;
  }
}


// FUNCIÓN SIMULACIÓN ORBITA
void simulate_orbit(unsigned long millis, double inclination, int ecef) {
    double time = (millis / 1000) * TIME_COMPRESSION;  // Real orbital time
    double angle = 2 * PI * (time / real_orbital_period);  // Angle in radians
    double x = r * cos(angle);  // X-coordinate (meters)
    double y = r * sin(angle) * cos(inclination);  // Y-coordinate (meters)
    double z = r * sin(angle) * sin(inclination);  // Z-coordinate (meters)

    if (ecef) {
        double theta = EARTH_ROTATION_RATE * time;
        double x_ecef = x * cos(theta) - y * sin(theta);
        double y_ecef = x * sin(theta) + y * cos(theta);
        x = x_ecef;
        y = y_ecef;
    }

    // Envia datos al python
    Serial.print("4 ");
    Serial.print(x);
    Serial.print(" ");
    Serial.print(y);
    Serial.print(" ");
    Serial.println(z);
}