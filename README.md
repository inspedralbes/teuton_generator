# server.py Resum

`server.py` engega un servidor web al **port 80** que permet mantenir actualitzat el fitxer config.yaml de Teuton a partir de les connexions dels clients (alumnes). 

# Exemple
El professor engega el servidor, en el directori on té els tests de Teuton (a on hi ha el 'start.rb', on hi ha d'haver el 'config.yaml').
```bash
sudo python3 server.py
```

Els alumnes hi fan **UNA** connexió amb 
```bash
$ curl "http://<SERVER_IP>/insert?name=John&email=john@example.com"
```

I automàticament s'actualitza el fitxer **config.yaml** amb les dades de l'alumne, i per tant, els tests de Teuton s'hi connectaran 

El professor, o els alumnes, poden obrir el navegador a 'http://<SERVER_IP>/list' i podran veure el llistat de tots els que ja estan donats d'alta

# Rutes

### 1. `/list`
- Mostra un resum del fitxer `config.yaml`.
- **Nota:** Les adreces IP estan ocultes per evitar que els alumnes les vegin fàcilment.

### 2. `/insert`
- Rep dos paràmetres: `nom` i `email`.
- Crea un nou registre al fitxer `config.yaml`, incloent-hi la IP detectada automàticament.
re dos paràmetres, nom i email, i que serviran per crear un nou registre juntament amb la IP al fitxer de config.yaml 

# Usage Instructions

## 1. Insert Data
- **Endpoint:** `/insert`
- **Parameters:** `name`, `email`
- **Example (curl):**
$ curl "http://<SERVER_IP>/insert?name=John&email=john@example.com"

## 2. List Users
- **Endpoint:** `/list`
- **Description:** Returns an HTML list of users sorted by name.
- **Example (browser):**
http://<SERVER_IP>/list

**Note:** IP address is automatically detected and used as a unique identifier.
