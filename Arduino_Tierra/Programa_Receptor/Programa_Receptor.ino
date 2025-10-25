#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)

const int led_rec = 8;                // LED rojo: indica recepción de datos
const int led_fallo_datostemp = 6;   // LED azul: indica fallo en datos de temperatura
const int led_timeout = 4;            // LED amarillo: indica timeout (5s sin datos)

const unsigned long led_on_interval = 500; // Duración que permanece encendido el LED de recepción
unsigned long led_rec_off_time = 0;        // Tiempo para apagar el LED de recepción
bool led_rec_on = false;

unsigned long last_message_time = 0;       // Última vez que se recibió dato
const unsigned long timeout_interval = 5000;  // Timeout en milisegundos

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);

  pinMode(led_rec, OUTPUT);
  digitalWrite(led_rec, LOW);

  pinMode(led_fallo_datostemp, OUTPUT);
  digitalWrite(led_fallo_datostemp, LOW);

  pinMode(led_timeout, OUTPUT);
  digitalWrite(led_timeout, LOW);

  last_message_time = millis(); // Inicializar temporizador
}

void loop() {
  if (mySerial.available()) {
    String data = mySerial.readString(); // Leer hasta salto de línea
    Serial.println(data);

    // LED recepción datos ON y programar apagado
    digitalWrite(led_rec, HIGH);
    led_rec_on = true;
    led_rec_off_time = millis() + led_on_interval;

    last_message_time = millis(); // Actualizar tiempo de último mensaje

    // Verificar palabra "Fallo" en la cadena recibida (case sensitive)
    if (data.indexOf("Fallo") >= 0) {
      digitalWrite(led_fallo_datostemp, HIGH);
    } else {
      digitalWrite(led_fallo_datostemp, LOW);
    }
  }

  // Apagar LED recepción después del intervalo
  if (led_rec_on && millis() >= led_rec_off_time) {
    digitalWrite(led_rec, LOW);
    led_rec_on = false;
  }

  // Controlar LED timeout: si pasaron más de 5 segundos sin datos
  if (millis() - last_message_time > timeout_interval) {
    digitalWrite(led_timeout, HIGH);
  } else {
    digitalWrite(led_timeout, LOW);
  }
}
