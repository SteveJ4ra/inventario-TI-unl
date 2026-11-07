from pathlib import Path
import sys,json,re
import argparse
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--samples',required=True,type=Path);args=parser.parse_args()
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate
schema=json.loads((ROOT/'docs/producto-final/openapi.json').read_text(encoding='utf-8'))
validate(schema)
samples=json.loads(args.samples.read_text(encoding='utf-8'))
errors=[];checked=0
for sample in samples:
    path=sample['path'].removeprefix('/api/v1')
    match=next((p for p in schema['paths'] if re.fullmatch(re.sub(r'{[^}]+}',r'[^/]+',p),path)),None)
    assert match,path
    op=schema['paths'][match][sample['method'].lower()]
    response=op['responses'].get(str(sample['status']))
    if response is None:
        errors.append({'path':match,'method':sample['method'],'status':sample['status'],'error':'Estado no documentado'});continue
    target=response['content']['application/json']['schema']
    validator=Draft202012Validator({'components':schema['components'],**target})
    for error in validator.iter_errors(sample['body']):
        errors.append({'path':match,'method':sample['method'],'status':sample['status'],'field':list(error.path),'error':error.message})
    checked+=1
result={'openapi_valid':True,'responses_checked':checked,'errors':errors}

print(json.dumps(result,ensure_ascii=True,indent=2));sys.exit(bool(errors))
