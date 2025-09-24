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

def on_packet(channel):
    payload = controller.read_payload()
    print("Received:", bytes(payload).decode("utf-8", errors="ignore"))
    controller.clear_irq_flags(RxDone=1)   # 플래그 클리어

if __name__ == "__main__":
    if lora_init():
        # DIO0 핀에 이벤트 감지 → HIGH 될 때 콜백 실행
        GPIO.add_event_detect(DIO0, GPIO.RISING, callback=on_packet)

        print("Listening for packets...")
        try:
            while True:
                time.sleep(1)  # 메인 루프는 그냥 대기
        except KeyboardInterrupt:
            GPIO.cleanup()



#########################################################
# 계속 수신모드 키고 콜백함수 지정해놓은 후 gpio 콜백함수 적어놓고 지내면 됨
# 그러다가 보내고싶으면 바로 controller.send_packet
# 엄준식
# send_packet 마친 후 controller.set_mode(SX127x.MODE_RXCONT)