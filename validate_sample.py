"""Reproduce the source-to-reference check without touching the working database."""
from pathlib import Path
from decimal import Decimal
from tempfile import TemporaryDirectory
import hashlib
import json
import time
from io import BytesIO
from openpyxl import load_workbook
from ovol import create_app
from ovol.db import get_db
from ovol.services.conversion import import_report,create_conversion


def main():
    root=Path(__file__).resolve().parent
    source=root/'samples/ovol_stock_valuation_20260930.txt'
    reference=root/'samples/client_reference.xlsx'
    expected={(r[1],r[5]):r for r in load_workbook(reference,data_only=True).active.values if r[1] and isinstance(r[8],(int,float))}
    started=time.perf_counter()
    with TemporaryDirectory() as folder:
        app=create_app({'TESTING':True,'DATABASE':str(Path(folder)/'validation.sqlite3')})
        with app.app_context(),get_db():
            rid=import_report('Ovol sample validation',source.name,source.read_bytes(),1)
            cid=create_conversion(rid,'Supplied sample verification')
            payload=get_db().execute('SELECT artifact FROM conversions WHERE id=?',(cid,)).fetchone()[0]
        wb=load_workbook(BytesIO(payload),data_only=True)
        actual={(r[1],r[5]):r for r in list(wb['Data'].values)[1:]}
        mismatches=[]
        normalizations=[]
        for key,row in actual.items():
            if key not in expected:
                mismatches.append({'unexpected_key':key})
                continue
            for index,(got,wanted) in enumerate(zip(row,expected[key])):
                if index>=8:
                    equal=(got is None and wanted is None) or (got is not None and wanted is not None and Decimal(str(got))==Decimal(str(wanted)))
                else:
                    raw=str(wanted) if wanted is not None else ''
                    clean=raw.removesuffix('┬á').strip()
                    if clean!=raw.strip():
                        normalizations.append({'key':key,'column':index+1,'reference_tail':'┬á','action':'remove known reference-only mojibake tail'})
                    equal=(str(got).strip() if got is not None else '')==clean
                if not equal:
                    mismatches.append({'key':key,'column':index+1,'actual':got,'reference':wanted})
        result={'source_records':len(actual),'reference_records':len(expected),'compared_cells':len(actual)*12,
                'missing_keys':sorted(set(expected)-set(actual)),'mismatches':mismatches,
                'reference_text_normalizations':normalizations,
                'elapsed_seconds':round(time.perf_counter()-started,3),
                'timing_scope':'One local automation run including app setup, import, export and comparison. Human review time excluded.',
                'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'reference_sha256':hashlib.sha256(reference.read_bytes()).hexdigest()}
        (root/'evidence/sample_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (root/'evidence/Ovol_Stock_Valuation_Converted.xlsx').write_bytes(payload)
        print(json.dumps({k:v for k,v in result.items() if k not in ('reference_text_normalizations',)},indent=2))
        assert len(actual)==1423 and set(actual)==set(expected) and not mismatches
        assert len(normalizations)==3


if __name__=='__main__':
    main()
