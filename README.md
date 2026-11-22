# Plataforma IoT per a la monitorització ambiental en edificis patrimonials

Plataforma per a rebre, normalitzar i consultar telemetria ambiental de fonts heterogènies. Forma part del Treball de Fi de Grau *Disseny i implementació d'un sistema IoT per a la monitorització ambiental en edificis patrimonials* (ETSINF, UPV).

El node LoRaWAN que envia les dades reals està en un altre repositori: <URL del repositori del node>.

## Què fa

- Rep missatges per MQTT de dues fonts: una de pròpia (JSON) i ChirpStack v4 (CayenneLPP). Cada font té el seu transformador, que la passa a un format canònic inspirat en SenML.
- Guarda les lectures en PostgreSQL. Els missatges que no es poden interpretar es guarden com a descarts, amb el motiu.
- Gestiona el cicle de vida dels dispositius: sense provisionar, actiu, silenciós i retirat. Un procés periòdic marca com a silenciosos els que fa una hora que no envien res.
- Organitza els dispositius en espais jeràrquics (recinte, edifici, planta, sala, segons l'ontologia BOT del W3C), dins de projectes i grups de treball.
- Exposa una API REST amb autenticació JWT i dos rols, administrador i lector.
- Inclou una interfície web feta amb NiceGUI que consulta l'API.

## Arquitectura

| Servei | Funció | Port |
|---|---|---|
| `postgres` | Base de dades | 5432 (només `127.0.0.1`) |
| `mosquitto` | Broker MQTT, amb un pont cap al broker de la passarel·la | 1883 |
| `migrate` | Aplica les migracions d'Alembic i acaba | |
| `api` | API REST (FastAPI). Documentació a `/docs` | 8000 |
| `subscriber` | Rep els missatges MQTT, els transforma i els guarda | |
| `sweeper` | Marca com a silenciosos els dispositius sense senyal | |
| `gui` | Interfície web | 80 |
| `ntp` | Servidor d'hora per a la passarel·la, que no té rellotge propi | 123/udp |

Tots els serveis propis es construïxen a partir de la mateixa imatge.

## Posada en marxa

Cal tindre Docker amb Compose i [uv](https://docs.astral.sh/uv/).

1. Copia `.env.example` com a `.env` i omple els valors. Les contrasenyes i el secret del JWT es generen amb:
   ```
   uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Arranca la plataforma:
   ```
   docker compose up -d --build
   ```
3. Crea el primer administrador. La contrasenya es llig de l'entorn perquè no quede a l'historial del terminal:
   ```
   uv sync
   NEW_USER_PASSWORD='<contrasenya>' uv run python scripts/create_user.py admin --role admin
   ```
   En PowerShell, primer `$env:NEW_USER_PASSWORD = '<contrasenya>'` i després l'ordre.
4. Entra a http://localhost amb aquest usuari.

La direcció de la passarel·la per al pont MQTT està a `infra/mosquitto/config/mosquitto.conf`.

## Dades de demostració

`scripts/populate_demo.py` crea usuaris, grups, projectes i espais amb l'API, i envia per MQTT set dies d'històric de deu dispositius de les dues fonts, a més d'uns quants missatges erronis. Necessita `ADMIN_USERNAME`, `ADMIN_PASSWORD` i `DEMO_PASSWORD` a l'entorn:

```
uv run python scripts/populate_demo.py          # estructura i històric
uv run python scripts/populate_demo.py --live   # i després, un uplink cada 5 minuts
```

## Proves

Les proves creen una base de dades temporal en el PostgreSQL del compose, així que cal tindre'l en marxa:

```
uv run pytest --cov=plataforma_iot
```

## Estructura

```
src/plataforma_iot/
  api/          routers, esquemes, permisos i consultes
  domain/       format canònic, estats, rols i excepcions
  ingestion/    subscriptor, encaminador, transformadors i persistència
  models/       models de SQLAlchemy
  tasks/        procés periòdic dels dispositius silenciosos
src/gui/        interfície web
alembic/        migracions
infra/mosquitto broker MQTT
scripts/        creació d'usuaris i dades de prova
tests/
```

## Afegir una font nova

1. Escriu un transformador a `ingestion/transformers/` que implemente el protocol `Transformer` i torne un `CanonicalUplink`.
2. Afig-lo a la taula `SOURCES` de `ingestion/sources.py`, amb el filtre de topic i el prefix.

La resta de la plataforma no canvia.