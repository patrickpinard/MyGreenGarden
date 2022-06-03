import smbus
from time import sleep

# bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

DEVICE_ADDRESS = 0x38  # 7 bit address (will be left shifted to add the read write bit)
ALTERNATE_DEVICE_ADDRESS = 0x20  # 7 bit address (will be left shifted to add the read write bit)

RELAY8_INPORT_REG_ADD = 0x00
RELAY8_OUTPORT_REG_ADD = 0x01
RELAY8_POLINV_REG_ADD = 0x02
RELAY8_CFG_REG_ADD = 0x03

#relayMaskRemap = [0x01, 0x04, 0x40, 0x10, 0x20, 0x80, 0x08, 0x02]  #original
relayMaskRemap = [0x02, 0x08, 0x80, 0x20, 0x10, 0x40, 0x04, 0x01]
#relayChRemap = [0, 2, 6, 4, 5, 7, 3, 1]  #original
relayChRemap = [1, 3, 7, 5, 4, 6, 2, 0]

def __relayToIO(relay):
    val = 0
    for i in range(0, 8):
        if (relay & (1 << i)) != 0:
            val = val + relayMaskRemap[i]
    return val


def __IOToRelay(iov):
    val = 0
    for i in range(0, 8):
        if (iov & relayMaskRemap[i]) != 0:
            val = val + (1 << i)
    return val


def __check(bus, add):
    cfg = bus.read_byte_data(add, RELAY8_CFG_REG_ADD)
    if cfg != 0:
        bus.write_byte_data(add, RELAY8_CFG_REG_ADD, 0)
        bus.write_byte_data(add, RELAY8_OUTPORT_REG_ADD, 0)
    return bus.read_byte_data(add, RELAY8_INPORT_REG_ADD)


def set(stack, relay, value):
    if stack < 0 or stack > 7:
        raise ValueError('Invalid stack level!')
    stack = 0x07 ^ stack
    if relay < 1:
        raise ValueError('Invalid relay number!')
    if relay > 8:
        raise ValueError('Invalid relay number!')
    bus = smbus.SMBus(1)
    hwAdd = DEVICE_ADDRESS + stack
    try:
        oldVal = __check(bus, hwAdd)
    except Exception as e:
        hwAdd = ALTERNATE_DEVICE_ADDRESS + stack
        try:
            oldVal = __check(bus, hwAdd)
        except Exception as e:
            bus.close()
            raise ValueError('8-relay card not detected!')
    oldVal = __IOToRelay(oldVal)
    try:
        if value == 0:
            oldVal = oldVal & (~(1 << (relay - 1)))
            oldVal = __relayToIO(oldVal)
            bus.write_byte_data(hwAdd, RELAY8_OUTPORT_REG_ADD, oldVal)
        else:
            oldVal = oldVal | (1 << (relay - 1))
            oldVal = __relayToIO(oldVal)
            bus.write_byte_data(hwAdd, RELAY8_OUTPORT_REG_ADD, oldVal)
    except Exception as e:
        bus.close()
        raise ValueError('Fail to write relay state value!')
    bus.close()


def set_all(stack, value):
    if stack < 0 or stack > 7:
        raise ValueError('Invalid stack level!')
    stack = 0x07 ^ stack
    if value > 255:
        raise ValueError('Invalid relay value!')
    if value < 0:
        raise ValueError('Invalid relay value!')

    bus = smbus.SMBus(1)
    hwAdd = DEVICE_ADDRESS + stack
    try:
        oldVal = __check(bus, hwAdd)
    except Exception as e:
        hwAdd = ALTERNATE_DEVICE_ADDRESS + stack
        try:
            oldVal = __check(bus, hwAdd)
        except Exception as e:
            bus.close()
            raise ValueError('8-relay card not detected!')
    value = __relayToIO(value)
    try:
        bus.write_byte_data(hwAdd, RELAY8_OUTPORT_REG_ADD, value)
    except Exception as e:
        bus.close()
        raise ValueError('Fail to write relay state value!')
    bus.close()


def get(stack, relay):
    if stack < 0 or stack > 7:
        raise ValueError('Invalid stack level!')
    stack = 0x07 ^ stack
    if relay < 1:
        raise ValueError('Invalid relay number!')
    if relay > 8:
        raise ValueError('Invalid relay number!')
    bus = smbus.SMBus(1)
    hwAdd = DEVICE_ADDRESS + stack
    try:
        val = __check(bus, hwAdd)
    except Exception as e:
        hwAdd = ALTERNATE_DEVICE_ADDRESS + stack
        try:
            val = __check(bus, hwAdd)
        except Exception as e:
            bus.close()
            raise ValueError('8-relay card not detected!')

    val = __IOToRelay(val)
    val = val & (1 << (relay - 1))
    bus.close()
    if val == 0:
        return 0
    else:
        return 1


def get_all(stack):
    if stack < 0 or stack > 7:
        raise ValueError('Invalid stack level!')
    stack = 0x07 ^ stack
    bus = smbus.SMBus(1)
    hwAdd = DEVICE_ADDRESS + stack
    try:
        val = __check(bus, hwAdd)
    except Exception as e:
        hwAdd = ALTERNATE_DEVICE_ADDRESS + stack
        try:
            val = __check(bus, hwAdd)
        except Exception as e:
            bus.close()
            raise ValueError('8-relay card not detected!')

    val = __IOToRelay(val)
    bus.close()
    return val

if __name__ == "__main__":

    set(0,1,1)
    sleep(1)
    set(0,2,1)
    sleep(1)
    set(0,3,1)
    sleep(1)
    set(0,4,1)
    sleep(1)
    set(0,5,1)
    sleep(1)
    set(0,6,1)
    sleep(1)
    set(0,7,1)
    sleep(1)
    set(0,8,1)
    sleep(1)
    set(0,1,0)
    sleep(1)
    set(0,2,0)
    sleep(1)
    set(0,3,0)
    sleep(1)
    set(0,4,0)
    sleep(1)
    set(0,5,0)
    sleep(1)
    set(0,6,0)
    sleep(1)
    set(0,7,0)
    sleep(1)
    set(0,8,0)
