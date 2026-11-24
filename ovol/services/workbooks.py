"""Snapshot export with typed numbers, provenance and Excel formula protection."""
from decimal import Decimal
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter


def append_safe(sheet, values):
    sheet.append(values)
    # Force untrusted strings to text, including = + - @ payloads.
    for cell in sheet[sheet.max_row]:
        if isinstance(cell.value,str):
            cell.data_type='s'


def build_workbook(columns, records, metadata, audit_rows, excluded, issues):
    wb = Workbook()
    ws = wb.active
    ws.title='Data'
    append_safe(ws,[c['name'] for c in columns])
    for row in records:
        values=[]
        for c in columns:
            value=row['values'].get(c['id'],'')
            values.append(Decimal(value) if value and c['data_type']=='decimal' else value or None)
        append_safe(ws,values)
    ws.freeze_panes='A2'
    if records:
        table=Table(displayName='ReportData',ref=f'A1:{get_column_letter(len(columns))}{len(records)+1}')
        table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True)
        ws.add_table(table)
    for i,c in enumerate(columns,1):
        ws.column_dimensions[get_column_letter(i)].width = 40 if 'Description' in c['name'] or c['name']=='Dimensions' else 23
        if c['data_type']=='decimal':
            for cell in list(ws.columns)[i-1][1:]:
                cell.number_format='#,##0.0000;[Red](#,##0.0000)'
    provenance=wb.create_sheet('Provenance')
    append_safe(provenance,['Source Line','Item / Record Reference'])
    for r in records:
        append_safe(provenance,[r['line_no'],r['id']])
    meta=wb.create_sheet('Metadata')
    append_safe(meta,['Field','Value'])
    for k,v in metadata.items():
        append_safe(meta,[k,str(v)])
    ex=wb.create_sheet('Exclusions')
    append_safe(ex,['Source Line','Reason','Original Text'])
    for r in excluded:
        append_safe(ex,[r['line_no'],r['reason'],r['raw_text']])
    for r in issues:
        append_safe(ex,[r['line_no'],r['disposition']+': '+r['resolution'],r['raw_text']])
    audit=wb.create_sheet('Audit')
    append_safe(audit,['Time (UTC)','Entity','Action','Details'])
    for r in audit_rows:
        append_safe(audit,[r['created_at'],r['entity'],r['action'],r['details']])
    for sheet in wb:
        sheet.freeze_panes='A2'
        for cell in sheet[1]:
            cell.fill=PatternFill('solid',fgColor='123F49')
            cell.font=Font(color='FFFFFF',bold=True)
            cell.alignment=Alignment(wrap_text=True)
        sheet.row_dimensions[1].height=32
        if sheet!=ws:
            for col in sheet.columns:
                sheet.column_dimensions[col[0].column_letter].width = 28
    output=BytesIO()
    wb.save(output)
    return output.getvalue()
