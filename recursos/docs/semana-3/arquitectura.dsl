workspace "Inventario TI" "C4 del flujo de activos y custodia" {
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
                modelos = component "Modelos" "Define persistencia y restricciones."
                v1 -> api "Enruta solicitudes"
                api -> permisos "Comprueba autorización"
                api -> servicios "Invoca operaciones"
                api -> modelos "Lee proyecciones de consulta"
                servicios -> modelos "Lee y actualiza"
            }
            db = container "Base de datos" "Conserva activos e historial." "PostgreSQL" "Database"
            web -> backend "Usa la API" "HTTPS/JSON"
            backend -> db "Consulta y actualiza" "ORM"
        }
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
