# Publicación del portal Quarto

Las fuentes se integran mediante PR a develop. main conserva su estado; la publicación utiliza una rama independiente gh-pages que contiene únicamente HTML/recursos generados.

## Procedimiento manual

1. Actualizar develop desde origin y comprobar que el árbol de fuentes esté limpio.
2. Ejecutar las comprobaciones del backend/documentación y revisar el resultado.
3. Generar el portal: quarto render portal.
4. Publicar explícitamente: quarto publish gh-pages portal --no-prompt.
5. Configurar GitHub Pages con fuente gh-pages y carpeta raíz, y verificar el despliegue y el enlace público.

URL del proyecto: https://stevej4ra.github.io/inventario-TI-unl/.

La publicación es una acción explícita después de la revisión; un push a develop ejecuta CI y no publica automáticamente el portal. GitHub construye/despliega Pages desde gh-pages. El workflow de CI conserva también el HTML como artefacto de revisión.

## Motivo de la configuración

El repositorio tiene main como rama predeterminada. GitHub exige que workflow_dispatch exista en la rama predeterminada para poder dispararlo. Usamos la alternativa oficial de Quarto/GitHub Pages desde una rama de publicación, evitando modificar main o cambiar la rama predeterminada del equipo.

Fuentes: https://quarto.org/docs/publishing/github-pages.html y https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow.

Pages publica documentación estática; el backend permanece en el despliegue Docker local acordado. No se publican secretos, bases, dumps ni datos de personas reales.
