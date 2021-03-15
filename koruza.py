from threading import Thread, Lock

from hardware.ws281x import LEDDriver
from src.tlv_protocol import *

class Koruza():
    def __init__(self):

        self.status_report = {
            "snr": None,
            "leds": None,
            "error_report":
            {
                "code": None
            },
            "motors":
            {
                "x": None,
                "y": None,
                "z": None,
                "encoder_x": None,
                "encoder_y": None
            },
        }

        self.status = {
            "snr": None,
            "gpio_reset": None,
            "leds": None,
            "error_report":
            {
                "code": None
            },
            "motors":
            {
                "connected": None,
                "x": None,
                "y": None,
                "z": None,
                "range_x": None,
                "range_y": None,
                "encoder_x": None,
                "encoder_y": None
            },
            "camera_calibration":
            {
                "port": None,
                "path": None,
                "width": None,
                "height": None,
                "offset_x": None,
                "offset_y": None,
                "global_offset_x": None,
                "global_offset_y": None,
                "zoom_x": None,
                "zoom_y": None,
                "zoom_w": None,
                "zoom_h": None,
                "distance": None
            },
            "sfp":
            {
                "tx_power": None,
                "rx_power": None
            }
        }

        self.lock = Lock()

    def incoming_message_loop(self):
        """Listen for message from motor driver"""
        while self.motor_wrapper_running:
            self.lock.acquire()
            line = self.ser.readline()
            self.lock.release()
            # parse motor driver message into tlv objects
            message_result, decoded_message = message_parse(line)

            # handle tlvs
            for index, tlv in enumerate(decoded_message):
                # message is REPLY
                if tlv.type == TlvType.TLV_REPLY:  # if of type reply
                    if tlv.value == TlvReply.REPLY_STATUS_REPORT:  # if value of reply is status report

                        # set motor connected
                        if not self.status["motors"]["connected"]:
                            self.status["motors"]["connected"] = True
                            self.koruza_restore_motor()  # TODO implement

                        # get motor position
                        if decoded_message[index + 1].type == TlvType.TLV_MOTOR_POSITION:
                            motor_pos = tlv.value
                            self.status["motors"]["x"] = motor_pos.x
                            self.status["motors"]["y"] = motor_pos.y
                            self.status["motors"]["z"] = motor_pos.z

                            # update motor position (when in range)
                            if self.status["motors"]["x"] >= -self.status["motors"]["range_x"] and self.status["motors"]["x"] <= self.status["motors"]["range_x"]
                            and self.status["motors"]["y"] >= -self.status["motors"]["range_y"] and self.status["motors"]["y"] <= self.status["motors"]["range_y"]:
                                self.status_report["motors"]["x"] = self.status["motors"]["x"]
                                self.status_report["motors"]["y"] = self.status["motors"]["y"]

                        # handle encoder value report
                        if decoded_message[index + 1].type == TlvType.TLV_ENCODER_VALUE:
                            encoder_value = tlv.value
                            self.status["encoder_value"]["x"] = encoder_value.x
                            self.status["encoder_value"]["y"] = encoder_value.y

                    if tlv.value == TlvReply.REPLY_ERROR_REPORT:
                        if decoded_message[index + 1].type == TlvType.TLV_ERROR_REPORT:
                            error = tlv.value
                            self.status["errors"]["code"] = error.code

                # message is COMMAND
                if tlv.type == TlvType.TLV_COMMAND:
                    if tlv.value == TlvCommand.COMMAND_RESTORE_MOTOR:
                        self.koruza_restore_motor()  # TODO implement

    def koruza_reboot(self):
        """Reboot koruza"""

        encoded_message = EnocdedMessage()
        cmd_reboot = create_command_tlv(TlvCommand.COMMAND_REBOOT)
        encoded_message.add(cmd_reboot)
        checksum = create_checksum_tlv(encoded_message.tlvs)
        encoded_message.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message)  # send message over serial
        self.lock.release()
        return True

    def koruza_firmware_upgrade(self):
        """Update koruza firmware"""

        encoded_message = EnocdedMessage()
        cmd_fw_upgrade = create_command_tlv(
            TlvCommand.COMMAND_FIRMWARE_UPGRADE)
        encoded_message.add(cmd_fw_upgrade)
        checksum = create_checksum_tlv(encoded_message.tlvs)
        encoded_message.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message)  # send message over serial
        self.lock.release()
        return True

    def koruza_hard_reset(self):
        """Hard reset koruza unit"""
        # TODO implement gpio commands
        pass

    def koruza_update_sfp_leds(self):
        """Update sfp leds"""
        rx_power_dbm = 10.0 * \
            math.log10(self.status["sfp"]["rx_power"] / 10000.0)
        if rx_power_dbm < -40.0:
            rx_power_dbm = -40.0  # is this ok?

        # TODO change LED color

    def koruza_update_status(self):
        """Read sfp driver data"""
        self.koruza_update_sfp()
        self.koruza_update_sfp_leds()

        encoded_message = EncodedMessage()
        cmd_get_status = create_command_tlv(TlvCommand.COMMAND_GET_STATUS)
        power_reading = create_power_reading_tlv(
            self.status["sfp"]["rx_power"])
        encoded_message.add_tlv(cmd_get_status)
        encoded_message.add_tlv(power_reading)
        checksum = create_checksum_tlv(encoded_message)
        encoded_message.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message)  # send message over serial
        self.lock.release()
        return True

    def koruza_calibration_forward_transform(self):
        """Calibration forward transform"""
        self.status["camera_calibration"]["offset_x"] = self.status["camera_calibration"]["global_offset_x"] - \
            self.status["camera_calibration"]["zoom_x"] * \
            self.status["camera_calibration"]["width"] / self.status["camera_calibration"]["zoom_w"]

        self.status["camera_calibration"]["offset_y"] = self.status["camera_calibration"]["global_offset_y"] - \
            self.status["camera_calibration"]["zoom_y"] * \
            self.status["camera_calibration"]["height"] / self.status["camera_calibration"]["zoom_h"]

    def koruza_calibration_inverse_transform(self):
        """Calibration inverse transform"""
        self.status["camera_calibration"]["global_offset_x"] = self.status["camera_calibration"]["offset_x"] * \
            self.status["camera_calibration"]["zoom_w"] + \
            self.status["camera_calibration"]["zoom_x"] * self.status["camera_calibration"]["width"]

        self.status["camera_calibration"]["global_offset_y"] = self.status["camera_calibration"]["offset_y"] * \
            self.status["camera_calibration"]["zoom_h"] + \
            self.status["camera_calibration"]["zoom_y"] * self.status["camera_calibration"]["height"]

    def koruza_set_webcam_calibration(self, offset_x, offset_y):
        # Given offsets are in zoomed-in coordinates, so we need to transform them
        # to global coordinates based on configured zoom levels.
        self.status["camera_calibration"]["offset_x"] = offset_x
        self.status["camera_calibration"]["offset_y"] = offset_y
        self.koruza_calibration_inverse_transform()

    def koruza_set_distance(distance):
        """Set camera distance"""
        self.status["camera_calibration"]["distance"] = distance
