workspace "Inventario TI" "C4 del backend integrado de la Unidad 1" {
    model {
        gestor = person "Gestor autorizado" "Opera el inventario."
        revisor = person "Revisor" "Decide solicitudes asignadas de otra facultad."
        operador = person "Operador técnico" "Administra facultades y revisores."
        sistema = softwareSystem "Inventario TI" "Gestiona activos, custodia e historial." {
            web = container "Aplicación web" "Interfaz para cuentas autorizadas." "React y Vite"
            backend = container "Backend" "Expone la API y aplica reglas." "Django y Django REST Framework" {
                v1 = component "Adaptador v1" "Publica rutas versionadas y normaliza respuestas JSON."
                api = component "API y serialización" "Valida las entradas y despacha operaciones."
                permisos = component "Autenticación y permisos" "Gestiona sesión, CSRF y autorización."
                servicios = component "Servicios" "Aplica reglas y transacciones de inventario y adquisición."
                observabilidad = component "Observabilidad" "Registra ruta, estado, duración e identificador; comprueba conexión SQL."
                modelos = component "Modelos" "Define persistencia y restricciones."
                observabilidad -> api "Correlaciona solicitudes sin cuerpos ni secretos"
                v1 -> api "Enruta solicitudes"
                api -> permisos "Comprueba autorización"
                api -> servicios "Invoca operaciones"
                api -> modelos "Lee proyecciones de consulta"
                servicios -> modelos "Lee y actualiza"
            }
            db = container "Base de datos" "Conserva activos e historial." "PostgreSQL" "Database"
            web -> backend "Usa la API" "HTTP local / HTTPS publicado; JSON"
            backend -> db "Consulta y actualiza" "ORM"
        }
        portal = softwareSystem "Portal técnico Quarto" "Documentación estática; preparado para GitHub Pages."
        portal -> sistema "Documenta contrato, procesos y operación"
        gestor -> sistema "Gestiona el inventario"
        revisor -> sistema "Decide solicitudes"
        operador -> sistema "Administra facultades y revisores"
        gestor -> web "Usa"
        revisor -> web "Usa"
        operador -> web "Usa"
    }
    views {
        systemContext sistema "C1" {
            include *
            autoLayout lr
        }
        container sistema "C2" {
            include *
            autoLayout lr
        }
        component backend "C3" {
            include *
            autoLayout lr
        }
    }
}
