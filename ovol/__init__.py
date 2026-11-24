"""Application factory: test databases never overwrite working data."""
import os
from pathlib import Path
import secrets
import hmac
from flask import Flask, session, request, abort, render_template
from werkzeug.exceptions import SecurityError
from .db import get_db, init_db


def create_app(test_config=None):
    app=Flask(__name__,instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True,exist_ok=True)
    secret_path=Path(app.instance_path)/'session.key'
    if not secret_path.exists():
        try:
            with secret_path.open('x') as f:
                f.write(secrets.token_hex(32))
            secret_path.chmod(0o600)
        except FileExistsError:
            pass
    app.config.from_mapping(SECRET_KEY=os.environ.get('OVOL_SECRET_KEY') or secret_path.read_text(),
          DATABASE=str(Path(app.instance_path)/'ovol.sqlite3'),MAX_CONTENT_LENGTH=6*1024*1024,
          SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Strict',TRUSTED_HOSTS=['127.0.0.1','localhost'])
    if test_config:
        app.config.update(test_config)

    def csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token']=secrets.token_hex(32)
        return session['csrf_token']
    app.jinja_env.globals['csrf_token']=csrf_token

    @app.before_request
    def protect_forms():
        if request.method in ('POST','PUT','PATCH','DELETE'):
            given=request.form.get('csrf_token') or request.headers.get('X-CSRF-Token','')
            expected=session.get('csrf_token','')
            if not expected or not hmac.compare_digest(given,expected):
                abort(400,description='The form expired. Refresh the page and try again.')

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control']='no-store'
        return response

    @app.teardown_appcontext
    def close_db(error):
        from flask import g
        db=g.pop('db',None)
        if db is not None:
            db.rollback()
            db.close()

    for status in (400,404,409,413):
        def handler(error):
            if isinstance(error,SecurityError):
                return 'Invalid host. Open http://127.0.0.1:5000 on this workstation.',400,{'Content-Type':'text/plain; charset=utf-8'}
            message='Upload is too large. Select a TXT file up to 5 MB.' if error.code==413 else error.description
            return render_template('error.html',title=f'Error {error.code}',message=message),error.code
        app.register_error_handler(status,handler)

    from .blueprints import reports, templates, review, exports
    for module in (reports,templates,review,exports):
        app.register_blueprint(module.bp)
    with app.app_context():
        first_run=get_db().execute("SELECT name FROM sqlite_master WHERE type='table' AND name='templates'").fetchone() is None
        init_db()
        from .seed import seed_templates
        if first_run:
            seed_templates()
    return app
