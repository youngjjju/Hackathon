import time
import RPi.GPIO as GPIO
from LoRaRF import SX127x

# BCM 모드 사용
GPIO.setmode(GPIO.BCM)

# 핀 설정 (예: 너가 연결한 핀 번호)
RESET = 25
BUSY = -1        # BUSY 핀이 없으면 -1
DIO1 = 24        # DIO1 또는 DIO0에 해당 IRQ 핀 (라이브러리 내부 매핑 확인)
TXEN = -1
RXEN = -1

# LoRa 인스턴스 생성
lora = SX127x()

def lora_init():
    # SPI, 핀 설정 (필요하면)
    lora.setSPI(0, 0, 7_800_000)  # 예: bus=0, cs=0, 속도 7.8MHz
    lora.setPins(RESET, BUSY, DIO1, TXEN, RXEN)
    
    # begin 호출
    ok = lora.begin()
    if not ok:
        print("LoRa begin failed")
        return False

    # RF 설정
    lora.setFrequency(433_000_000)
    lora.setLoRaModulation(sf=7, bw=125_000, cr=5, low_datarate_opt=False)
    lora.setTxPower(17, 1)   # 두번째 인자는 라이브러리 상수 확인
    lora.setRxGain(0)           # 기본 gain
    lora.setLoRaPacket(header_type=0, preamble=8, payload_len=255, crc_enable=True, invert_iq=False)
    lora.setSyncWord(0x12)  

    # IRQ 콜백
    lora.onReceive(on_packet)

    # 연속 수신 모드 요청
    lora.request(lora.RX_CONTINUOUS)

    print("LoRa init OK, listening mode set")
    return True

def on_packet(data_bytes):
    # 콜백으로 받는 데이터가 바이트 배열 형태로 넘어옴
    try:
        msg = bytes(data_bytes).decode('utf-8', errors='ignore')
    except:
        msg = str(data_bytes)   ##### 디코딩 실패하면 그냥 숫자로라도 나오게
    print("Received:", msg)
    print("RSSI:", lora.packetRssi(), "SNR:", lora.snr())
    ## 위에건 신호세기랑 노이즈 역 비율 (높을수록 노이즈 없음)

def lora_send(msg: str):
    lora.beginPacket()
    lora.write(msg.encode('utf-8'))
    lora.endPacket()
    lora.wait()
    print("Sent:", msg)

    # 송신 후 다시 수신 모드
    lora.request(lora.RX_CONTINUOUS)

if __name__ == '__main__':
    if not lora_init():
        exit(1)

    try:
        while True:
            lora_send("Hello LoRaRF")
            time.sleep(10)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Exit")
