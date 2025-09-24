import time
import RPi.GPIO as GPIO
from LoRaRF import SX127x

# 핀 번호 (BCM 기준)
RESET = 25    # LoRa Reset 핀
DIO0  = 24    # LoRa DIO0 핀 (RxDone, TxDone 이벤트)

# LoRa 컨트롤러 객체
controller = SX127x(spi_bus=0, spi_cs=0, reset_pin=RESET, dio0_pin=DIO0)

# ✅ 초기화
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
        print("❌ LoRa chip not found or init failed!")
        return False

    # 수신 모드 진입
    controller.request()
    print("✅ LoRa RX init done.")
    return True

# ✅ 수신 콜백
def on_packet(channel):
    if controller.available() > 0:
        data = []
        while controller.available() > 0:
            data.append(controller.read())
        msg = bytes(data).decode("utf-8", errors="ignore")
        print("📩 Received:", msg)

# ✅ 송신 함수
def lora_send(msg: str):
    controller.beginPacket()
    controller.write(msg.encode("utf-8"))
    controller.endPacket()
    controller.wait()  # 송신 완료 대기
    print("📤 Sent:", msg)

    # 송신 후 다시 수신 모드
    controller.request()

# 실행부
if __name__ == "__main__":
    if lora_init():
        # 이벤트 감지: DIO0 Rising → on_packet 실행
        GPIO.add_event_detect(DIO0, GPIO.RISING, callback=on_packet)

        print("✨ LoRa 송수신기 준비 완료 (RX 대기 + 필요 시 TX)")

        try:
            while True:
                # 예시: 10초마다 메시지 송신
                lora_send("Hello from TXRX")
                time.sleep(10)

        except KeyboardInterrupt:
            print("\n프로그램 종료")
            GPIO.cleanup()
