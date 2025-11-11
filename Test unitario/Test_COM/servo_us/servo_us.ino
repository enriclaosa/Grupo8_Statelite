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

// Servo en manual o automatico
bool servo_M_A = false;

void setup() {
  Serial.begin(9600);
  miServo.attach(servoPin);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {

  if(data.indexOf("Cambio") >= 0){
    if(servo_M_A){
      servo_M_A = False;
    }
    if(!servo_M_A){
      servo_M_A = True;
    }
  }
  
  // --- Lectura del joystick ---
  if(sevro_M_A){
    int xValue = analogRead(joyX); // valor entre 0 y 1023

  // Convertir a ángulo (0° a 180°)
    int angulo = map(xValue, 0, 1023, 0, 180);
    miServo.write(angulo);
  }

  if(!servo_M_A){
      miServo.write(angulo);
  // Cambiar dirección al llegar a los extremos
    angulo += direccion;
    if (angulo >= 180) {
      direccion = -1;
    }   
    else if (angulo <= 0) {
      direccion = 1;
    }
  }
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
