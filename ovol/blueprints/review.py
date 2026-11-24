"""Ming Kong's proposed feature: row CRUD, validation and source-line review."""
from flask import Blueprint,render_template,request,redirect,url_for,flash,abort
from ..db import get_db,audit,ReportRepository
from ..services.parsers import validate_values
from ..services.conversion import add_record
from .common import row_or_404,report_or_404,required_text

bp=Blueprint('review',__name__)


@bp.route('/reports/<int:report_id>/records/new',methods=['GET','POST'])
@bp.route('/records/<int:record_id>/edit',methods=['GET','POST'])
def form(report_id=None,record_id=None):
    db=get_db()
    row=row_or_404('records',record_id) if record_id is not None else None
    if row:
        report_id=row['report_id']
    report=report_or_404(report_id)
    columns=ReportRepository(db).columns(report_id)
    values={}
    if row:
        values={c['column_id']:c['value'] for c in db.execute('SELECT * FROM cells WHERE record_id=?',(record_id,))}
    issue=None
    issue_id=request.args.get('issue_id') or request.form.get('issue_id')
    if issue_id:
        try:
            issue=row_or_404('issues',int(issue_id))
        except ValueError:
            abort(400,description='Invalid source issue.')
        if issue['report_id']!=report_id or issue['disposition']!='open':
            abort(409,description='This source issue is no longer open.')
    if request.method=='POST':
        try:
            reason=required_text('reason',500)
            submitted=[request.form.get(f'c_{c["id"]}','') for c in columns]
            clean,errors=validate_values(submitted,columns)
            values=dict(zip([c['id'] for c in columns],submitted))
            if errors:
                raise ValueError('; '.join(errors))
            with db:
                if row:
                    changed=db.execute('UPDATE records SET revision=revision+1, reason=? WHERE id=? AND revision=?',
                           (reason,record_id,request.form.get('revision',''))).rowcount
                    if not changed:
                        abort(409,description='This record changed in another tab. Reload before editing.')
                    before={c['column_id']:c['value'] for c in db.execute('SELECT * FROM cells WHERE record_id=?',(record_id,))}
                    db.executemany('UPDATE cells SET value=? WHERE record_id=? AND column_id=?',[(v,record_id,c['id']) for c,v in zip(columns,clean)])
                    audit('record',record_id,'update',{'before':before,'after':dict(zip([c['name'] for c in columns],clean)),'reason':reason},report_id)
                else:
                    line_no=issue['line_no'] if issue else int(request.form.get('line_no','0'))
                    if line_no<1 or line_no>len(report['raw_text'].split('\n')):
                        raise ValueError('Source line must exist in the uploaded report.')
                    raw=issue['raw_text'] if issue else report['raw_text'].split('\n')[line_no-1]
                    record_id=add_record(report_id,line_no,raw,clean,columns)
                    audit('record',record_id,'create',{'values':dict(zip([c['name'] for c in columns],clean)),'reason':reason},report_id)
                    if issue:
                        changed=db.execute("UPDATE issues SET disposition='resolved',resolution=? WHERE id=? AND disposition='open'",(f'Recovered as record {record_id}: '+reason,issue['id'])).rowcount
                        if not changed:
                            abort(409,description='Source issue was already reviewed. Reload.')
                        audit('issue',issue['id'],'recover',{'record_id':record_id,'reason':reason},report_id)
            flash('Record saved with an audit event.','success')
            return redirect(url_for('review.detail',record_id=record_id))
        except ValueError as e:
            flash(str(e),'error')
    return render_template('record_form.html',title='Correct record' if row else 'Add a reviewed record',report=report,record=row,columns=columns,values=values,issue=issue)


@bp.get('/records/<int:record_id>')
def detail(record_id):
    row=row_or_404('records',record_id)
    repo=ReportRepository(get_db())
    values={r['column_id']:r['value'] for r in get_db().execute('SELECT * FROM cells WHERE record_id=?',(record_id,))}
    columns=repo.columns(row['report_id'])
    _,errors=validate_values([values.get(c['id'],'') for c in columns],columns)
    return render_template('record_detail.html',title='Record review',record=row,report=repo.get(row['report_id']),columns=columns,values=values,errors=errors)


@bp.route('/records/<int:record_id>/exclude',methods=['GET','POST'])
def exclude(record_id):
    row=row_or_404('records',record_id)
    if request.method=='POST':
        try:
            reason=required_text('reason',500)
            with get_db() as db:
                db.execute('UPDATE records SET excluded=?,reason=?,revision=revision+1 WHERE id=?',(0 if row['excluded'] else 1,reason,record_id))
                audit('record',record_id,'include' if row['excluded'] else 'exclude',{'reason':reason},row['report_id'])
            return redirect(url_for('review.detail',record_id=record_id))
        except ValueError as e:
            flash(str(e),'error')
    return render_template('confirm.html',title='Restore record' if row['excluded'] else 'Exclude record',description='Keep the original source, and record a reason for this decision.',label=f'Record {record_id}',needs_reason=True)


@bp.route('/records/<int:record_id>/delete',methods=['GET','POST'])
def delete(record_id):
    row=row_or_404('records',record_id)
    if request.method=='POST':
        try:
            reason=required_text('reason',500)
            with get_db() as db:
                before={str(r['column_id']):r['value'] for r in db.execute('SELECT * FROM cells WHERE record_id=?',(record_id,))}
                audit('record',record_id,'delete',{'before':before,'line_no':row['line_no'],'original':row['raw_text'],'reason':reason},row['report_id'])
                db.execute('DELETE FROM records WHERE id=?',(record_id,))
            flash('Record deleted; original file and audit history retained.','success')
            return redirect(url_for('reports.detail',report_id=row['report_id']))
        except ValueError as e:
            flash(str(e),'error')
    return render_template('confirm.html',title='Delete record',description='The original file and deletion audit remain. Use Exclude if the record should be listed in the export exclusions.',label=f'Record {record_id}',needs_reason=True)


@bp.route('/issues/<int:issue_id>/review',methods=['GET','POST'])
def issue_review(issue_id):
    issue=row_or_404('issues',issue_id)
    if request.method=='POST':
        try:
            reason=required_text('reason',500)
            if issue['disposition']!='open':
                abort(409,description='This issue was already reviewed. Reload.')
            with get_db() as db:
                changed=db.execute("UPDATE issues SET disposition='excluded',resolution=? WHERE id=? AND disposition='open'",(reason,issue_id)).rowcount
                if not changed:
                    abort(409,description='This issue was already reviewed. Reload.')
                audit('issue',issue_id,'exclude',{'reason':reason,'line_no':issue['line_no'],'original':issue['raw_text']},issue['report_id'])
            return redirect(url_for('reports.detail',report_id=issue['report_id']))
        except ValueError as e:
            flash(str(e),'error')
    return render_template('issue.html',title='Review source line',issue=issue)
