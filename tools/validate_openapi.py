"""Valida OpenAPI y compara opcionalmente una exportación del runtime."""
import argparse,json
from pathlib import Path
from openapi_spec_validator import validate
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path);args=parser.parse_args()
schema=json.loads((ROOT/'docs/producto-final/openapi.json').read_text(encoding='utf-8'))
validate(schema)
if args.runtime:
    assert json.loads(args.runtime.read_text(encoding='utf-8'))==schema, 'La exportación del runtime difiere del contrato versionado'
print('OpenAPI 3.1 válido; contrato y exportación coherentes.')
