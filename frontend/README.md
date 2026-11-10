# Pantalla web · Inventario TI

React + TypeScript y Vite. Dependencias directas fijadas y package-lock.json versionable; instalar con npm ci para reproducirlas. Node recomendado local: 22.23.1; consultar engines de package.json al cambiar de entorno.

Desde frontend/:

```powershell
npm.cmd ci
npm.cmd run dev
```

Abrir http://127.0.0.1:5173/. Requiere backend Django activo en 127.0.0.1:8000, migraciones aplicadas y un gestor creado con el comando interactivo del backend. No hay cuentas predeterminadas ni registro público.

El proxy de Vite envía /api al backend manteniendo el contexto de la web. Para otro destino, definir VITE_PROXY_TARGET antes de iniciar y agregar el origen real de la web a DJANGO_CSRF_TRUSTED_ORIGINS del backend. Si el puerto está ocupado, seleccionar otro y ajustar ese origen; no detener procesos ajenos.

Pruebas y compilación:

```powershell
npm.cmd test -- --run
npm.cmd run build
```

Resultado original del incremento 002: 17 pruebas en siete archivos y compilación TypeScript/Vite correctas. Interacciones comprobadas: obligatorios, custodios sin cuenta, entrega, devolución, condición, rectificación con motivo, historial, filtros y errores del cliente API. La validación en navegador está documentada en [validation.md](../specs/002-registro-consulta-activos/validation.md).

La web usa cookies de sesión, solicita CSRF para escrituras y no almacena contraseñas/tokens en localStorage. Las acciones muestran el estado de la ficha y el backend valida nuevamente; un conflicto de revisión recarga la ficha sin reenviar la escritura automáticamente. Cerrar sesión limpia el estado privado de la vista. Etiquetas en español y diseño adaptable a escritorio/vista estrecha.

El build deja dist/ ignorado por Git; no significa despliegue público. Para la ejecución académica usar npm run dev junto al backend. No se incluye cliente móvil ni portal de custodios.

En Windows PowerShell se usa `npm.cmd` para evitar depender de npm.ps1, sin cambiar la política de ejecución del sistema. En Linux se utiliza `npm` sin la extensión .cmd.


## Licencias 006

Botón Licencias en navegación de escritorio y móvil: alta, lista/filtros, detalle, edición e historia. El cliente usa PATCH con CSRF y revisión; 409 recarga sin reintentar. Estado temporal calculado en backend; remanentes de vencidos se muestran con su advertencia.

Suite actual: 33 pruebas en nueve archivos y build correcto. Las 13 nuevas de 006 usan red simulada; también se ejecutó un recorrido Chrome real con backend y DB efímeros. Evidencia y límites en [validation.md](../specs/006-lotes-licencias/validation.md). Se conserva package-lock sin dependencias nuevas.
