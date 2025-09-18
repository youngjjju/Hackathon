##라즈베리파이 핀 활성화, 터미널: sudo raspi-config
##pip3 install gpiozero
##3.3v 확인
import RPi.GPIO as GPIO
import spidev
from sx127x import SX127x


##gpio 랑 spi 초기설정##
GPIO.setmode(GPIO.BMC)

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1000000


####sx127x 송수신 단계#####

### LORA 모듈이랑 연결되는 라즈베리파이 핀 넘버 입력해야됨 아래에
NSS = 17
RESET = 0
DI0 = 22

controller = SX127x(spi, GPIO, nss_pin=NSS, reset_pin=RESET, di0_pin=DI0)


### lora 통신 주파수 설정
controller.set_frequency(915)
controller.set_spreading_factor(7)  ##높을수록 느리고 멀리, 잡음 영향x 6~12
controller.set_tx_power(14)   ####높을수록 멀리멀리 ~20

#### LORA 송신

controller.send_packet("Hello lora my love")


### lora 수신


### 1. callback 함수 지정하기
## >>>payload 는 알아서 sx127x 함수에서 받아오는 수신값임
def callback(payload):
    print("elon musk")

### 2. lora 수신 시 실행될 함수
controller.on_receive(callback)


### 3. 수신모드로 전환

controller.set_mode_rx()


#### 끄고싶으면 controller.sleep()
