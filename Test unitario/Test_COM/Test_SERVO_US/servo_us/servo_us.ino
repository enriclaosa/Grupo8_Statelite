#include <Servo.h>

// Pines del sensor ultrasónico
const int trigPin = 9;
const int echoPin = 8;

// Pin del servo
const int servoPin = 3;

// Pin del joystick
const int joyX = A0;

// Crear objeto servo
Servo miServo;

void setup() {
  Serial.begin(9600);
  miServo.attach(servoPin);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  // --- Lectura del joystick ---
  int xValue = analogRead(joyX); // valor entre 0 y 1023

  // Convertir a ángulo (0° a 180°)
  int angulo = map(xValue, 0, 1023, 0, 180);
  miServo.write(angulo);

  // --- Medir distancia con el sensor ultrasónico ---
  long duracion;
  int distancia;

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duracion = pulseIn(echoPin, HIGH);
  distancia = duracion * 0.034 / 2; // velocidad del sonido 340 m/s → 0.034 cm/us

  // --- Mostrar datos en el monitor serial ---
  Serial.print("Angulo: ");
  Serial.print(angulo);
  Serial.print("°   |   Distancia: ");
  Serial.print(distancia);
  Serial.println(" cm");

}
