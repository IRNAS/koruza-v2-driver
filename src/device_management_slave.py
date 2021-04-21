import logging
import logging.handlers

import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from ...src.constants import DEVICE_MANAGEMENT_PORT, KORUZA_MAIN_PORT, OTHER_UNIT_IP

log = logging.getLogger()

filename = "./koruza_v2/logs/device_management_log.log"
logging.basicConfig(format='%(asctime)s - %(module)s - %(levelname)s - %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
rotate_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=10485760, backupCount=4)
rotate_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%d/%m/%Y %H:%M:%S'))
logging.getLogger().addHandler(rotate_handler)

log = logging.getLogger()
log.info("-------------- NEW RUN with logging enabled --------------")

class DeviceManagement():
    def __init__(self):
        print("Initing device management")
        # pass

        self.remote_device_client = xmlrpc.client.ServerProxy(f"http://{OTHER_UNIT_IP}:{DEVICE_MANAGEMENT_PORT}", allow_none=True)
        self.local_koruza_client = xmlrpc.client.ServerProxy(f"http://localhost:{KORUZA_MAIN_PORT}", allow_none=True)

        self.mode = "slave"

    def request_remote(self, command, params):
        """
        Used locally from koruza.py
        Request remote command over one of the available channels
        TODO: enable multiple channels in config, only local network is supported for now

        Only used to pipe command to remote endpoint!
        """

        if self.mode == "slave":
            return

        print(f"Received remote request command: {command}, params: {params}")

        response = self.remote_device_client.handle_remote_request(command, params)
        print(f"Received response from remote: {response}")

        # with xmlrpc.client.ServerProxy(f"http://{REMOTE_UNIT_IP}:{DEVICE_MANAGEMENT_PORT}", allow_none=True) as client:
        #     print(f"Issuing ble command {command} with {params}")
        #     response = client.handle_remote_request(command, params)
        #     return response

    def handle_remote_request(self, command, params):
        """
        Exposed externally as endpoint for remote calls
        """

        # TODO parse command and params to call correct koruza method
        # with xmlrpc.client.ServerProxy(f"http://localhost:{KORUZA_MAIN_PORT}", allow_none=True) as client:

        print(f"Handling remote request: {command} with params {params}")

        if command == "get_sfp_data":
            response = self.local_koruza_client.get_sfp_data()

        if command == "get_motors_position":
            response = self.local_koruza_client.get_motors_position()

        if command == "move_motors":
            response = self.local_koruza_client.move_motors(*params)  # unpack params

        if command == "home":
            response = self.local_koruza_client.home()

        if command == "disable_led":
            response = self.local_koruza_client.disable_led()

        print(f"Response from slave unit: {response}")
        return response

print("Device management called")
if __name__ == "__main__":
    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    with SimpleXMLRPCServer(("0.0.0.0", DEVICE_MANAGEMENT_PORT),  # expose to outside
                            requestHandler=RequestHandler, allow_none=True, logRequests=True) as server:
        server.register_introspection_functions()
        server.register_instance(DeviceManagement())
        log.info(f"Serving XML-RPC on 192.168.13.226 port {DEVICE_MANAGEMENT_PORT}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            log.info("\nKeyboard interrupt received, exiting.")
            # sys.exit(0)
