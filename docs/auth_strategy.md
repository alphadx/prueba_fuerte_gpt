# Estrategia de control de usuarios e identidad (SSO)

## Decisión

Sí, se considera **SSO con Keycloak** desde esta etapa para evitar acoplar autenticación al API y facilitar crecimiento multi-canal.

## Objetivos

- Centralizar autenticación (usuarios internos y potenciales usuarios externos).
- Delegar login/OIDC a un IdP estándar.
- Mantener autorización de negocio (roles ERP) en la aplicación.

## Modelo propuesto

1. **Identidad (IdP):** Keycloak.
2. **Autenticación:** OIDC/OAuth2 (Authorization Code + PKCE para web).
3. **Autorización de negocio:** roles del ERP (`admin`, `cajero`, `bodega`, `rrhh`) mapeados desde claims del token.
4. **API Gateway futura (opcional):** validación JWT en borde.

## Separación de responsabilidades

- Keycloak gestiona:
  - login,
  - credenciales,
  - MFA (si se activa),
  - federación futura (Google/Microsoft/AD).
- ERP API gestiona:
  - permisos de dominio,
  - políticas por sucursal,
  - auditoría funcional.

## Configuración base esperada

- Realm: `erp-barrio`.
- Client backend: `erp-api` (bearer-only o confidential según arquitectura).
- Client frontend: `erp-web` (public client + PKCE).
- Roles realm/app: `admin`, `cajero`, `bodega`, `rrhh`.

## Riesgos mitigados al introducir Keycloak temprano

- Evitar migración compleja de usuarios locales a SSO más adelante.
- Reducir deuda técnica en seguridad/autenticación.
- Mejorar trazabilidad de sesiones y eventos de login.


## Estado actual en API (iteración paso 5)

- La API ya extrae identidad desde bearer token (`sub`) y roles desde `roles` o `realm_access.roles` (compatible con Keycloak).
- La verificación criptográfica HS256 se activa al definir `JWT_HS256_SECRET`.
- Por seguridad, el modo sin verificación queda deshabilitado por defecto y sólo se habilita explícitamente con `JWT_ALLOW_INSECURE_TOKENS=true` (uso local temporal).
- Se validan claims temporales `exp` y `nbf` para evitar uso de tokens expirados/no vigentes.
- Opcionalmente se puede exigir aislamiento por emisor/audiencia con `JWT_EXPECTED_ISS` y `JWT_EXPECTED_AUD`.

## Próximos pasos técnicos

1. Levantar Keycloak en Docker Compose (`full`) junto a su base de datos.
2. Definir variables `KEYCLOAK_*` en `.env.example`.
3. Añadir validación de JWT de Keycloak en API (paso 5 de auth/permisos).
4. Documentar flujo login/logout y refresh token en web.
