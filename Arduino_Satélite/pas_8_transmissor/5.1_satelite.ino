void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
}

void loop() {
  if(mySerial.available()){
    String comando = mySerial.readStringUntil('\n');
    comando.trim();
    int fin = comando.indexOf(' ',0);// Troba la posició del primer espai en la cadena
    int codigo = comando.substring(0, fin).toInt();// Extreu el codi (del principi fins a la posició espai) i el converteix a int
    int inicio = fin+1;// Marca on comença la informació després del codi
    if(codigo == 1){
      fin=comando.indexOf(' ',inicio);// Busca si hi ha un altre espai després del valor
      intervalHT = comando.substring(inicio, fin).toInt();// El valor que hi ha després de l'espai el passa a int i l'assigna a l'intervalHT
    }
    else if(codigo == 2){
//orientacio sensor distancia
    }
    else if(codigo == 3){
      enviarDatos == false;
    }
  }
}
