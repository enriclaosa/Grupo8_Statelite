#include <Servo.h>

// --- Pines ---
const int trigPin = 9;
const int echoPin = 8;
const int servoPin = 3;
const int joyX = A0;

// --- Variables ---
Servo miServo;
bool modoAutomatico = true;  // Cambia a true para barrido automático

int angulo = 90;     // Posición inicial del servo
int direccion = 1;   // Para el modo automático

// --- Temporizadores ---
unsigned long tiempoAnteriorServo = 0;
unsigned long tiempoAnteriorSensor = 0;
unsigned long tiempoAnteriorSerial = 0;

// --- Intervalos (ms) ---
const unsigned long intervaloServo = 15;     // velocidad del barrido automático
const unsigned long intervaloSensor = 100;   // frecuencia de medición
const unsigned long intervaloSerial = 800;   // frecuencia de impresión
const unsigned long intervaloJoy = 50;       // frecuencia de lectura del joystick

// --- Variables auxiliares ---
int distancia = 0;
unsigned long tiempoAnteriorJoy = 0;

void setup() {
  Serial.begin(9600);
  miServo.attach(servoPin);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  unsigned long tiempoActual = millis();

  // --- SERVO: modo automático o manual "sticky" ---
  if (modoAutomatico) {
    // Movimiento automático con rebote 0° ↔ 180°
    if (tiempoActual - tiempoAnteriorServo >= intervaloServo) {
      tiempoAnteriorServo = tiempoActual;
      angulo += direccion;
      if (angulo >= 180 || angulo <= 0) {
        direccion *= -1;
      }
      miServo.write(angulo);
    }

  } else {
    // Modo manual "sticky"
    if (tiempoActual - tiempoAnteriorJoy >= intervaloJoy) {
      tiempoAnteriorJoy = tiempoActual;
      int xValue = analogRead(joyX);

      // Zona muerta alrededor del centro
      int deadZone = 100;
      int centro = 512;

      if (xValue > centro + deadZone) {
        angulo++;
      } else if (xValue < centro - deadZone) {
        angulo--;
      }

      // Limitar ángulo entre 0 y 180
      angulo = constrain(angulo, 0, 180);
      miServo.write(angulo);
    }
  }

  // --- SENSOR ultrasónico ---
  if (tiempoActual - tiempoAnteriorSensor >= intervaloSensor) {
    tiempoAnteriorSensor = tiempoActual;
    distancia = medirDistancia();
  }

  // --- MONITOR SERIAL ---
  if (tiempoActual - tiempoAnteriorSerial >= intervaloSerial) {
    tiempoAnteriorSerial = tiempoActual;
    Serial.print("Angulo: ");
    Serial.print(angulo);
    Serial.print("° | Distancia: ");
    Serial.print(distancia);
    Serial.println(" cm");
  }
}

// --- Función para medir distancia ---
int medirDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracion = pulseIn(echoPin, HIGH, 25000); // Timeout 25 ms (~4 m)
  int distanciaCM = duracion * 0.034 / 2;
  return distanciaCM;
}
