"""Adil's proposed feature: report CRUD and import orchestration."""
import sqlite3
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from ..db import get_db, audit, ReportRepository
from ..services.conversion import import_report
from ..services.parsers import validate_values
from .common import required_text, report_or_404

bp=Blueprint('reports',__name__)


@bp.get('/')
def home():
    db=get_db()
    rows=db.execute('SELECT r.*, (SELECT count(*) FROM records WHERE report_id=r.id) AS row_count FROM reports r ORDER BY id DESC').fetchall()
    return render_template('reports.html',title='Reports',reports=rows)


@bp.route('/reports/new',methods=['GET','POST'])
def new():
    db=get_db()
    if request.method=='POST':
        try:
            name=required_text('name')
            upload=request.files.get('file')
            if not upload or not upload.filename.lower().endswith('.txt'):
                raise ValueError('Choose a .txt file.')
            tid=int(request.form.get('template_id','0'))
            with db:
                rid=import_report(name,secure_filename(upload.filename) or 'report.txt',upload.read(),tid)
            flash('Report imported. Review the records, then export.','success')
            return redirect(url_for('reports.detail',report_id=rid))
        except (ValueError,sqlite3.IntegrityError) as e:
            flash(str(e),'error')
    templates=db.execute('SELECT * FROM templates ORDER BY name').fetchall()
    return render_template('report_form.html',title='Import a report',templates=templates,report=None)


@bp.get('/reports/<int:report_id>')
def detail(report_id):
    report=report_or_404(report_id)
    db=get_db()
    repo=ReportRepository(db)
    columns=repo.columns(report_id)
    rows=repo.records(report_id)
    for row in rows:
        _,row['errors']=validate_values([row['values'].get(c['id'],'') for c in columns],columns)
    invalid_rows = [row for row in rows if row['errors'] and not row['excluded']]
    issues=db.execute('SELECT * FROM issues WHERE report_id=? ORDER BY line_no,id',(report_id,)).fetchall()
    open_issues = [issue for issue in issues if issue['disposition'] == 'open']
    try:
        page=max(1,int(request.args.get('page',1)))
    except ValueError:
        page=1
    pages=max(1,(len(rows)+49)//50)
    page=min(page,pages)
    return render_template('report_detail.html',title=report['name'],report=report,columns=columns,
          rows=rows[(page-1)*50:page*50],total=len(rows),included=sum(not r['excluded'] for r in rows),
          invalid=len(invalid_rows), first_invalid=next(iter(invalid_rows), None),
          issues=issues, open_issues=len(open_issues), first_issue=next(iter(open_issues), None),
          page=page, pages=pages,
          conversions=db.execute('SELECT id,label,row_count,created_at FROM conversions WHERE report_id=? ORDER BY id DESC',(report_id,)).fetchall())


@bp.route('/reports/<int:report_id>/edit',methods=['GET','POST'])
def edit(report_id):
    report=report_or_404(report_id)
    if request.method=='POST':
        try:
            name=required_text('name')
            with get_db() as db:
                db.execute('UPDATE reports SET name=? WHERE id=?',(name,report_id))
                audit('report',report_id,'rename',{'before':report['name'],'after':name},report_id)
            return redirect(url_for('reports.detail',report_id=report_id))
        except ValueError as e:
            flash(str(e),'error')
    return render_template('report_form.html',title='Rename report',report=report,templates=[])


@bp.route('/reports/<int:report_id>/delete',methods=['GET','POST'])
def delete(report_id):
    report=report_or_404(report_id)
    if request.method=='POST':
        with get_db() as db:
            audit('report',report_id,'delete',{'name':report['name'],'sha256':report['sha256']},report_id)
            db.execute('DELETE FROM reports WHERE id=?',(report_id,))
        flash('Report, its rows and saved exports deleted. Audit events retained.','success')
        return redirect(url_for('reports.home'))
    return render_template('confirm.html',title='Delete report',description='This deletes this report, all its records and saved Excel exports. Audit events remain.',label=report['name'])


@bp.get('/reports/<int:report_id>/source')
def source(report_id):
    report=report_or_404(report_id)
    return send_file(BytesIO(report['raw_bytes']),mimetype='text/plain',as_attachment=True,download_name='source-'+report['filename'])


@bp.get('/reports/<int:report_id>/audit')
def history(report_id):
    report=report_or_404(report_id)
    rows=get_db().execute('SELECT * FROM audit_events WHERE report_id=? ORDER BY id DESC',(report_id,)).fetchall()
    return render_template('audit.html',title='Audit history',report=report,events=rows)
