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
DIO0  = 24    # TxDone 핀

# LoRa 컨트롤러 객체 생성
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

    # 통신 파라미터 맞추기
    controller.set_freq(433E6)       # 433 MHz
    controller.set_spreading_factor(7)  # SF7
    controller.set_bandwidth(125E3)     # 125 kHz
    controller.set_coding_rate(5)       # CR 4/5
    controller.set_pa_config(pa_select=1, max_power=7, output_power=15)  # PA_BOOST 출력

    controller.set_mode(SX127x.MODE_STDBY)   # 송신 준비 모드
    print("LoRa TX init done.")
    return True

def lora_send(data: bytes):
    controller.write_payload(list(data))     # FIFO에 데이터 쓰기
    controller.set_mode(SX127x.MODE_TX)      # 송신 시작
    print("Sending packet...")

    # 송신 완료 대기 (DIO0 핀 = TxDone)
    while GPIO.input(DIO0) == 0:
        time.sleep(0.01)

    controller.clear_irq_flags(TxDone=1)     # TxDone 플래그 클리어
    print("Send done!")

# 실행부
if __name__ == "__main__":
    if lora_init():
        while True:
            msg = "Hello LoRa!".encode("utf-8")
            lora_send(msg)
            time.sleep(2)
