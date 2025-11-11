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

unsigned long ultimoBarrido = 0;
const int pasoBarrido = 1;
const unsigned long intervaloBarrido = 15;

unsigned long tiempoInicioPulso = 0;
bool esperandoPulso = false;
long duracion = 0;
int distancia = 0;

String mensaje;

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  dht.begin();
  pinMode(LedVerd, OUTPUT);
  nextLedRojo = millis() + intervalLedRojo;
  nextHT = millis() + intervalHT;
  nextTimeoutHT = millis() + intervalTimeoutHT;

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

    int fin = mensaje.indexOf(' ',0);// Troba la posició del primer ' ' en la cadena
    int codigo = mensaje.substring(0, fin).toInt();// Extreu el codi (del principi fins a la posició espai) i el converteix a int
    int inicio = fin+1;// Marca on comença la informació després del codi
    
    if(codigo == 4){
      fin=mensaje.indexOf(' ',inicio);// Busca si hi ha un altre : després del valor
      if (fin == -1) fin = mensaje.length();  // Si no hi ha un altre valor, agafa fins el final final
        intervalHT = mensaje.substring(inicio, fin).toInt() * 1000;// El valor que hi ha després de l'espai el passa a int i l'assigna a l'intervalHT + multiplica per 1000 per passar a milis
    }
    else if(codigo == 2){
      int nuevoAngulo = mensaje.substring(inicio).toInt();
      if (nuevoAngulo >= 0 && nuevoAngulo <= 180) {
        angulo = nuevoAngulo;
        miServo.write(angulo);
        controlPython = true; // Python toma control
      }
    }
    else if(codigo == 3){
      enviarDatos = false;
    }
}
// --- Barrido automático del servo si Python no controla ---
  if (!controlPython) {
    if (millis() - ultimoBarrido >= intervaloBarrido) {
      angulo += direccion * pasoBarrido;
      if (angulo >= 180) {
        angulo = 180;
        direccion = -1;
      }
      if (angulo <= 0) {
        angulo = 0;
        direccion = 1;
      }
      miServo.write(angulo);
      ultimoBarrido = millis();
    }
  }
  if (!esperandoPulso) {
    digitalWrite(trigPin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigPin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    tiempoInicioPulso = micros();
    esperandoPulso = true;
  } else {
    if (digitalRead(echoPin) == HIGH) {
      duracion = micros() - tiempoInicioPulso;
      distancia = duracion * 0.034 / 2;
      esperandoPulso = false;
    } else if (micros() - tiempoInicioPulso > 30000) {
      // timeout si no llega eco
      distancia = -1;
      esperandoPulso = false;
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
        mySerial.print("1 ");
        mySerial.print(h);
        mySerial.print(" ");
        mySerial.println(t);
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
