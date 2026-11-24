from flask import abort, request
from ..db import get_db, ReportRepository


def required_text(name,maximum=100):
    value=request.form.get(name,'').strip()
    if not value or len(value)>maximum:
        raise ValueError(f'{name.replace("_"," ").capitalize()} must contain 1 to {maximum} characters.')
    return value


def report_or_404(report_id):
    report=ReportRepository(get_db()).get(report_id)
    if report is None:
        abort(404)
    return report


def row_or_404(table,row_id):
    # The table name is an internal constant, never a request parameter.
    if table not in ('records','issues','conversions','templates'):
        raise ValueError('Invalid repository table.')
    row=get_db().execute(f'SELECT * FROM {table} WHERE id=?',(row_id,)).fetchone()
    if row is None:
        abort(404)
    return row
