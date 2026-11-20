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

El esquema de la base de datos se crea con Alembic a partir de los modelos de
SQLAlchemy:

```bash
uv run alembic -c migrations/alembic.ini upgrade head
```

Alembic usa la misma URL que la aplicación: `DATABASE_URL` si está definida, o
`sqlite:///app.db` dentro de `instance/` por defecto. Para revertir el esquema:
`uv run alembic -c migrations/alembic.ini downgrade base`.

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

## Deuda técnica detectada (Issue #3)

La comparación con el modelo conceptual UML (`diagramaCompleto.png` /
`Proyecto taller.asta`) mostró diferencias que no se corrigen en este Issue
porque requieren modificar los modelos actuales y corresponden a otros Issues:

- Falta representar el rol de administrador (`Admin`).
- Falta el atributo de respuesta aceptada (`accepted`) y la asociación
  `RTA Elegida` (multiplicidad `0..1`).
- Falta el atributo `descripcion` en `Etiqueta`.

La migración inicial refleja únicamente los modelos vigentes; estas diferencias
quedan documentadas para resolverse en Issues separados.
