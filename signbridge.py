# import monkeypatch before everything else so gevent can 
# patch them with gevent-friendly functions asap
from gevent import monkey
monkey.patch_all()

import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db, socketio
from app.models import User
import signal
import sys

app = create_app()
HOST = "127.0.0.1"
PORT = 5000

# this context processor is used to test database operations
# remove it in production
@app.shell_context_processor
def make_shell_context():
    return {'sa': sa, 'so': so, 'db': db, 'User': User}

# gracefully handle shutdown
# not required but i would like to not be panic texted
# about a Big Scary Error named "keyboard interrupt"
def handle_shutdown(sig, frame):
    print("\nShutting down server...")
    app.logger.info("Received shutdown signal")
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_shutdown)
    
    print(f"\nDevelopment server running at: http://{HOST}:{PORT}\n")
    app.logger.info(f"Development server URL: http://{HOST}:{PORT}")

    socketio.run(app, host=HOST, port=PORT, debug=True, use_reloader=False)

