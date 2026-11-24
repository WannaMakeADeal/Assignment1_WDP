"""Aidan's proposed feature: saved conversion CRUD and immutable downloads."""
from io import BytesIO
from flask import Blueprint,render_template,request,redirect,url_for,flash,send_file
from ..db import get_db,audit
from ..services.conversion import create_conversion
from .common import report_or_404,row_or_404,required_text

bp=Blueprint('exports',__name__)


@bp.route('/reports/<int:report_id>/exports/new',methods=['GET','POST'])
def new(report_id):
    report=report_or_404(report_id)
    if request.method=='POST':
        try:
            label=required_text('label')
            with get_db():
                cid=create_conversion(report_id,label)
            return redirect(url_for('exports.detail',conversion_id=cid))
        except ValueError as e:
            flash(str(e),'error')
    return render_template('export_form.html',title='Create Excel export',report=report,conversion=None)


@bp.get('/exports/<int:conversion_id>')
def detail(conversion_id):
    conversion=row_or_404('conversions',conversion_id)
    return render_template('export_detail.html',title='Excel export ready',conversion=conversion)


@bp.route('/exports/<int:conversion_id>/edit',methods=['GET','POST'])
def edit(conversion_id):
    conversion=row_or_404('conversions',conversion_id)
    if request.method=='POST':
        try:
            label=required_text('label')
            with get_db() as db:
                db.execute('UPDATE conversions SET label=? WHERE id=?',(label,conversion_id))
                audit('conversion',conversion_id,'rename',{'before':conversion['label'],'after':label},conversion['report_id'])
            return redirect(url_for('exports.detail',conversion_id=conversion_id))
        except ValueError as e:
            flash(str(e),'error')
    return render_template('export_form.html',title='Rename saved export',report=None,conversion=conversion)


@bp.route('/exports/<int:conversion_id>/delete',methods=['GET','POST'])
def delete(conversion_id):
    conversion=row_or_404('conversions',conversion_id)
    if request.method=='POST':
        with get_db() as db:
            audit('conversion',conversion_id,'delete',{'artifact_sha256':conversion['artifact_sha256']},conversion['report_id'])
            db.execute('DELETE FROM conversions WHERE id=?',(conversion_id,))
        return redirect(url_for('reports.detail',report_id=conversion['report_id']))
    return render_template('confirm.html',title='Delete saved export',description='Deletes this Excel snapshot. The source report and reviewed rows remain.',label=conversion['label'])


@bp.get('/exports/<int:conversion_id>/download')
def download(conversion_id):
    conversion=row_or_404('conversions',conversion_id)
    return send_file(BytesIO(conversion['artifact']),mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,download_name=f'ovol-report-{conversion_id}.xlsx')
