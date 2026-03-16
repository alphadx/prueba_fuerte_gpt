# Estrategia de rollback y contingencia operativa (Paso 12 - Etapa 6)

## Objetivo
Definir una estrategia ejecutable para revertir cambios de release y contener incidentes, con criterios explícitos para **abortar release** y responsables por decisión.

## Principios
1. **Seguridad primero:** ante duda, priorizar continuidad operativa y consistencia de datos.
2. **Abort early:** no esperar degradación prolongada cuando hay señales críticas (P0/P1).
3. **Rollback reproducible:** usar procedimientos versionados y auditables.
4. **Comunicación controlada:** cada decisión debe quedar registrada con timestamp, owner y alcance.

## Criterios explícitos para abortar release
Se debe declarar `ABORT_RELEASE` de forma inmediata si ocurre cualquiera de los siguientes:

- Falla de cualquier check bloqueante C1-C7 en `docs/release_go_live_checklist.md` durante la corrida final.
- Error de integridad en flujos críticos (ventas, pagos, billing) con riesgo de inconsistencia contable/documental.
- Incidente P0 activo (caída API, indisponibilidad de flujo de venta, corrupción de estado crítico).
- Incidente P1 persistente > 15 minutos sin mitigación efectiva.
- Señal SLO crítica fuera de umbral y tendencia negativa durante su ventana de observación.

## Matriz de contingencia por escenario

| Escenario | Trigger | Contención inmediata | Rollback | Owner |
|---|---|---|---|---|
| Regresión funcional en API | `make test` o smoke rojo | congelar despliegue y bloquear promoción | revert a commit estable + rerun gates | Backend/API |
| Degradación billing | `billing.error_rate` fuera de SLO / dead-letter creciente | pausar emisión automática y activar reproceso controlado | rollback de cambio de emisión + drenar cola | Billing owner |
| Degradación pagos | `payments.error_rate` alto / pending acumulado | pausar método afectado vía flags | rollback de adapter/webhook change | Payments owner |
| Falla infra Docker/Compose | `doctor-docker`/`compose-smoke` rojo en entorno release | detener release y mover validación a runner sano | no aplica código; rollback de release attempt | Infra owner |
| Evidencia incompleta de salida | checklist sin trazabilidad mínima | declarar PENDIENTE_ENTORNO/NO-GO | re-ejecutar corrida completa en entorno válido | Release captain |

## Runbook resumido de rollback

1. **Decisión**
   - Responsable: Release captain + Tech lead.
   - Registrar: motivo, alcance, timestamp UTC, SHA afectado.

2. **Contención**
   - Pausar promoción/despliegue.
   - Activar feature flags de mitigación (si aplica).
   - Comunicar estado a QA/Producto/Operación.

3. **Ejecución de rollback**
   - Volver al último commit/tag estable.
   - Reaplicar configuración segura mínima.
   - Verificar consistencia en flujos críticos.

4. **Validación post-rollback**
   - Ejecutar: `make test`, `make bootstrap-validate`, `make smoke-test-state`.
   - Validar SLI/SLO críticos (billing/pagos/health).
   - Documentar resultado como `NO-GO` o `PENDIENTE_ENTORNO` según corresponda.

5. **Cierre de incidente**
   - Crear postmortem breve con causa raíz, impacto y acciones preventivas.
   - Definir owner y fecha para remediación permanente.

## Evidencia mínima obligatoria tras rollback

```yaml
rollback_execution:
  timestamp_utc: "YYYY-MM-DDTHH:MM:SSZ"
  trigger: "<causa>"
  decision_owner: "<rol/persona>"
  affected_commit: "<sha>"
  rollback_target: "<sha/tag estable>"
  checks_after_rollback:
    - name: "make test"
      status: "pass|fail|warning_env"
    - name: "make bootstrap-validate"
      status: "pass|fail|warning_env"
    - name: "make smoke-test-state"
      status: "pass|fail|warning_env"
  slo_status:
    billing: "ok|degraded"
    payments: "ok|degraded"
    api_health: "ok|degraded"
  final_decision: "NO-GO|PENDIENTE_ENTORNO|GO"
```


## Comandos operativos de contingencia

### Contención rápida (sin rollback de código)
1. Congelar release (no promover nuevas versiones).
2. Ejecutar diagnóstico base:
   - `make test`
   - `make bootstrap-validate`
   - `make smoke-test-state`
3. Si hay degradación de pagos, desactivar método afectado por flag:
   - `PUT /payments/flags` con `enabled=false` para `branch/channel/method` impactado.
4. Si hay degradación de billing, pausar procesamiento automático y reintentar lote controlado:
   - `POST /billing/worker/process` con límite acotado.

### Rollback de release (código/config)
1. Seleccionar SHA estable previo validado.
2. Ejecutar rollback de versión (git revert o deploy del SHA estable según entorno).
3. Revalidar gates bloqueantes y SLI críticos.
4. Registrar evidencia usando la plantilla YAML de este documento.


## Criterio de salida post-contingencia
- **NO-GO**: persiste cualquier check bloqueante en `FAIL` o SLO crítico fuera de umbral.
- **PENDIENTE_ENTORNO**: no hay fallas funcionales críticas, pero falta evidencia de infraestructura (Docker/Compose).
- **GO**: sólo si la revalidación completa queda en verde, sin riesgos críticos abiertos y con evidencia versionada.
