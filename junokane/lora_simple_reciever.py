import time
from LoRaRF import SX127x
import RPi.GPIO as GPIO

# 핀 번호 (BCM 기준)
RESET = 25
DIO0  = 24

# LoRa 컨트롤러 객체
controller = SX127x(spi_bus=0, spi_cs=0, reset_pin=RESET, dio0_pin=DIO0)

def lora_init():
    ok = controller.begin(
        frequency=433E6,
        bw=125E3,
        sf=7,
        cr=5,
        syncWord=0x12,
        power=17,
        preambleLength=8,
        gain=0
    )
    if not ok:
        print("LoRa chip not found or init failed!")
        return False

    print("LoRa RX init done.")
    return True

def on_packet(channel):
    # 수신 데이터 읽기
    if controller.available() > 0:
        data = []
        while controller.available() > 0:
            data.append(controller.read())
        print("Received:", bytes(data).decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    if lora_init():
        # DIO0 핀 이벤트 감지 → HIGH 될 때 콜백 실행
        GPIO.add_event_detect(DIO0, GPIO.RISING, callback=on_packet)

        print("Listening for packets...")
        try:
            while True:
                time.sleep(1)  # 메인 루프는 대기만 함
        except KeyboardInterrupt:
            GPIO.cleanup()
