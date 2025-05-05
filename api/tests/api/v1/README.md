# Unit tests

Este directorio contiene las pruebas unitarias para los endpoints de la versión 1 de la API.

## `test_tasks.py`

Este archivo contiene pruebas unitarias específicas para los endpoints relacionados con la gestión de tareas (`/api/v1/tasks`). Las pruebas cubren:

-   Creación de tareas.
-   Obtención de tareas (individuales y listas).
-   Actualización de tareas (marcar como completada, cambiar título/descripción/fecha de vencimiento).
-   Asignación de tareas a usuarios.
-   Eliminación lógica (`soft delete`) de tareas.
-   Validación de permisos (asegurarse de que los usuarios solo puedan interactuar con tareas de sus equipos).

## `test_teams.py`

Este archivo contiene pruebas unitarias específicas para los endpoints relacionados con la gestión de equipos (`/api/v1/teams`). Las pruebas cubren:

-   Creación de equipos.
-   Obtención de equipos (individuales y listas).
-   Actualización de la información del equipo (nombre, descripción).
-   Gestión de miembros:
    -   Añadir miembros al equipo.
    -   Eliminar miembros del equipo.
    -   Listar miembros del equipo (cuando se implemente el endpoint).
-   Eliminación lógica (`soft delete`) de equipos.
-   Validación de permisos (asegurarse de que solo los miembros del equipo puedan realizar acciones).

## Ejecución de las Pruebas

Estas pruebas se ejecutan automáticamente como parte del conjunto de pruebas completo utilizando `pytest`. Están diseñadas para probar cada endpoint de forma aislada, utilizando una base de datos de prueba y datos simulados definidos en `conftest.py`.

Comando para ejecutar las pruebas:
docker-compose run --rm api python -m pytest tests/
