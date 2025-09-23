import time
import argparse
from imu import MPU6050
from accident_detect import AccidentDetector

def main():
    # ✅ 터미널 옵션 처리
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="테스트 모드 실행 (랜덤 데이터 + 랜덤 duration)")
    args = parser.parse_args()

    # ✅ 옵션에 따라 imu/test_mode 결정
    imu = MPU6050(test_mode=args.test)
    detector = AccidentDetector(
        threshold=0.8,          # 전체 가속도 크기 임계값 ↓ 민감도 강화
        min_duration=0.0,       # 지속시간 최소 제한 없음
        jerk_threshold=0.2,     # jerk 임계값 ↓ 민감도 강화
        axis_delta_threshold=0.5,  # 축별 순간 변화량 체크 추가
        test_mode=args.test
    )

    mode = "테스트 모드" if args.test else "실제 모드"
    print(f"🚗 IMU 기반 사고 감지 프로그램 시작 ({mode})")

    while True:
        try:
            accel = imu.read_accel()
            accident, mag, jerk, duration, axis_delta = detector.detect(accel)

            if accident:
                print(f"[⚠️ 사고 감지] 크기: {mag:.2f}g, "
                      f"Jerk: {jerk:.2f} g/s, "
                      f"지속시간: {duration:.3f}s, "
                      f"Δ축변화: {axis_delta}, 값: {accel}")
            else:
                print(f"[정상] 크기: {mag:.2f}g, "
                      f"Jerk: {jerk:.2f} g/s, "
                      f"지속시간: {duration:.3f}s, "
                      f"Δ축변화: {axis_delta}")

            time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n프로그램 종료")
            break

if __name__ == "__main__":
    main()
