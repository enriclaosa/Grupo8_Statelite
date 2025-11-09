#include <SoftwareSerial.h>
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11); // RX, TX 
#define LedVerd 6
unsigned long nextLedRojo;
const unsigned long intervalLedRojo = 500;
unsigned long nextHT;
const unsigned long intervalHT = 3000;
unsigned long nextTimeoutHT;
const unsigned long intervalTimeoutHT = 5000;
bool esperandoTimeout = false;
bool enviarDatos = true;
String mensaje;

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  dht.begin();
  pinMode(LedVerd, OUTPUT);
  nextLedRojo = millis() + intervalLedRojo;
  nextHT = millis() + intervalHT;
  nextTimeoutHT = millis() + intervalTimeoutHT;
}

void loop() {  
if (mySerial.available() > 0) {
  mensaje = mySerial.readStringUntil('\n');
  Serial.println(mensaje);
  mensaje.trim();
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
