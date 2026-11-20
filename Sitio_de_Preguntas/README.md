# Sitio de preguntas

Aplicación Flask para crear preguntas, responderlas y votar las respuestas.

## Funcionalidades

- Cada pregunta pertenece a una única categoría y puede tener varias etiquetas.
- Creación y modificación de preguntas.
- Respuestas de usuarios, ordenadas por puntaje (de mayor a menor).
- Votos positivos (`1`) y negativos (`-1`): cada usuario tiene un único voto por
  respuesta y el puntaje es un entero con la suma de todos los votos.
- API JSON para todas las operaciones.
- La creación de respuestas usa Factory Method: `Autor` delega en
  `FabricaConcretaRespuestas`, que elige la estrategia según el tipo.

No hay autenticación: el usuario se indica con `usuario_id` en el cuerpo JSON.
Para crear usuarios se puede usar `POST /api/usuarios`.

## Puesta en marcha

```bash
uv sync
uv run sitio-de-preguntas
```

La creación del esquema y las migraciones de la base de datos quedan a cargo del
módulo de base de datos (otro responsable).

Variables de entorno:

- `DATABASE_URL`: URL de SQLAlchemy (por defecto `sqlite:///app.db`).
- `SECRET_KEY`: clave de Flask (por defecto `development-only-key`).

## Rutas principales

`/health`, `/api/usuarios`, `/api/categorias`, `/api/etiquetas`,
`/api/preguntas` (admite filtros `categoria_id` y `etiqueta_id`),
`/api/preguntas/<id>` (incluye las respuestas ordenadas por puntaje),
`POST /api/preguntas/<id>/respuestas`, `POST /api/respuestas/<id>/votos`.

Ejemplo de creación de una pregunta:

```bash
curl -X POST http://127.0.0.1:5000/api/preguntas \
  -H 'Content-Type: application/json' \
  -d '{"usuario_id": 1, "titulo": "¿Cómo ordenar?", "contenido": "Detalle", "categoria_id": 1, "etiquetas_ids": [1]}'
```
