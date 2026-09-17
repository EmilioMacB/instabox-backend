# InstaBox Backend API

Servicio backend en la nube desarrollado con FastAPI, PostgreSQL (Amazon RDS) y Amazon S3 para la gestión de estaciones de fotos de eventos sociales, generación automatizada de composiciones estilo Polaroid y empaquetado en archivos ZIP descargables.

## Arquitectura

* **Cómputo:** Amazon EC2 (Amazon Linux 2023) ejecutando FastAPI y Uvicorn en el puerto 8000.
* **Seguridad e Identidad:** Perfil IAM `LabInstanceProfile` asociado a EC2 para delegar permisos hacia S3 y Secrets Manager sin credenciales hardcodeadas.
* **Gestión de Secretos:** AWS Secrets Manager almacena la cadena de conexión de base de datos; la aplicación la consume en tiempo de ejecución.
* **Base de Datos:** Amazon RDS (PostgreSQL) con tablas `events` y `photos` vinculadas por llave foránea en cascada.
* **Almacenamiento de Objetos:** Amazon S3 para fotos reducidas (`pictures/`) y marcos procesados (`polaroids/`).

## Endpoints

* `POST /events`: Registra un evento nuevo y retorna su `event_id`.
* `POST /upload`: Recibe foto, mensaje y `event_id`. Redimensiona a 128x128 px, genera el marco Polaroid con texto, almacena ambos en S3 y guarda los metadatos en RDS.
* `GET /events/{event_id}`: Consulta RDS y retorna la información del evento junto con el conteo total de fotos asociadas.
* `POST /finish`: Consulta las polaroids del evento en RDS, las descarga de S3, las comprime en un `.zip` en memoria y retorna el archivo descargable.

## Ejecución en EC2

```bash
# Clonar y entrar al proyecto
git clone <URL_DEL_REPOSITORIO>
cd instabox-backend

# Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Inicializar tablas en RDS
python init_db.py

# Iniciar servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000

## Limpieza de Recursos (Teardown)

El proyecto incluye el script automatizado `teardown.sh` para destruir de forma ordenada y permanente toda la infraestructura aprovisionada en AWS (S3, RDS, Secrets Manager y EC2), evitando consumos y cargos posteriores.

### Ejecución del script

Conéctate a la instancia o ejecuta desde un entorno con AWS CLI autenticado:

```bash
# Desactivar paginador de AWS CLI para evitar pausas interactivas
export AWS_PAGER=""

# Otorgar permisos de ejecución y correr el script
chmod +x teardown.sh
./teardown.sh

