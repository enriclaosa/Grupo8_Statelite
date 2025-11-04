#include <SoftwareSerial.h>
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11); // RX, TX 
#define LedVerd 6
unsigned long nextMillis1;
const unsigned long interval1 = 500;
unsigned long nextMillis2;
const unsigned long interval2 = 3000;
unsigned long nextTimeoutHT;
const unsigned long interval3 = 5000;
bool esperandoTimeout = false;
bool enviarDatos = true;
String mensaje;

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  dht.begin();
  pinMode(LedVerd, OUTPUT);
  nextMillis1 = millis() + interval1;
  nextMillis2 = millis() + interval2;
  nextTimeoutHT = millis() + interval3;
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (Serial.available() > 0) {
    mensaje = Serial.readStringUntil('\n');
  }
  if(mensaje == "Parar")
    enviarDatos = false;
  if(mensaje == "Reanudar")
    enviarDatos = true;
  if(enviarDatos == true){
    if (isnan(h) || isnan(t)){
      mySerial.println("Error al leer el sensor DHT11");
      if (!esperandoTimeout){
        esperandoTimeout = true
        nextTimeoutHT = millis() + interval3;
      }
    }
    else {
      if (millis() >= nextMillis2){
        esperandoTimeout = false;
        digitalWrite(LedVerd, HIGH);
        mySerial.print(h);
        mySerial.print(" ");
        mySerial.println(t);
        if (millis() >= nextMillis1){
          digitalWrite(LedVerd, LOW);
          nextMillis1 = millis() + interval1;
        }
        nextMillis2 = millis() + interval2;
      }
        
    }
    if(esperandoTimeout && (millis() >= nextTimeoutHT))
      mySerial.println("Fallo");
  }
}
