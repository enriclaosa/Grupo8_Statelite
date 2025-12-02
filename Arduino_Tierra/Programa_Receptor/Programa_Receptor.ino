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

// Medias tempratura
#define MAX_MEDIAS 10
float ultimasTemperaturas[MAX_MEDIAS]; // para las últimas 10 temperaturas
int indiceTemp = 0;                    // para que vuelva a 1 cuando este a 10 
int contadorTemp = 0;                   
float mediaTemperaturas = 0;

bool activarMediaEnArduino = true;


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

    //Media teperaturas!
    if (mensaje == "MEDIA_ON") {
        activarMediaEnArduino = true;
    } 
    else if (mensaje == "MEDIA_OFF") {
        activarMediaEnArduino = false;
    }
    if(activarMediaEnArduino){
      ultimasTemperaturas[indiceTemp] = temperatura;
      indiceTemp = (indiceTemp + 1) % MAX_MEDIAS;
      if (contadorTemp < MAX_MEDIAS) contadorTemp++;

      float suma = 0;
      for (int i = 0; i < contadorTemp; i++) {
          suma += ultimasTemperaturas[i];
      }
      mediaTemperaturas = suma / contadorTemp;
      Serial.print("Temperatura: "); Serial.print(temperatura);
      Serial.print(" °C, Media últimas "); Serial.print(contadorTemp);
      Serial.print(": "); Serial.println(mediaTemperaturas);
      }

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
    }
  
    // --- Detección de fallo del sensor ---
      if (distancia <= 0 || distancia > 400) {
        if (!falloDistancia) {
          falloDistancia = true;
          digitalWrite(buzzer, HIGH);
          buzzer_on_time = millis() + buzzer_duration;
        }
       else {
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
}
}
