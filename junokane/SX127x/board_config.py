import RPi.GPIO as GPIO

class BoardConfig:
    def __init__(self, spi, gpio, nss_pin, reset_pin, dio0_pin):
        self.spi = spi
        self.gpio = gpio
        self.nss_pin = nss_pin
        self.reset_pin = reset_pin
        self.dio0_pin = dio0_pin

        gpio.setmode(GPIO.BCM)
        gpio.setup(self.nss_pin, GPIO.OUT)
        gpio.setup(self.reset_pin, GPIO.OUT)
        gpio.setup(self.dio0_pin, GPIO.IN)

        gpio.output(self.nss_pin, 1)
        gpio.output(self.reset_pin, 1)