# import monkeypatch before everything else so gevent can 
# patch them with gevent-friendly functions asap
from gevent import monkey
monkey.patch_all()

import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db, socketio
from app.models import User

app = create_app()

# this context processor is used to test database operations
# remove it in production
@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User}

if __name__ == '__main__':
    socketio.run(app, debug=True)