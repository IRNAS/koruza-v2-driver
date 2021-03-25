
# ========== I2C ====================

#RPi I2C channel
I2C_CHANNEL = 1

#SFP ADDRESSES
SFP_TRANSMIT = 0  # sfp identifier
SFP_RECEIVE = 1
#MUX ADDRESS

# =========== TLV ===================
#
#
#

# =========== NETWORK ===============
LOCALHOST = ""   # TODO find a way to implement below code:
"""
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
LOCALHOST = s.getsockname()[0]
"""