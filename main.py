import logging
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from .src.koruza import Koruza

# config loggers
logging.getLogger("filelock").disabled = True # disable filelock logger
# logging.getLogger("xmlrpc.server").disabled = True # disable filelock logger

filename = "./koruza_v2/logs/koruza_log.log"
logging.basicConfig(format='%(asctime)s - %(module)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
rotate_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=10485760, backupCount=4)
rotate_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%d/%m/%Y %H:%M:%S'))
logging.getLogger().addHandler(rotate_handler)

log = logging.getLogger()
log.info("-------------- NEW RUN with logging enabled --------------")

if __name__ == "__main__":
    # Restrict to a particular path.
    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    with SimpleXMLRPCServer(('localhost', 8000),
                            requestHandler=RequestHandler, allow_none=True, logRequests=False) as server:
        server.register_introspection_functions()
        server.register_instance(Koruza())
        log.info("Serving XML-RPC on localhost port 8000")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            log.info("\nKeyboard interrupt received, exiting.")
            # sys.exit(0)

