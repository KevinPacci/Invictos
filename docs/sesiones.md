# Resumen de Trabajo - Invictos

## Estado General
- Proyecto versionado en Git (remoto: https://github.com/KevinPacci/Invictos.git).
- Backend FastAPI ahora maneja usuarios con JWT (/auth/register, /auth/login, /auth/me).
- Cliente Flet incluye pantalla de autenticacion, caches y colas por usuario, textos centralizados en client/i18n.py y tema en client/ui/theme.py.
- invictos seed crea el usuario demo demo@example.com (demo1234) con apuestas de ejemplo.

## Dependencias clave
- Python 3.12 (la venv debe crearse con esta version).
- Paquetes adicionales: passlib[bcrypt], bcrypt==4.0.1, python-jose[cryptography], email-validator, python-dotenv.
- Nuevos modulos backend: backend/security.py (hash + JWT), backend/auth.py (OAuth2), backend/models.py ampliado con clases de usuario y token.

## Configuracion local
1. python -m venv .venv
2. .\.venv\Scripts\activate
3. pip install --upgrade pip
4. pip install -e .
5. Archivo .env sugerido:
   ```
   INVICTOS_JWT_SECRET=cambia-esta-clave
   INVICTOS_JWT_EXP_MIN=240
   INVICTOS_DB_URL=sqlite:///./invictos.db
   INVICTOS_API_URL=http://127.0.0.1:8000
   INVICTOS_CACHE_DIR=D:\Others\invictos\.cache
   INVICTOS_SYNC_INTERVAL=180
   ```
6. Cargar variables: .\load_env.ps1
7. Inicializar datos demo (despues de borrar invictos.db si existe): invictos seed

## Ejecucion diaria
- Backend: invictos backend --host 0.0.0.0 --port 8000
- Cliente: invictos client
- Usuario demo: demo@example.com / demo1234

## Cambios en el cliente
- Carpeta client/ui agrupa componentes reutilizables y el tema.
- client/app.py controla autenticacion y refresca metricas solo cuando los controles ya estan montados.
- client/cache.py guarda auth.json, cache de apuestas y cola por user_id en subcarpetas.
- client/api.py implementa login, registro y perfil, configurando el header Authorization con el token.

## Cambios en el backend
- backend/models.py: clases User*, Token, AuthResponse; Bet contiene user_id y relaciones.
- backend/main.py: rutas protegidas con get_current_user_id, nuevos endpoints de autenticacion.
- backend/crud.py: funciones para usuarios y consultas filtradas por user_id.
- backend/seed.py: crea usuario demo y apuestas asociadas.
- .gitignore: ignora .venv/, invictos.db y __pycache__/

## Scripts auxiliares
- load_env.ps1: cargar variables ejecutando .\load_env.ps1 (por defecto lee .env; acepta parametro -Path).

## Pendiente / proximos pasos
- Despliegue gratuito (Postgres Neon, backend Render, frontend web via GitHub Pages/Netlify).
- Redactar guia de uso (docs/USO.md) orientada a usuarios finales.
- Futuras integraciones con APIs externas (Sofascore u otras) para estadisticas/mentor de apuestas.

## Notas
- Para reiniciar la base local: eliminar invictos.db y ejecutar invictos seed.
- Siempre activar la venv y cargar .env antes de usar invictos backend/client/seed.
- Para compartir contexto basta con este archivo (docs/sesiones.md) en el repo.
