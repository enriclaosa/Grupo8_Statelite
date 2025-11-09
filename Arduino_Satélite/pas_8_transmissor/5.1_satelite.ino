void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
}

void loop() {
  if(mySerial.available()){
    String comando = mySerial.readStringUntil('\n');
    comando.trim();
    int fin = comando.indexOf(':',0);// Troba la posició del primer : en la cadena
    int codigo = comando.substring(0, fin).toInt();// Extreu el codi (del principi fins a la posició espai) i el converteix a int
    int inicio = fin+1;// Marca on comença la informació després del codi
    if(codigo == 1){
      fin=comando.indexOf(':',inicio);// Busca si hi ha un altre : després del valor
      if (fin == -1) fin = comando.length();  // Si no hi ha un altre valor, agafa fins el final final
        intervalHT = comando.substring(inicio, fin).toInt() * 1000;// El valor que hi ha després de l'espai el passa a int i l'assigna a l'intervalHT + multiplica per 1000 per passar a milis
    }
    else if(codigo == 2){
//orientacio sensor distancia
    }
    else if(codigo == 3){
      enviarDatos = false;
    }
  }
}
