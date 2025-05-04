## Configuración y Ejecución

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-de-tu-repo>
    cd task-manager
    ```

2.  **Crear el archivo de configuración del entorno:**
    Crear un archivo `.env` en la raíz del proyecto (`task-manager/.env`) con el siguiente contenido.

    ```dotenv
    # Configuración de PostgreSQL
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_DB=postgres

    # Configuración de la Aplicación (Leída por Pydantic Settings)
    PROJECT_NAME="Task Manager API"
    API_V1_STR="/api/v1"
    DATABASE_URL="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}"

    # Configuración JWT (Leída por Pydantic Settings)
    SECRET_KEY="YOUR_VERY_SECRET_KEY_CHANGE_THIS"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```

3.  **Build y ejecutar la aplicación usando Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
    Este comando hará lo siguiente:
    *   Construirá la imagen Docker para la API basada en `api/Dockerfile`.
    *   Descargará la imagen de PostgreSQL.
    *   Creará e iniciará los contenedores para la base de datos (`db`) y la API (`api`).
    *   Cargará las variables de entorno desde el archivo `.env` en los contenedores.
    *   La API estará disponible en `http://localhost:8000`.

## Documentación de la API

Una vez que la aplicación está en ejecución, Swagger UI está disponible en:
[http://localhost:8000/docs](http://localhost:8000/docs)

Para probar los endpoints desde Swagger UI, se debe crear un usuario con el endpoint `/api/v1/users/` y luego autenticarse con el username y password del usuario creado.

## Stack Tecnológico

*   **Framework Web:** FastAPI
*   **Base de Datos:** PostgreSQL
*   **ORM:** SQLAlchemy
*   **Migraciones de Base de Datos:** Alembic
*   **Validación de Esquemas:** Pydantic
*   **Autenticación:** JWT (usando `python-jose` y `passlib[bcrypt]`)
*   **Configuración:** `pydantic-settings`, archivo `.env`
*   **Contenerización:** Docker, Docker Compose
*   **Servidor ASGI:** Uvicorn

## Decisiones Clave de Diseño y Notas de Implementación

*   **Autenticación:** Se implementó autenticación basada en JWT. Los usuarios inician sesión a través de `/api/v1/login/access-token` usando datos de formulario (`username`, `password`) para recibir un token de acceso. Este token debe incluirse en la cabecera `Authorization: Bearer <token>` para los endpoints protegidos.
*   **Seguridad de Contraseñas:** Las contraseñas de los usuarios nunca se almacenan en texto plano. Se hashean usando `bcrypt` a través de la biblioteca `passlib` antes de guardarlas en la base de datos (`crud_user.py`).
*   **Gestión de Configuración:** La configuración de la aplicación (URL de la base de datos, secrets JWT, etc.) se gestiona usando `BaseSettings` de Pydantic (`api/app/core/config.py`). La configuración se carga principalmente desde variables de entorno, las cuales son pobladas por Docker Compose leyendo el archivo `.env` raíz del proyecto (`env_file: .env` en `docker-compose.yml`). Las configuraciones definidas en `config.py` sin valores predeterminados son obligatorias y deben estar presentes en el entorno.
*   **Migraciones de Base de Datos:** Alembic está configurado (aunque la configuración inicial de migraciones podría necesitar hacerse vía `alembic init` y configuración) para gestionar los cambios en el esquema de la base de datos. Las definiciones de los modelos están en `api/app/models/`.
*   **Operaciones CRUD:** Las interacciones con la base de datos están organizadas en módulos CRUD (`api/app/crud/`) para cada modelo (ej., `crud_user.py`, `crud_team.py`, `crud_task.py`), promoviendo la separación de responsabilidades.
*   **Diseño de Esquemas y OpenAPI:** Los esquemas Pydantic (`api/app/schemas/`) definen las estructuras de datos para las solicitudes y respuestas de la API.
*   **Gestión de Dependencias:** Las dependencias de Python se listan en `api/requirements.txt`. Se fijaron versiones específicas para `passlib` (1.7.4) y `bcrypt` (3.2.0) para resolver problemas de compatibilidad en tiempo de ejecución.
*   **Dockerización:** La aplicación está contenerizada usando Docker. `docker-compose.yml` define los servicios `api` y `db`, gestiona la red, los volúmenes para la persistencia de datos y la carga de variables de entorno a través del archivo `.env` raíz.

## Desarrollo

*   **Ejecución de Migraciones:** Las migraciones de la base de datos típicamente se ejecutarían usando comandos como `docker-compose exec api alembic revision --autogenerate -m "Descripción"` y `docker-compose exec api alembic upgrade head`.
