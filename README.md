# Trabajo Practico N1: File Transfer

## Introduccion a los Sistemas Distribuidos (75.43)

## Ejecutar

### Como Cliente:

**Upload:**
Envia un archivo al servidor para ser guardado con el nombre asignado:
``` bash
> python upload -h
usage: upload [-h] [ -v | -q ] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME]
```

Donde los argumentos opcionales son:
```
-h, --help | muestra este mensaje de ayuda (como ejecutar con los comandos) y sale
-v, --verbose | aumento de la salida de mensajes del logger
-q, --quiet | disminucion de la salida de mensajes del logger
-H, host | direccion IP del servidor
-p, --port | puerto del servidor
-s, --src | ruta de archivo a cargar
-n, --name | nombre de archivo
```

**Download:**
Descarga un archivo especificado desde el servidor
``` bash
> python download -h
usage: download [-h] [ -v | -q ] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]
```

Donde los argumentos opcionales coinciden con los anteriores excepto por:
```
-d, --dst | ruta de destino del archivo a descargar
```

### Como Servidor:
Provee el servicio de almacenamiento y descarga de archivos
``` bash
> python start-server -h
usage: start-server [-h] [ -v | -q ] [-H ADDR] [-p PORT] [-s DIRPATH]
```

Donde los argumentos opcionales son:
```
-h, --help | muestra este mensaje de ayuda (como ejecutar con los comandos) y sale
-v, --verbose | aumento de la salida de mensajes del logger
-q, --quiet | disminucion de la salida de mensajes del logger
-H, host | direccion IP del servidor
-p, --port | puerto del servidor
-s, --storage | ruta de alamcenamiento del archivo
```


## Grupo 2:
  * Rafael Berenguel
  * Juan Ignacio Biancuzzo
  * Agustina Fraccaro
  * Sofia Javes
  * Agustina Schmidt
