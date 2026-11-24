import pytest
from ovol import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING':True,'DATABASE':str(tmp_path/'test.sqlite3'),'SECRET_KEY':'test-only-key'})


@pytest.fixture
def client(app):
    c=app.test_client()
    c.get('/reports/new')
    return c


@pytest.fixture
def post(client):
    def send(path,values=None,**kwargs):
        with client.session_transaction() as session:
            token=session['csrf_token']
        return client.post(path,data=dict(values or {},csrf_token=token),**kwargs)
    return send
