"""Lance's proposed feature: reusable parsing-template CRUD."""
import csv
import io
import sqlite3
from flask import Blueprint,render_template,request,redirect,url_for,flash
from ..db import get_db,audit
from ..services.conversion import template_data
from ..services.parsers import STOCK_COLUMNS
from .common import required_text,row_or_404

bp=Blueprint('templates',__name__,url_prefix='/templates')


def parse_column_spec(text,kind):
    columns=[]
    if kind=='stock':
        return [dict(name=n,data_type=t,required=int(r),start_pos=None,end_pos=None) for n,t,r in STOCK_COLUMNS]
    if len(text)>12000:
        raise ValueError('Column configuration is too large.')
    names=set()
    last_end=0
    for row in csv.reader(io.StringIO(text),strict=True):
        if not row:
            continue
        if len(row)!=5:
            raise ValueError('Each column needs: Name,type,required,start,end (five values).')
        name,typ,required,start,end=[v.strip() for v in row]
        if not name or len(name)>60 or name.casefold() in names or typ not in ('text','decimal') or required not in ('0','1'):
            raise ValueError('Use unique column names (1-60 characters), text/decimal, and required 0/1.')
        names.add(name.casefold())
        start_pos=end_pos=None
        if kind=='fixed':
            try:
                start_pos,end_pos=int(start),int(end)
            except ValueError as exc:
                raise ValueError('Fixed-width columns require integer start and end positions.') from exc
            if not (0<=start_pos<end_pos<=2000) or start_pos<last_end:
                raise ValueError('Use ordered, non-overlapping fixed ranges between 0 and 2000.')
            last_end=end_pos
        columns.append(dict(name=name,data_type=typ,required=int(required),start_pos=start_pos,end_pos=end_pos))
    if not 1<=len(columns)<=30:
        raise ValueError('Define between 1 and 30 columns.')
    return columns


@bp.get('')
def index():
    return render_template('templates.html',title='Mapping templates',templates=get_db().execute('SELECT * FROM templates ORDER BY id').fetchall())


@bp.get('/<int:template_id>')
def detail(template_id):
    row_or_404('templates',template_id)
    return render_template('template_detail.html',title='Template details',template=template_data(template_id))


@bp.route('/new',methods=['GET','POST'])
@bp.route('/<int:template_id>/edit',methods=['GET','POST'])
def form(template_id=None):
    template=template_data(template_id) if template_id is not None else None
    if request.method=='POST':
        try:
            name=required_text('name',80)
            kind=request.form.get('kind','')
            delimiter=request.form.get('delimiter','|')
            if kind not in ('stock','delimited','fixed'):
                raise ValueError('Choose a supported parser.')
            if delimiter=='TAB':
                delimiter='\t'
            if kind=='delimited' and (len(delimiter)!=1 or delimiter in ('\r','\n','"','\x00')):
                raise ValueError('Delimiter must be one character, or TAB.')
            columns=parse_column_spec(request.form.get('columns',''),kind)
            with get_db() as db:
                if template:
                    db.execute('UPDATE templates SET name=?,kind=?,delimiter=? WHERE id=?',(name,kind,delimiter,template_id))
                    db.execute('DELETE FROM template_columns WHERE template_id=?',(template_id,))
                else:
                    template_id=db.execute('INSERT INTO templates(name,kind,delimiter) VALUES (?,?,?)',(name,kind,delimiter)).lastrowid
                db.executemany('INSERT INTO template_columns(template_id,position,name,data_type,required,start_pos,end_pos) VALUES (?,?,?,?,?,?,?)',
                     [(template_id,i,c['name'],c['data_type'],c['required'],c['start_pos'],c['end_pos']) for i,c in enumerate(columns)])
                audit('template',template_id,'update' if template else 'create',{'name':name,'kind':kind,'columns':columns})
            flash('Template saved. Existing reports keep their original template snapshot.','success')
            return redirect(url_for('templates.detail',template_id=template_id))
        except (ValueError,csv.Error,sqlite3.IntegrityError) as e:
            flash('Template name must be unique.' if isinstance(e,sqlite3.IntegrityError) else str(e),'error')
    spec=''
    if template:
        out=io.StringIO()
        writer=csv.writer(out,lineterminator='\n')
        for c in template['columns']:
            writer.writerow([c['name'],c['data_type'],c['required'],c['start_pos'] if c['start_pos'] is not None else '',c['end_pos'] if c['end_pos'] is not None else ''])
        spec=out.getvalue()
    return render_template('template_form.html',title='Edit template' if template else 'New mapping template',template=template,spec=spec)


@bp.route('/<int:template_id>/delete',methods=['GET','POST'])
def delete(template_id):
    row=row_or_404('templates',template_id)
    if request.method=='POST':
        with get_db() as db:
            audit('template',template_id,'delete',{'name':row['name']})
            db.execute('DELETE FROM templates WHERE id=?',(template_id,))
        flash('Template deleted. Imported reports and saved exports remain available.','success')
        return redirect(url_for('templates.index'))
    return render_template('confirm.html',title='Delete template',description='Imported reports retain their template snapshot. New imports cannot use this template.',label=row['name'])
