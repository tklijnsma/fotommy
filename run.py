import os
from fotommy import app

def run_server():
    if 'macbook' in os.environ.get('HOSTNAME',''):
        app.run(port=5000)
    else:
        app.run(
            host='0.0.0.0',
            port=23457,
            ssl_context = (
                # 'cert.pem',
                # 'key.pem',
                '/etc/letsencrypt/live/amelienorah.nl/fullchain.pem',
                '/etc/letsencrypt/live/amelienorah.nl/privkey.pem'
                ),
            threaded=True,
            debug=False
            )

if __name__ == "__main__":
    run_server()