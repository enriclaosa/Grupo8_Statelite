#include <SoftwareSerial.h>
#include <DHT.h>
#include <Servo.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11); // RX, TX
#define LedVerd 6
unsigned long nextLedVerde;
const unsigned long intervalLedVerde = 500;
unsigned long nextHT;
unsigned long intervalHT = 3000;
unsigned long nextTimeoutHT;
unsigned long intervalTimeoutHT = 5000;
bool esperandoTimeout = false;
bool enviarDatos = true;

// Variables Servo
const int servoPin = 3;
const int trigPin = 9;
const int echoPin = 8;
Servo miServo;
int angulo = 90;
int direccion = 1;
bool controlPython = false;

// Variables joystick
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
float temperatura= 0;

const unsigned long intervaloDistancia = 200; // 200ms entre medidas
unsigned long nextMedidaDistancia = 0;
int ultimaDistanciaEnviada = -2;

// Medias tempratura
#define MAX_MEDIAS 10
float ultimasTemperaturas[MAX_MEDIAS]; // para las últimas 10 temperaturas
int indiceTemp = 0;                    // para que vuelva a 1 cuando este a 10 
int contadorTemp = 0;                   
float mediaTemperaturas = 0;

bool activarMediaEnArduino = false;

// Checksum 
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
  nextLedVerde = millis() + intervalLedVerde;
  nextHT = millis() + intervalHT;
  nextTimeoutHT = millis() + intervalTimeoutHT;
  pinMode(joystickXPin, INPUT);

  // Servo y ultrasónico
  miServo.attach(servoPin);
  miServo.write(angulo);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {  
  if (mySerial.available() > 0) {
    mensaje = mySerial.readStringUntil('\n');
    Serial.println(mensaje);
    mensaje.trim();
  
    if (mensaje == "Cambio") {          // Botón de la interfaz
      controlJoystick = !controlJoystick; // Alterna modo joystick
      controlPython = false;             // Python deja de mandar ángulos
    } else {
      int fin = mensaje.indexOf(' ', 0);
      int codigo = (fin == -1) ? mensaje.toInt() : mensaje.substring(0, fin).toInt();
      int inicio = fin + 1;
  
      if (codigo == 1) {
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
          controlPython = false; // Vuelve a barrido automático
      } else if (codigo == 3) {
        enviarDatos = false;
      }
    }
  }


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
  
  // Medir distancia con sensor ultrasónico
  if (ahora >= nextMedidaDistancia) {
    nextMedidaDistancia = ahora + intervaloDistancia;

    // disparar pulso
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);

    long tiempoPulso = pulseIn(echoPin, HIGH, 30000);
    if (tiempoPulso == 0) {
      distancia = -1;
      esperandoPulso = false;
    } else {
      distancia = tiempoPulso * 0.034 / 2;
    }
    if (distancia != ultimaDistanciaEnviada) {
      // Hacemos que se impriman las distancias detectadas en el serial monitor del satélite para facilitar pruebas
      Serial.print("Distancia  ");
      Serial.print(distancia);
      Serial.println(" cm");
      ultimaDistanciaEnviada = distancia;
    }
  }

  if(enviarDatos == true){
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (mensaje == "MEDIA_ON")
      activarMediaEnArduino = true; // Se calcula la media de las últimas 10 temmperaturas en el satélite
    else if (mensaje == "MEDIA_OFF")
      activarMediaEnArduino = false; // Se calcula la media de las últimas 10 temmperaturas en tierra (Python)

    if(activarMediaEnArduino){
      ultimasTemperaturas[indiceTemp] = t;
      indiceTemp = (indiceTemp + 1) % MAX_MEDIAS;
      if (contadorTemp < MAX_MEDIAS) contadorTemp++;

      float suma = 0;
      for (int i = 0; i < contadorTemp; i++) {
        suma += ultimasTemperaturas[i];
      }
      mediaTemperaturas = suma / contadorTemp;
    }

    if(mensaje == "Parar")
      enviarDatos = false;
    if(mensaje == "Reanudar")
      enviarDatos = true;
    
    if (millis() >= nextHT){ // Envío de datos
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
        String linea3= "3 " + String(mediaTemperaturas)+  " "; 
        mySerial.println(ConChecksum(linea3));
        nextLedVerde = millis() + intervalLedVerde;
      }
      nextHT = millis() + intervalHT;
    }
    if (millis() >= nextLedVerde)
      digitalWrite(LedVerd, LOW);
    if(esperandoTimeout && (millis() >= nextTimeoutHT)){
      mySerial.println("Fallo");
      esperandoTimeout = false;
    }
  }  
}
