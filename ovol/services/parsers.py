"""Deterministic parsers: never guess financial values or silently drop unknown lines."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import csv
from decimal import Decimal, InvalidOperation
import re

STOCK_COLUMNS = [
 ('Item Group','text',True),('Item Code','text',True),('Description','text',True),
 ('Description 2','text',False),('Dimensions','text',False),('Warehouse Code','text',True),
 ('Warehouse Description','text',True),('Unit','text',True),('Item Cost','decimal',True),
 ('Consignment Quantity','decimal',False),('Quantity On Hand','decimal',True),('Total Value','decimal',True)]


@dataclass
class ParsedRecord:
    line_no: int
    raw: str
    values: list[str]


@dataclass
class ParseResult:
    records: list[ParsedRecord] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    skipped: int = 0


def normal_decimal(value):
    """Canonical decimal string; blank stays blank, zero stays zero."""
    s = str(value).strip()
    if not s:
        return ''
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    if s.endswith('-'):
        s = '-' + s[:-1]
    if not re.fullmatch(r'[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)',s):
        raise ValueError('Enter a number, e.g. 1234.50 or (25.00).')
    try:
        n = Decimal(s.replace(',',''))
        if not n.is_finite() or len(n.as_tuple().digits)>15:
            raise ValueError('Number exceeds Excel\'s safe 15 significant digits.')
        return format(n,'f')
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal value.') from exc


def validate_values(values, columns):
    result, errors = [], []
    for index,c in enumerate(columns):
        v = str(values[index] if index<len(values) else '').strip()
        if len(v)>2000:
            errors.append(f"{c['name']}: maximum 2000 characters.")
        if c['required'] and not v:
            errors.append(f"{c['name']}: required.")
        if v and c['data_type']=='decimal':
            try:
                v = normal_decimal(v)
            except ValueError as e:
                errors.append(f"{c['name']}: {e}")
        result.append(v)
    return result,errors


class ReportParser(ABC):
    @abstractmethod
    def parse(self, text, columns):
        raise NotImplementedError


class StockValuationParser(ReportParser):
    """Ovol's September 2026 fixed layout; form feeds do not end a record."""
    def parse(self, text, columns):
        result = ParseResult()
        current = None
        group = ''
        footer = False
        totals = False
        for number,line in enumerate(text.replace('\r\n','\n').replace('\r','\n').split('\n'),1):
            line = line.lstrip('\f')
            s = line.strip()
            if not s:
                result.skipped += 1
                continue
            if s.startswith('Options Selected :'):
                footer = True
            if footer:
                result.skipped += 1
                continue
            if s.startswith('ITEM GROUP :'):
                group = s.split(':',1)[1].strip().split()[0]
                current = None
                totals = False
                result.skipped += 1
                continue
            if re.match(r'^(Warehouse (?:TOTALS|GRAND totals)|Item Group TOTALS|REPORT TOTALS|Report TOTALS|Grand TOTALS|GRAND TOTAL|TOTAL for ITEM GROUP)',s):
                current = None
                totals = True
                result.skipped += 1
                continue
            if totals and line.startswith(' ') and len(line)>105 and re.search(r'\d',line[90:]):
                # Continuation of a multi-warehouse total in the supplied layout.
                result.skipped += 1
                continue
            if s.startswith(('OVOL Singapore','Item Code','Type Con Iss','---')):
                result.skipped += 1
                continue
            if line and not line[0].isspace():
                totals = False
                values = [group,line[:16].strip(),line[16:48].strip(),'','',line[48:53].strip(),
                          line[53:71].strip(),line[71:78].strip(),line[78:90].strip(),
                          line[90:105].strip(),line[105:120].strip(),line[120:].strip()]
                # Retain even invalid rows so staff can correct them before export.
                current = ParsedRecord(number,line,values)
                result.records.append(current)
            elif current is not None:
                part = s
                target = 4 if re.match(r'^W\s*=',part) else 3
                current.values[target] = (current.values[target]+' '+part).strip()
                current.raw += '\n'+line
            else:
                result.issues.append(dict(line_no=number,raw=line,message='Unrecognised line; review before export.'))
        return result


class DelimitedParser(ReportParser):
    def __init__(self, delimiter):
        self._delimiter = delimiter

    def parse(self, text, columns):
        result = ParseResult()
        for number,line in enumerate(text.splitlines(),1):
            if not line.strip():
                result.skipped += 1
                continue
            try:
                values = next(csv.reader([line],delimiter=self._delimiter,strict=True))
                if len(values)!=len(columns):
                    raise ValueError(f'Expected {len(columns)} columns, found {len(values)}.')
                result.records.append(ParsedRecord(number,line,values))
            except (csv.Error, ValueError) as exc:
                result.issues.append(dict(line_no=number,raw=line,message=str(exc)))
        return result


class FixedWidthParser(ReportParser):
    def parse(self, text, columns):
        result = ParseResult()
        for number,line in enumerate(text.splitlines(),1):
            if not line.strip():
                result.skipped += 1
                continue
            end = max(c['end_pos'] for c in columns)
            if len(line)<end or line[end:].strip():
                result.issues.append(dict(line_no=number,raw=line,message='Line length does not match the selected fixed-width layout.'))
            else:
                values = [line[c['start_pos']:c['end_pos']].strip() for c in columns]
                result.records.append(ParsedRecord(number,line,values))
        return result


def get_parser(kind, delimiter=','):
    return {'stock':lambda:StockValuationParser(),'delimited':lambda:DelimitedParser(delimiter),
            'fixed':lambda:FixedWidthParser()}[kind]()
