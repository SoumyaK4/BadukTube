import logging
import signal
import sys

from app import app

def signal_handler(sig, frame):
    logging.info('Shutting down gracefully...')
    sys.exit(0)

if __name__ == '__main__':
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the application (production mode)
    app.run(host='0.0.0.0', port=5000, debug=False)
