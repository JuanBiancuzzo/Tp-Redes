# Trabajo Practico N2: Software-Defined Networks
## Introduccion a los Sistemas Distribuidos (75.43)
## Grupo 2:
  * Rafael Berenguel
  * Juan Ignacio Biancuzzo
  * Agustina Fraccaro
  * Sofia Javes
  * Agustina Schmidt

Se desarrolla una topología con cantidad de switches variable, formando una cadena, con dos hosts de cada lado de la misma. Uno de los switches (cualquiera) actuará como Firewall con ciertas reglas de filtrado de paquetes. 

### Herramientas:
* Mininet
* POX
* Python 2.7
* iperf

Para correr el trabajo, primero se debe correr en una terminal el siguiente comando:

```bash
./run_pox.sh
```
En este archivo se encuentran los comandos necesarios para correr POX. Con esto, podremos configurar el Firewall cuando los switches se conecten.

Luego, debemos correr mininet, con el siguiente comando:
```bash
sudo ./run_mininet.sh
```
Esto correrá la topología mencionada anteriormente. Para cambiar la cantidad de switches de la topología, y también para cambiar cuál switch será el firewall, se debe editar el archivo ```config.json``` que se encuentra en la raíz del proyecto.

Luego, para correr iperf debemos correr dentro de mininet el comando: ```xterm <host>```. Debemos abrir dos terminales, para dos hosts distintos.

Luego, dentro de las terminales que se abren al correr el comando anterior, ejecutamos iperf:
* En una terminal, ejecutamos el servidor: 
```bash 
iperf -u -s -p <puerto>
```

* En la otra, ejecutamos el cliente:
```bash 
iperf -u -c <ip_servidor> -p <puerto_servidor>
```

Donde -u es para especificar que se comunicarán con UDP, -s especifica que es el servidor, -c que es el cliente y -p para el puerto.

Si se quiere que se comuniquen con TCP, debe eliminar el flag -u y agregar limitaciones:
```bash
   iperf -c <ip_servidor>  -p <puerto_servidor> -b <n> -n <n> -l <n> -t <n>
```
Donde:
* -b: limita ancho de banda (ej 200 bps)

* -n: limita cantidad de paquetes (ej 20 paquetes)

* -l: limita tamaño paquetes (ej 25 bytes)

* -t: limita tiempo de conexion (ej 5 seg)