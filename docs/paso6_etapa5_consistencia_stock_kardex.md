# Paso 6 — Etapa 5: Consistencia stock/kardex y rollback

## Objetivo
Garantizar que una venta fallida no deje residuos ni en stock ni en kardex, incluso en fallos parciales de ventas con múltiples líneas.

## Mejoras implementadas
1. Se agregó `rollback_reference(reference_id)` en `ProductService` para revertir en bloque movimientos de stock vinculados a una referencia de venta.
2. En `SaleService.complete_sale`, ante fallo en cualquier descuento de stock, se ejecuta rollback por referencia de venta (`sale_id`) en vez de compensaciones manuales por producto.
3. El rollback por referencia restaura:
   - cantidades originales de stock,
   - lista de movimientos kardex sin rastros de intentos fallidos.

## Validación agregada
- Caso de stock insuficiente simple: además de stock/sale, se verifica que no queden movimientos kardex.
- Caso de falla parcial multi-línea:
  - primera línea descuenta correctamente,
  - segunda línea falla por stock insuficiente,
  - rollback restaura stock de ambas líneas,
  - kardex queda limpio (`[]`),
  - no se persiste venta.

## Salida formal de Etapa 5
Consistencia inventario-venta reforzada con rollback completo por referencia, validada en escenarios de falla simple y parcial.
