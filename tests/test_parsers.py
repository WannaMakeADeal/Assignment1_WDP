from decimal import Decimal
from pathlib import Path
import pytest
from openpyxl import load_workbook
from ovol.services.parsers import normal_decimal,StockValuationParser,STOCK_COLUMNS,DelimitedParser,FixedWidthParser,validate_values

ROOT=Path(__file__).resolve().parents[1]
COLS=[dict(name=n,data_type=t,required=r) for n,t,r in STOCK_COLUMNS]


@pytest.mark.parametrize('raw,expected',[('0','0'),('.7500','0.7500'),('1,234.50','1234.50'),('(25.00)','-25.00'),('25.00-','-25.00'),('',''),('-0.50','-0.50')])
def test_money_is_preserved(raw,expected):
    assert normal_decimal(raw)==expected


@pytest.mark.parametrize('raw',['NaN','Infinity','1,23','1e6','=5+5','1234567890123456','--4'])
def test_unsafe_or_ambiguous_numbers_fail(raw):
    with pytest.raises(ValueError):normal_decimal(raw)


def test_client_file_matches_reference_cells():
    parsed=StockValuationParser().parse((ROOT/'samples/ovol_stock_valuation_20260930.txt').read_text(),COLS)
    assert len(parsed.records)==1423
    assert parsed.issues==[]
    expected={(r[1],r[5]):r for r in load_workbook(ROOT/'samples/client_reference.xlsx',data_only=True).active.values if r[1] and isinstance(r[8],(int,float))}
    assert len(expected)==1423
    keys=set()
    for r in parsed.records:
        key=(r.values[1],r.values[5])
        assert key not in keys
        keys.add(key)
        assert not validate_values(r.values,COLS)[1]
        for i,(actual,wanted,c) in enumerate(zip(r.values,expected[key],COLS)):
            if c['data_type']=='decimal':
                assert (not actual and wanted is None) or (actual and wanted is not None and Decimal(actual)==Decimal(str(wanted)))
            else:
                # The supplied reference contains three UTF-8/CP437 mojibake tails.
                wanted=(str(wanted) if wanted is not None else '').removesuffix('┬á').strip()
                assert actual==wanted,(key,i,actual,wanted)
    assert keys==set(expected)


def test_page_header_does_not_break_multiline_description():
    text=(ROOT/'samples/ovol_stock_valuation_20260930.txt').read_text()
    parsed=StockValuationParser().parse(text,COLS)
    r=next(r for r in parsed.records if r.values[1]=='CSF22ONCRASY373')
    assert r.values[3]=='1917373'
    assert r.values[4].startswith('W=')


def test_stock_unknown_line_before_data_is_retained():
    r=StockValuationParser().parse('   UNEXPECTED SOURCE LINE',COLS)
    assert len(r.issues)==1
    assert r.issues[0]['line_no']==1


def test_delimited_parser_retains_wrong_column_count():
    r=DelimitedParser('|').parse('A|"a|b"|10\nbad|line',[{}, {}, {}])
    assert r.records[0].values==['A','a|b','10']
    assert len(r.issues)==1


def test_fixed_width_rejects_unmapped_suffix():
    cols=[dict(start_pos=0,end_pos=3),dict(start_pos=3,end_pos=6)]
    r=FixedWidthParser().parse('ABC123\nDEF456lost',cols)
    assert r.records[0].values==['ABC','123']
    assert len(r.issues)==1


def test_required_and_optional_numeric_validation():
    values,errors=validate_values(['',''],[dict(name='Required',data_type='text',required=True),dict(name='Optional',data_type='decimal',required=False)])
    assert errors==['Required: required.']
    assert values==['','']
