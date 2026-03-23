# Diagnóstico Docker HTTP - 2026-03-23

## Contexto

Se revisó el comportamiento de respuestas GET sobre los puertos 3000 y 8081 dentro del stack Docker Compose del repo.

## Hallazgos

1. El servicio `web` en `docker-compose.yml` no estaba sirviendo contenido HTTP.
2. El contenedor `web` usaba `sleep infinity`, por lo que el puerto 3000 quedaba publicado pero sin proceso escuchando.
3. El contenedor `web` tampoco montaba `apps/web`, así que aunque existía frontend estático en el repo, Compose no lo exponía.
4. Keycloak sí estaba configurado para levantar en perfil `full`, pero el bootstrap realizaba una única validación demasiado temprana.
5. En un reporte previo el chequeo devolvió `HTTP 000000`, lo que mezcla un timeout real con un bug de formato del script al concatenar dos salidas `000`.
6. En reportes posteriores Keycloak respondió `HTTP 302`, consistente con un arranque correcto y redirección esperada del root.

## Evidencia

- `web` con placeholder sin servidor HTTP: `docker-compose.yml`.
- Frontend estático existente y ejecutable fuera de Compose: `apps/web/README.md`.
- Falla temprana de Keycloak: `docs/bootstrap_run_2026-03-23_00-16-21.txt`.
- Respuesta correcta posterior de Keycloak: `docs/bootstrap_run_2026-03-23_00-28-03.txt`.

## Correcciones aplicadas

1. `web` ahora monta `./apps/web:/web` y ejecuta un servidor estático Node en el puerto 3000.
2. Se agregó `apps/web/server.js` para servir `index.html`, `app.js` y `styles.css` sin dependencias externas.
3. Se habilitó `KC_HEALTH_ENABLED=true` en Keycloak.
4. `scripts/bootstrap.sh` ahora usa reintentos HTTP para evitar falsos negativos durante el warm-up de Keycloak.
5. `scripts/bootstrap.sh` ahora verifica también `web_ui:3000`.
6. Se corrigió el formato del código HTTP para evitar el falso valor `000000`.

## Conclusión

- Problema en `3000`: configuración incorrecta del servicio `web`.
- Problema en `8081`: ventana de readiness y chequeo demasiado agresivo, no una falla estructural de Compose.