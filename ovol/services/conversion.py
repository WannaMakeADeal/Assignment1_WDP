"""Atomic ingestion; reviewed rows are the only data allowed into exports."""
import hashlib
import json
from .parsers import get_parser, validate_values
from .workbooks import build_workbook
from ..db import get_db, audit, ReportRepository


def template_data(template_id):
    db=get_db()
    row=db.execute('SELECT * FROM templates WHERE id=?',(template_id,)).fetchone()
    if row is None:
        raise ValueError('Choose an existing template.')
    columns=[dict(c) for c in db.execute('SELECT * FROM template_columns WHERE template_id=? ORDER BY position',(template_id,))]
    return dict(row,columns=columns)


def add_record(report_id,line_no,raw,values,columns):
    db=get_db()
    values,_=validate_values(values,columns)
    record_id=db.execute('INSERT INTO records(report_id,line_no,raw_text) VALUES (?,?,?)',(report_id,line_no,raw)).lastrowid
    db.executemany('INSERT INTO cells(record_id,column_id,value) VALUES (?,?,?)',
                   [(record_id,c['id'],v) for c,v in zip(columns,values)])
    return record_id


def import_report(name,filename,data,template_id):
    if not data or len(data)>5*1024*1024:
        raise ValueError('Select a non-empty TXT file up to 5 MB.')
    if b'\x00' in data:
        raise ValueError('Binary/UTF-16 files are unsupported. Save as UTF-8 or Windows-1252 TXT.')
    try:
        text=data.decode('utf-8-sig')
        encoding='UTF-8'
    except UnicodeDecodeError:
        try:
            text=data.decode('cp1252')
            encoding='Windows-1252'
        except UnicodeDecodeError as exc:
            raise ValueError('Unsupported encoding. Save as UTF-8 TXT.') from exc
    digest=hashlib.sha256(data).hexdigest()
    db=get_db()
    if db.execute('SELECT id FROM reports WHERE sha256=?',(digest,)).fetchone():
        raise ValueError('This exact file has already been imported. Open the existing report.')
    config=template_data(template_id)
    parsed=get_parser(config['kind'],config['delimiter']).parse(text,config['columns'])
    if not parsed.records and not parsed.issues:
        raise ValueError('No records were found. Check the file and selected template.')
    report_id=db.execute('INSERT INTO reports(name,filename,sha256,raw_text,raw_bytes,template_id,template_snapshot) VALUES (?,?,?,?,?,?,?)',
                         (name,filename,digest,text,data,template_id,json.dumps(config))).lastrowid
    db.executemany('INSERT INTO report_columns(report_id,position,name,data_type,required) VALUES (?,?,?,?,?)',
                   [(report_id,i,c['name'],c['data_type'],c['required']) for i,c in enumerate(config['columns'])])
    columns=ReportRepository(db).columns(report_id)
    for r in parsed.records:
        add_record(report_id,r.line_no,r.raw,r.values,columns)
    for issue in parsed.issues:
        db.execute('INSERT INTO issues(report_id,line_no,raw_text,message) VALUES (?,?,?,?)',
                   (report_id,issue['line_no'],issue['raw'],issue['message']))
    audit('report',report_id,'import',dict(filename=filename,sha256=digest,encoding=encoding,
          records=len(parsed.records),unrecognised_lines=len(parsed.issues),known_layout_lines_skipped=parsed.skipped),report_id)
    return report_id


def create_conversion(report_id,label):
    db=get_db()
    if not db.in_transaction:
        db.execute('BEGIN IMMEDIATE')
    repo=ReportRepository(db)
    report=repo.get(report_id)
    columns=repo.columns(report_id)
    rows=repo.records(report_id)
    selected=[r for r in rows if not r['excluded']]
    if not selected:
        raise ValueError('At least one included record is required for export.')
    if db.execute("SELECT 1 FROM issues WHERE report_id=? AND disposition='open'",(report_id,)).fetchone():
        raise ValueError('Resolve or explicitly exclude every unrecognised source line before export.')
    for r in selected:
        _,errors=validate_values([r['values'].get(c['id'],'') for c in columns],columns)
        if errors:
            raise ValueError(f"Record {r['id']} (line {r['line_no']}) needs correction: "+'; '.join(errors))
    snapshot=dict(columns=[dict(c) for c in columns],rows=rows,
                  issues=[dict(r) for r in db.execute('SELECT * FROM issues WHERE report_id=? ORDER BY id',(report_id,))],
                  source_sha256=report['sha256'],template=json.loads(report['template_snapshot']))
    fingerprint=hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest()
    events=[dict(r) for r in db.execute('SELECT * FROM audit_events WHERE report_id=? ORDER BY id',(report_id,))]
    artifact=build_workbook(columns,selected,{'Report':report['name'],'Original file':report['filename'],
             'Source SHA256':report['sha256'],'Reviewed data SHA256':fingerprint,'Included rows':len(selected),
             'Excluded rows':len(rows)-len(selected),'Template snapshot':report['template_snapshot'],
             'Workflow':'Local single-user POC; no ERP write-back'},events,[r for r in rows if r['excluded']],snapshot['issues'])
    artifact_hash=hashlib.sha256(artifact).hexdigest()
    cid=db.execute('INSERT INTO conversions(report_id,label,artifact,input_sha256,artifact_sha256,row_count) VALUES (?,?,?,?,?,?)',
                   (report_id,label,artifact,fingerprint,artifact_hash,len(selected))).lastrowid
    audit('conversion',cid,'create',dict(label=label,rows=len(selected),input_sha256=fingerprint,artifact_sha256=artifact_hash),report_id)
    return cid
