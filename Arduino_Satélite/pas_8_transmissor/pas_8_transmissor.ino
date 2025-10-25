#include <SoftwareSerial.h>
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11); // RX, TX 
#define LedVerd 6
unsigned long nextMillis;
const unsigned long interval = 500;
unsigned long nextTimeoutHT;
bool esperandoTimeout = false;
bool enviarDatos = true;
String mensaje;

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  dht.begin();
  pinMode(6, OUTPUT);
  nextMillis = millis() + interval;
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (Serial.available() > 0) {
    mensaje = Serial.readString();
  }
  if(mensaje == "Parar")
    enviarDatos = false;
  if(mensaje == "Reanudar")
    enviarDatos = true;
  if(enviarDatos == true){
    if (isnan(h) || isnan(t)){
      mySerial.println("Error al leer el sensor DHT11");
      esperandoTimeout = true;
      nextTimeoutHT = millis() + 5000;
    }
    else {
      esperandoTimeout = false;
      digitalWrite(6, HIGH);
      mySerial.print(h);
      mySerial.print(" ");
      mySerial.println(t);
    if (millis() >= nextMillis){
      digitalWrite(6, LOW);
    }
    delay (3000);
    }
  }
}