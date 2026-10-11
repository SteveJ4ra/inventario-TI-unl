# Mapa de actores

Mapa de actores del sistema de inventario y sus relaciones. Línea continua: interacción con el sistema; línea discontinua: relación entre actores. Descripción detallada en [actores.md](actores.md).

```mermaid
flowchart LR
  GES["Gestor de activos<br/>Usuario principal"]
  CUS["Custodio<br/>Usuario secundario"]
  ADM["Administrador<br/>Responsable del sistema"]
  SGI(["Sistema de inventario"])
  GES <--> SGI
  CUS <--> SGI
  ADM <--> SGI
  GES -. asigna activo .-> CUS
```
