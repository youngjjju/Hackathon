import spidev
import RPi.GPIO as GPIO
import time
from SX127x.SX127x import SX127x

# SPI 초기화
spi = spidev.SpiDev()
spi.open(0, 0)              # SPI0, CS0
spi.max_speed_hz = 5000000  # 5 MHz

# 핀 번호 (BCM 기준)
NSS   = 8     # Chip Select
RESET = 25    # Reset 핀
DIO0  = 24    # RxDone 핀

# LoRa 컨트롤러 객체
controller = SX127x(spi, GPIO, nss_pin=NSS, reset_pin=RESET, dio0_pin=DIO0)

def lora_init():
    controller.reset()
    version = controller.read_reg(0x42)
    print(f"Chip Version: 0x{version:02X}")
    if version != 0x12:
        print("LoRa chip not found!")
        return False

    controller.set_mode(SX127x.MODE_SLEEP)
    time.sleep(0.1)

    controller.set_freq(433E6)                 # 433 MHz
    controller.set_spreading_factor(7)         # SF7
    controller.set_bandwidth(125E3)            # 125 kHz
    controller.set_coding_rate(5)              # CR 4/5
    controller.set_mode(SX127x.MODE_RXCONT)    # 연속 수신 모드

    print("LoRa RX init done.")
    return True

def lora_receive():
    if GPIO.input(DIO0) == 1:     # 패킷 수신 완료 신호
        payload = controller.read_payload()  # FIFO에서 바로 읽기
        print("Received:", bytes(payload).decode("utf-8", errors="ignore"))

# 실행부
if __name__ == "__main__":
    if lora_init():
        while True:
            lora_receive()
            time.sleep(0.1)
