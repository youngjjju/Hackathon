import spidev
import RPi.GPIO as GPIO
import time
from SX127x.SX127x import SX127x

# SPI 초기화
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 5000000

# 핀 설정
NSS   = 8
RESET = 25
DIO0  = 24

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

    # 기본 파라미터.... 통신 거리랑 출력 등등 센더랑 리시버 맞춰야됨
    controller.set_freq(433E6)
    controller.set_spreading_factor(7)
    controller.set_bandwidth(125E3)
    controller.set_coding_rate(5)
    controller.set_pa_config(pa_select=1, max_power=7, output_power=15)

    controller.set_mode(SX127x.MODE_STDBY)
    print("LoRa TX init done.")
    return True

if __name__ == "__main__":
    if lora_init():
        while True:
            msg = "Hello LoRa!".encode("utf-8") ###여기서 msg 적으면 됨.
            controller.send_packet(list(msg))   # 그냥 이 한 줄이면 송신 끝
            print("Send done!")
            time.sleep(2)

##############################
# 
