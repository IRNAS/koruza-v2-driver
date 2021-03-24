
# ========== I2C ====================

#RPi I2C channel
I2C_CHANNEL_RPI = 1

#SFP ADDRESSES

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