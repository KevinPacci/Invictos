# Arquitectura propuesta

## Objetivos
- Convertir el tracker de apuestas en una aplicacion de escritorio multiplataforma.
- Permitir sincronizacion entre dispositivos mediante un backend accesible por HTTP.
- Mantener la experiencia rica (resumen mensual, breakdown diario, parlays) e introducir una UI mas clara y escalable.

## Componentes

### Servicio backend (`backend/`)
- **Framework**: FastAPI para exponer una API REST.
- **Persistencia**: SQLite mediante SQLModel (ORM ligero sobre SQLAlchemy).
- **Modelos**:
  - `Bet`: id UUID, fecha, tipo (`single|parlay`), detalle, stake, odds, cashout opcional, outcome (`acertada|fallida|pendiente`), timestamps.
  - `ParlayLeg`: id UUID, bet_id FK, detalle, cuota.
- **Sincronizacion**:
  - Endpoint `GET /sync?since=` devuelve apuestas modificadas desde la fecha indicada.
  - Operaciones CRUD (`POST /bets`, `PATCH /bets/{id}`, `DELETE /bets/{id}`) aplican `updated_at`.
  - Control de versiones mediante campo `updated_at` con precision ISO.
- **Autenticacion**: placeholder para API key simple (configurable por variable de entorno) para poder desplegar a un hosting barato cuando se necesite.

### Aplicacion de escritorio (`client/`)
- **Framework**: Flet (basado en Flutter, empaquetable a Windows/macOS/Linux, y apps moviles).
- **Estado local**: cache en disco (`app_state.json`) para arrancar offline y aplicar replays cuando la API no responda.
- **Sincronizacion**:
  - Sincroniza cambios locales en cola; reintenta cuando vuelve la conectividad.
  - Descarga delta usando `GET /sync` al iniciar y cada cierto intervalo.
- **UI**:
  - Dashboard con tarjetas de metricas globales y del mes actual.
  - Vista diaria editable con tarjetas y controles inline.
  - Editor lateral para crear apuestas single/parlay (con calculo automatico de cuota compuesta).
  - Tipografia base `Inter`/`SF Pro`, paleta neutra + acentos neon similares al diseno original pero mejor jerarquia.
  - Layout responsive con navegacion tipo tabs (`Resumen`, `Diario`, `Historial`).
  - Indicadores visuales consistentes (pildoras para tipo, badges de estado, barras de progreso para yield).

## Flujo de datos
1. El cliente arranca, carga cache local y solicita `/sync?since=<timestamp_cache>`.
2. El backend devuelve apuestas nuevas o modificadas; el cliente mezcla con el estado local.
3. Acciones del usuario (crear, editar, eliminar) se reflejan en el estado local y se envian como mutaciones a la API.
4. En caso de fallo de red, las mutaciones quedan en cola `pending_ops.json` y se reintentan periodicamente.

## Distribucion
- `pyproject.toml` unifica dependencias (FastAPI, Flet, SQLModel, Typer para CLI).
- Script `invictos.py` con CLI (p.ej. `python invictos.py backend` / `python invictos.py app`).
- Instrucciones para empaquetar el cliente (`flet pack`) y, opcionalmente, desplegar el backend (Railway/Fly.io/Render).

