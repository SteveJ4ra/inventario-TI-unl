"""Comprobaciones portables del contrato exportado, BPMN y fuentes del portal."""
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from lxml import etree
import hashlib
ROOT = Path(__file__).resolve().parent.parent
schema = json.loads((ROOT / "docs/producto-final/openapi.json").read_text(encoding="utf-8"))
assert schema["openapi"] == "3.1.0"
assert len(schema["paths"]) >= 40
assert set(schema["components"]["schemas"]["Envelope"]["required"]) == {"success","message","data","errors","meta"}
def refs(value):
    if isinstance(value, dict):
        if "$ref" in value:
            assert value["$ref"].split("/")[-1] in schema["components"]["schemas"]
        for child in value.values(): refs(child)
    elif isinstance(value, list):
        for child in value: refs(child)
refs(schema)
ns = {"b":"http://www.omg.org/spec/BPMN/20100524/MODEL"}
standards=ROOT/"tools/standards/bpmn"
for name,record in json.loads((standards/"sources.json").read_text()).items():
    assert hashlib.sha256((standards/name).read_bytes()).hexdigest()==record["sha256"]
xsd=etree.XMLSchema(etree.parse(str(standards/"BPMN20.xsd")))
xsd.assertValid(etree.parse(str(ROOT/"docs/producto-final/custodia.bpmn")))
xml = ET.parse(ROOT / "docs/producto-final/custodia.bpmn")
ids = {element.attrib["id"] for element in xml.iter() if "id" in element.attrib}
for flow in xml.findall(".//b:sequenceFlow", ns):
    assert flow.attrib["sourceRef"] in ids and flow.attrib["targetRef"] in ids
for gateway in xml.findall(".//b:exclusiveGateway", ns):
    assert len(gateway.findall("b:outgoing", ns)) >= 2
assert len(xml.findall(".//b:startEvent",ns)) == 1
assert xml.findall(".//b:endEvent",ns)
for path in ["portal/_quarto.yml", "portal/index.qmd", "docs/producto-final/arquitectura.dsl"]:
    assert (ROOT/path).is_file(), path
print(f"Contrato: {len(schema['paths'])} rutas; BPMN: XSD OMG, referencias y decisiones válidas; fuentes completas.")
