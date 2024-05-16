import argparse
import ssl

import uvicorn

from app.config import Settings

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to bind on')
    parser.add_argument('-r', '--reload', type=bool, default=False, help='Reload when changes found')
    parser.add_argument('-s', '--settings', type=str, default='settings.json', help='Settings file name')

    args = parser.parse_args()

    settings = Settings()

    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=args.port,
        reload=args.reload,
        ssl_cert_reqs=ssl.CERT_REQUIRED,
        ssl_version=ssl.PROTOCOL_TLSv1_2,
        ssl_keyfile=settings.server_key_file,
        ssl_certfile=settings.server_cert_file,
        ssl_ca_certs=settings.ca_file
    )
