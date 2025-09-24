import time
from .constants import *
from .board_config import BoardConfig

class SX127x(BoardConfig):
    def __init__(self, spi, gpio, nss_pin, reset_pin, dio0_pin):
        super().__init__(spi, gpio, nss_pin, reset_pin, dio0_pin)

    def reset(self):
        self.gpio.output(self.reset_pin, 0)
        time.sleep(0.1)
        self.gpio.output(self.reset_pin, 1)
        time.sleep(0.1)

    def read_reg(self, addr):
        self.gpio.output(self.nss_pin, 0)
        val = self.spi.xfer2([addr & 0x7F, 0x00])
        self.gpio.output(self.nss_pin, 1)
        return val[1]

    def write_reg(self, addr, val):
        self.gpio.output(self.nss_pin, 0)
        self.spi.xfer2([addr | 0x80, val])
        self.gpio.output(self.nss_pin, 1)

    def set_mode(self, mode):
        self.write_reg(REG_OP_MODE, mode)

    def set_freq(self, freq):
        frf = int((freq / 32e6) * (1 << 19))
        self.write_reg(REG_FRF_MSB, (frf >> 16) & 0xFF)
        self.write_reg(REG_FRF_MID, (frf >> 8) & 0xFF)
        self.write_reg(REG_FRF_LSB, frf & 0xFF)

    def set_spreading_factor(self, sf):
        reg = self.read_reg(REG_MODEM_CONFIG2)
        self.write_reg(REG_MODEM_CONFIG2, (reg & 0x0F) | ((sf << 4) & 0xF0))

    def set_bandwidth(self, bw):
        reg = self.read_reg(REG_MODEM_CONFIG1)
        self.write_reg(REG_MODEM_CONFIG1, (reg & 0x0F) | ((bw << 4) & 0xF0))

    def set_coding_rate(self, cr):
        reg = self.read_reg(REG_MODEM_CONFIG1)
        self.write_reg(REG_MODEM_CONFIG1, (reg & 0xF1) | ((cr << 1) & 0x0E))

    def read_payload(self):
        irq_flags = self.read_reg(REG_IRQ_FLAGS)
        self.write_reg(REG_IRQ_FLAGS, 0xFF)
        if irq_flags & IRQ_RX_DONE_MASK:
            current_addr = self.read_reg(REG_FIFO_RX_CURRENT_ADDR)
            received_count = self.read_reg(REG_RX_NB_BYTES)
            self.write_reg(REG_FIFO_ADDR_PTR, current_addr)
            payload = []
            for i in range(received_count):
                payload.append(self.read_reg(REG_FIFO))
            return payload
        return []