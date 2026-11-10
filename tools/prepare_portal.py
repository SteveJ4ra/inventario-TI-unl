"""Preparar solo documentación pública para el portal generado."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/"portal"/"recursos"
# Evitar que un recurso retirado siga apareciendo en una publicación posterior.
assert DEST.resolve().parent == (ROOT/"portal").resolve() and DEST.name == "recursos"
if DEST.exists():
    shutil.rmtree(DEST)
allowed={".md",".json",".png",".svg",".puml",".dsl",".bpmn",".txt",".csv"}
for folder in ["docs","specs"]:
    for source in (ROOT/folder).rglob("*"):
        if source.is_file() and source.suffix.lower() in allowed:
            target=DEST/source.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
source=ROOT/".specify/memory/constitution.md"
target=DEST/"constitution.md";target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
print("Recursos documentales preparados.")
