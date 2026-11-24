from io import BytesIO
from pathlib import Path
import hashlib
import sqlite3
import pytest
from openpyxl import load_workbook
from ovol.db import get_db,ReportRepository
from ovol.services.conversion import import_report,create_conversion


def ingest(app,data=b'A1|Paper|12|24.00\nB2|Board|3|12.50'):
    with app.app_context(),get_db():
        return import_report('Demo','demo.txt',data,2)


def test_csrf_required_for_every_write(client):
    assert client.post('/reports/new',data={}).status_code==400
    assert client.post('/templates/new',data={}).status_code==400


def test_untrusted_host_is_rejected(client):
    assert client.get('/',headers={'Host':'malicious.example'}).status_code==400


def test_security_headers(client):
    r=client.get('/')
    assert r.headers['X-Content-Type-Options']=='nosniff'
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']
    assert r.headers['Cache-Control']=='no-store'


def test_upload_report_crud(app,client,post):
    r=post('/reports/new',{'name':'September','template_id':'2','file':(BytesIO(b'A|Paper|2|5.00'),'demo.txt')})
    assert r.status_code==302
    assert client.get('/reports/1').status_code==200
    assert b'Paper' in client.get('/reports/1').data
    assert post('/reports/1/edit',{'name':'Revised'}).status_code==302
    assert b'Revised' in client.get('/reports/1').data
    assert client.get('/reports/1/source').data.startswith(b'A|Paper')
    assert post('/reports/1/delete').status_code==302
    assert client.get('/reports/1').status_code==404
    with app.app_context():
        assert get_db().execute('SELECT count(*) FROM audit_events').fetchone()[0]==3
        assert get_db().execute('SELECT count(*) FROM records').fetchone()[0]==0
        assert not get_db().execute('PRAGMA foreign_key_check').fetchall()


@pytest.mark.parametrize('name,data',[('bad.csv',b'a'),('bad.txt',b''),('binary.txt',b'\x00binary')])
def test_invalid_uploads_do_not_create_reports(app,post,name,data):
    assert post('/reports/new',{'name':'Bad','template_id':'2','file':(BytesIO(data),name)}).status_code==200
    with app.app_context():
        assert get_db().execute('SELECT count(*) FROM reports').fetchone()[0]==0


def test_duplicate_import_does_not_duplicate_records(app):
    ingest(app)
    with app.app_context(),get_db():
        with pytest.raises(ValueError,match='already been imported'):
            import_report('Duplicate','dup.txt',b'A1|Paper|12|24.00\nB2|Board|3|12.50',2)
        assert get_db().execute('SELECT count(*) FROM records').fetchone()[0]==2


def test_template_crud_and_report_snapshot(app,client,post):
    ingest(app)
    with app.app_context():
        before=ReportRepository(get_db()).records(1)
        snapshot=get_db().execute('SELECT template_snapshot FROM reports WHERE id=1').fetchone()[0]
    spec='Code,text,1,,\nAmount,decimal,1,,'
    assert post('/templates/new',dict(name='New layout',kind='delimited',delimiter='|',columns=spec)).status_code==302
    assert b'New layout' in client.get('/templates/3').data
    assert post('/templates/3/edit',dict(name='Changed',kind='fixed',delimiter='|',columns='Code,text,1,0,4\nAmount,decimal,1,4,12')).status_code==302
    assert b'Changed' in client.get('/templates/3').data
    assert post('/templates/3/delete').status_code==302
    assert client.get('/templates/3').status_code==404
    assert post('/templates/2/delete').status_code==302
    assert client.get('/reports/1').status_code==200
    with app.app_context():
        assert ReportRepository(get_db()).records(1)==before
        assert get_db().execute('SELECT template_snapshot FROM reports WHERE id=1').fetchone()[0]==snapshot


def test_invalid_template_is_atomic(app,post):
    before=None
    with app.app_context():before=get_db().execute('SELECT count(*) FROM template_columns').fetchone()[0]
    response=post('/templates/2/edit',dict(name='Bad',kind='fixed',delimiter='|',columns='A,text,1,0,8\nB,text,1,4,10'))
    assert b'non-overlapping' in response.data
    with app.app_context():assert get_db().execute('SELECT count(*) FROM template_columns').fetchone()[0]==before


def test_record_crud_and_revision_conflict(app,client,post):
    ingest(app)
    with app.app_context():cols=ReportRepository(get_db()).columns(1)
    values={f'c_{c["id"]}':v for c,v in zip(cols,['A1','Corrected paper','13','26.00'])}
    assert post('/records/1/edit',dict(values,reason='Verified source',revision='1')).status_code==302
    assert b'Corrected paper' in client.get('/records/1').data
    assert post('/records/1/edit',dict(values,reason='Stale tab',revision='1')).status_code==409
    assert post('/reports/1/records/new',dict(values,line_no='1',reason='Manual recovery')).status_code==302
    assert client.get('/records/3').status_code==200
    assert post('/records/3/exclude',dict(reason='Duplicate manual row')).status_code==302
    assert b'Excluded:' in client.get('/records/3').data
    assert post('/records/3/exclude',dict(reason='Restore reviewed row')).status_code==302
    assert post('/records/3/delete',dict(reason='Remove duplicate')).status_code==302
    assert client.get('/records/3').status_code==404


def test_invalid_record_edit_leaves_old_values(app,post):
    ingest(app)
    with app.app_context():cols=ReportRepository(get_db()).columns(1)
    values={f'c_{c["id"]}':v for c,v in zip(cols,['A1','Paper','not a number','24'])}
    r=post('/records/1/edit',dict(values,reason='Test invalid entry',revision='1'))
    assert b'Enter a number' in r.data
    with app.app_context():
        assert ReportRepository(get_db()).records(1)[0]['values'][cols[2]['id']]=='12'


def test_export_blocked_by_invalid_record(app):
    ingest(app,b'A|Paper|bad|25.00')
    with app.app_context(),get_db():
        with pytest.raises(ValueError,match='needs correction'):create_conversion(1,'Invalid')
        assert get_db().execute('SELECT count(*) FROM conversions').fetchone()[0]==0


def test_unknown_source_line_must_be_reviewed(app,client,post):
    ingest(app,b'A|Paper|2|5\nnondata')
    with app.app_context(),get_db():
        with pytest.raises(ValueError,match='unrecognised'):create_conversion(1,'Blocked')
    assert client.get('/issues/1/review').status_code==200
    assert post('/issues/1/review',dict(reason='Verified non-data footer')).status_code==302
    assert post('/reports/1/exports/new',dict(label='Reviewed')).status_code==302
    wb=load_workbook(BytesIO(client.get('/exports/1/download').data),data_only=True)
    assert wb['Exclusions'].max_row==2
    assert 'footer' in wb['Exclusions']['B2'].value


def test_issue_can_be_recovered_as_record(app,client,post):
    ingest(app,b'A|Paper|2|5\nB Board 3 7')
    with app.app_context():cols=ReportRepository(get_db()).columns(1)
    values={f'c_{c["id"]}':v for c,v in zip(cols,['B','Board','3','7'])}
    assert post('/reports/1/records/new?issue_id=1',dict(values,reason='Re-keyed from source',issue_id='1')).status_code==302
    with app.app_context(),get_db():
        assert get_db().execute('SELECT disposition FROM issues WHERE id=1').fetchone()[0]=='resolved'
        create_conversion(1,'Recovered')


def test_excel_snapshot_crud_and_formula_text(app,client,post):
    ingest(app,b'=HYPERLINK("bad")|@danger|2|5.00')
    assert post('/reports/1/exports/new',dict(label='First snapshot')).status_code==302
    first=client.get('/exports/1/download').data
    w=load_workbook(BytesIO(first),data_only=False)
    assert w['Data']['A2'].data_type=='s'
    assert w['Data']['B2'].data_type=='s'
    assert w['Data']['C2'].data_type=='n'
    assert set(w.sheetnames)=={'Data','Provenance','Metadata','Exclusions','Audit'}
    assert w['Data'].max_row==2
    with app.app_context():cols=ReportRepository(get_db()).columns(1)
    values={f'c_{c["id"]}':v for c,v in zip(cols,['NEW','Changed','3','7.00'])}
    post('/records/1/edit',dict(values,reason='Changed after export',revision='1'))
    assert client.get('/exports/1/download').data==first
    assert post('/exports/1/edit',dict(label='Renamed snapshot')).status_code==302
    assert b'Renamed snapshot' in client.get('/exports/1').data
    assert client.get('/exports/1/download').data==first
    with app.app_context():
        row=get_db().execute('SELECT artifact_sha256 FROM conversions WHERE id=1').fetchone()
        assert hashlib.sha256(first).hexdigest()==row[0]
    assert post('/exports/1/delete').status_code==302
    assert client.get('/exports/1').status_code==404
    assert client.get('/reports/1').status_code==200


def test_report_deletion_cascades_exports(app,post):
    ingest(app)
    post('/reports/1/exports/new',dict(label='Snapshot'))
    post('/reports/1/delete')
    with app.app_context():
        for t in ('records','cells','report_columns','issues','conversions'):
            assert get_db().execute(f'SELECT count(*) FROM {t}').fetchone()[0]==0
        assert get_db().execute('SELECT count(*) FROM audit_events').fetchone()[0]>=3


def test_xss_names_are_escaped(app,client,post):
    ingest(app)
    post('/reports/1/edit',dict(name='<script>alert(1)</script>'))
    body=client.get('/reports/1').data
    assert b'<script>alert(1)</script>' not in body
    assert b'&lt;script&gt;' in body


def test_relaunch_preserves_data(app):
    ingest(app)
    from ovol import create_app
    second=create_app(dict(TESTING=True,DATABASE=app.config['DATABASE']))
    assert b'Demo' in second.test_client().get('/').data


@pytest.mark.parametrize('data',[b'\xef\xbb\xbfA|Paper|1|2',b'A|Caf\xe9 paper|1|2'])
def test_source_download_preserves_original_bytes(app,client,data):
    ingest(app,data)
    assert client.get('/reports/1/source').data==data


def test_deleted_templates_stay_deleted_after_relaunch(app,post):
    post('/templates/1/delete')
    post('/templates/2/delete')
    from ovol import create_app
    second=create_app(dict(TESTING=True,DATABASE=app.config['DATABASE']))
    with second.app_context():
        assert get_db().execute('SELECT count(*) FROM templates').fetchone()[0]==0


@pytest.mark.parametrize('path',['/reports/999','/records/999','/templates/999','/exports/999','/issues/999/review'])
def test_missing_records_return_404(client,path):
    assert client.get(path).status_code==404


def test_report_points_to_invalid_row_on_later_page(app, client):
    clean_rows = [f"P{i}|Paper|2|4" for i in range(50)]
    data = "\n".join(clean_rows + ["LAST|Board|wrong|4"]).encode()
    ingest(app, data)
    page = client.get('/reports/1').get_data(as_text=True)
    assert 'href="/records/51">Review first invalid record' in page
    assert 'Create Excel export' not in page


def test_report_primary_action_matches_review_state(app, client, post):
    ingest(app, b"A1|Paper|2|4\nunknown comment")
    page = client.get('/reports/1').get_data(as_text=True)
    assert 'Review first unknown line' in page
    assert 'Create Excel export' not in page
    assert post('/issues/1/review', dict(reason='Sample comment')).status_code == 302
    page = client.get('/reports/1').get_data(as_text=True)
    assert 'Create Excel export' in page
    assert post('/records/1/exclude', dict(reason='Sample exclusion')).status_code == 302
    page = client.get('/reports/1').get_data(as_text=True)
    assert 'No included records.' in page
    assert 'Ready to export.' not in page
