#include <SoftwareSerial.h>
#include <DHT.h>
#include <Servo.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11); // RX, TX
#define LedVerd 6
unsigned long nextLedRojo;
const unsigned long intervalLedRojo = 500;
unsigned long nextHT;
unsigned long intervalHT = 3000;
unsigned long nextTimeoutHT;
unsigned long intervalTimeoutHT = 5000;
bool esperandoTimeout = false;
bool enviarDatos = true;

// --- Variables Servo ---
const int servoPin = 3;
const int trigPin = 9;
const int echoPin = 8;

Servo miServo;
int angulo = 90;
int direccion = 1;
bool controlPython = false;
const int joystickXPin = A0;        // pin del eje X del joystick
const int joystickDeadzone = 40;    // zona muerta para evitar jitter
const int joystickMinPaso = 2;      // cambio mínimo de ángulo para mover
bool controlJoystick = false;       // modo joystick
int ultimoAnguloJoystick = 90;      // último ángulo fijado por joystick (sticky)

unsigned long ultimoBarrido = 0;
const int pasoBarrido = 1;
const unsigned long intervaloBarrido = 15;

unsigned long tiempoInicioPulso = 0;
bool esperandoPulso = false;
long duracion = 0;
int distancia = 0;

const unsigned long intervaloDistancia = 200; // 200ms entre medidas
unsigned long nextMedidaDistancia = 0;
int ultimaDistanciaEnviada = -2;

const int segPins[7] = {2, 3, 4, 5, 6, 7, 8};

//cheksum 
String ConChecksum(String mensaje) {
  int checksum = 0;
  for (int i = 0; i < mensaje.length(); i++) {
    checksum += mensaje[i];
  }
  return mensaje + "|" + String(checksum);
}

String mensaje;

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  dht.begin();
  pinMode(LedVerd, OUTPUT);
  nextLedRojo = millis() + intervalLedRojo;
  nextHT = millis() + intervalHT;
  nextTimeoutHT = millis() + intervalTimeoutHT;
  pinMode(joystickXPin, INPUT);

  // Servo y ultrasónico
  miServo.attach(servoPin);
  miServo.write(angulo);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  for (int i = 0; i < 7; i++) {
    pinMode(segPins[i], OUTPUT);
  }

  // Nombre 8 -> tots els segments ON
  for (int i = 0; i < 7; i++) {
    digitalWrite(segPins[i], LOW);   // ànode comú: LOW encén el segment
  }
}

void loop() {  
    if (mySerial.available() > 0) {
        mensaje = mySerial.readStringUntil('\n');
        Serial.println(mensaje);
        mensaje.trim();
      
        if (mensaje == "Cambio") {          // botón de la interfaz
          controlJoystick = !controlJoystick; // alterna modo joystick
          controlPython = false;             // Python deja de mandar ángulos
        } else {
          int fin = mensaje.indexOf(' ', 0);
          int codigo = (fin == -1) ? mensaje.toInt() : mensaje.substring(0, fin).toInt();
          int inicio = fin + 1;
      
          if (codigo == 4) {
            fin = mensaje.indexOf(' ', inicio);
            if (fin == -1) fin = mensaje.length();
            intervalHT = mensaje.substring(inicio, fin).toInt() * 1000;
          } else if (codigo == 2) {
            int nuevoAngulo = mensaje.substring(inicio).toInt();
            if (nuevoAngulo >= 0 && nuevoAngulo <= 180) {
              angulo = nuevoAngulo;
              miServo.write(angulo);
              controlPython = true;  // Python toma control
            }
            if (nuevoAngulo == -1)
              controlPython = false;
          } else if (codigo == 3) {
            enviarDatos = false;
          }
        }
      }


// --- Barrido automático del servo si Python no controla ---
if (controlJoystick) {
    int lectura = analogRead(joystickXPin);
    int delta = abs(lectura - 512);

    if (delta > joystickDeadzone) {
      int nuevoAngulo = map(lectura, 0, 1023, 0, 180);
      // sólo mover si el cambio es apreciable para evitar jitter
      if (abs(nuevoAngulo - ultimoAnguloJoystick) >= joystickMinPaso) {
        ultimoAnguloJoystick = nuevoAngulo;
        angulo = nuevoAngulo;
        miServo.write(angulo);
      }
    }
    // sticky: si el joystick vuelve a la zona muerta, el servo se queda en último ángulo
  } else if (!controlPython) {
    // barrido automático
    if (millis() - ultimoBarrido >= intervaloBarrido) {
      angulo += direccion * pasoBarrido;
      if (angulo >= 180) { angulo = 180; direccion = -1; }
      if (angulo <= 0)   { angulo = 0;   direccion = 1; }
      miServo.write(angulo);
      ultimoBarrido = millis();
    }
  }
  // (si controlPython es true, ya se mueve con los comandos de Python)
   
  unsigned long ahora = millis();

    // Medir distancia sin bloquear
    if (ahora >= nextMedidaDistancia) {
        nextMedidaDistancia = ahora + intervaloDistancia;

        // disparar pulso
        digitalWrite(trigPin, LOW);
        delayMicroseconds(2);
        digitalWrite(trigPin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trigPin, LOW);

        // medir pulso manualmente con timeout
        /*unsigned long startTime = micros();
        while (digitalRead(echoPin) == LOW && micros() - startTime < 30000) ; // esperar subida
        unsigned long tiempoPulso = 0;
        if (digitalRead(echoPin) == HIGH) {
            unsigned long pulsoInicio = micros();
            while (digitalRead(echoPin) == HIGH && micros() - pulsoInicio < 30000) ; // esperar bajada
            tiempoPulso = micros() - pulsoInicio;
        }*/
        long tiempoPulso = pulseIn(echoPin, HIGH, 30000);
        if (tiempoPulso == 0) {
            distancia = -1;
            esperandoPulso = false;
        } else {
            distancia = tiempoPulso * 0.034 / 2;
        }
         if (distancia != ultimaDistanciaEnviada) {
            Serial.print("Distancia  ");
            Serial.print(distancia);
            Serial.println(" cm");
            ultimaDistanciaEnviada = distancia;
         }
    }
    if(mensaje == "Parar")
    enviarDatos = false;
    if(mensaje == "Reanudar")
    enviarDatos = true;
    if(enviarDatos == true){
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (millis() >= nextHT){
        if (isnan(h) || isnan(t)){
        if (!esperandoTimeout){
            esperandoTimeout = true;
            nextTimeoutHT = millis() + intervalTimeoutHT;
        }
        }
        else {
        esperandoTimeout = false;
        digitalWrite(LedVerd, HIGH);
        String linea1 = "1 " + String(h) + " " + String(t) + " ";
        mySerial.println(ConChecksum(linea1));
        String linea2 = "2 " + String(angulo) + " " + String(distancia) + " ";
        mySerial.println(ConChecksum(linea2));

        nextLedRojo = millis() + intervalLedRojo;
        }
        nextHT = millis() + intervalHT;
    }
    if (millis() >= nextLedRojo)
        digitalWrite(LedVerd, LOW);
    if(esperandoTimeout && (millis() >= nextTimeoutHT)){
        mySerial.println("Fallo");
        esperandoTimeout = false;
        }
    }  
}

