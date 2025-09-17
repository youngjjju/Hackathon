import time
import argparse
import logging
import pandas as pd
from collections import deque
from imu import MockIMU
from features import FeatureExtractor
from config import load_config


def parse_args():
    p = argparse.ArgumentParser(description="Crash detect simulator")
    p.add_argument("--dt", type=float, help="Sample period DT_S (sec)")
    p.add_argument("--alpha", type=float, help="LPF alpha (0..1)")
    p.add_argument("--thresh", type=float, help="lin_a threshold (g)")
    p.add_argument("--hold", type=float, help="hold time (ms)")
    p.add_argument("--jerk", type=float, help="jerk threshold (m/s^3)")
    p.add_argument("--inhibit", type=float, help="inhibit time (ms)")
    p.add_argument("--pre", type=int, help="snapshot pre window (ms)")
    p.add_argument("--post", type=int, help="snapshot post window (ms)")
    p.add_argument("--buffer", type=int, help="ring buffer seconds")
    p.add_argument("--logfile", type=str, help="log file path (optional)")
    p.add_argument("--verbose", action="store_true", help="verbose logging")
    return p.parse_args()


class RingBuf:
    def __init__(self, capacity: int):
        self.q = deque(maxlen=capacity)

    def push(self, item: dict):
        self.q.append(item)

    def snapshot(self, start_ms: int, end_ms: int):
        return [it for it in list(self.q) if start_ms <= it["ts_ms"] <= end_ms]


def main():
    # ---- 설정 로드 + 인자 파싱 ----
    cfg = load_config()
    args = parse_args()

    # 명령줄 인자로 덮어쓰기
    if args.dt is not None:        cfg["DT_S"] = args.dt
    if args.alpha is not None:     cfg["LPF_ALPHA"] = args.alpha
    if args.thresh is not None:    cfg["THRESH_G"] = args.thresh
    if args.hold is not None:      cfg["HOLD_MS"] = args.hold
    if args.jerk is not None:      cfg["THRESH_JERK"] = args.jerk
    if args.inhibit is not None:   cfg["INHIBIT_MS"] = args.inhibit
    if args.pre is not None:       cfg["PRE_MS"] = args.pre
    if args.post is not None:      cfg["POST_MS"] = args.post
    if args.buffer is not None:    cfg["BUFFER_SEC"] = args.buffer

    # 로깅 설정
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        filename=args.logfile if args.logfile else None,
        encoding="utf-8"
    )
    log = logging.getLogger("crash")

    # ---- 설정 전개 ----
    DT_S         = cfg["DT_S"]
    LPF_ALPHA    = cfg["LPF_ALPHA"]
    THRESH_G     = cfg["THRESH_G"]
    HOLD_MS      = cfg["HOLD_MS"]
    THRESH_JERK  = cfg["THRESH_JERK"]
    INHIBIT_MS   = cfg["INHIBIT_MS"]
    PRE_MS       = cfg["PRE_MS"]
    POST_MS      = cfg["POST_MS"]
    BUFFER_SEC   = cfg["BUFFER_SEC"]

    imu = MockIMU()
    fe  = FeatureExtractor(alpha=LPF_ALPHA)
    rb  = RingBuf(capacity=int(100 * BUFFER_SEC))  # 100Hz 기준

    print("Init OK, start loop @100Hz (Python)")
    print("Loaded config:", cfg)
    log.info(f"Config: {cfg}")

    over_ms = 0.0
    inhibit_until = -1

    # 약 4초 실행(필요시 조정)
    for i in range(400):
        s = imu.read()
        f = fe.update(DT_S, s["ax"], s["ay"], s["az"])
        now_ms = s["ts_ms"]

        # 버퍼 저장
        rb.push({
            "ts_ms": now_ms,
            "ax": s["ax"], "ay": s["ay"], "az": s["az"],
            "lin": f["lin_a"], "jerk": f["jerk_mps3"]
        })

        # 이벤트 판정 (지속시간 + jerk + 재트리거 금지)
        if now_ms >= inhibit_until:
            if f["lin_a"] >= THRESH_G:
                over_ms += DT_S * 1000.0  # ms 누적
            else:
                over_ms = 0.0

            cond_hold = over_ms >= HOLD_MS
            cond_jerk = abs(f["jerk_mps3"]) >= THRESH_JERK

            if cond_hold and cond_jerk:
                msg = (f"[EVENT] t={now_ms}ms | lin={f['lin_a']:.2f}g, "
                       f"jerk={f['jerk_mps3']:.1f} (hold={over_ms:.0f}ms)")
                print(msg); log.info(msg)

                inhibit_until = now_ms + INHIBIT_MS
                over_ms = 0.0

                # 스냅샷 저장 (사전/사후)
                start = max(0, now_ms - PRE_MS)
                end   = now_ms + POST_MS
                snap = rb.snapshot(start, end)
                out_name = f"snapshot_{now_ms}ms.csv"
                pd.DataFrame(snap).to_csv(out_name, index=False, encoding="utf-8")
                print(f"[SNAPSHOT] saved {len(snap)} rows -> {out_name}")
                log.info(f"SNAPSHOT rows={len(snap)} file={out_name}")

        # 상태 출력(100ms마다)
        if i % 10 == 0:
            msg = f"t={now_ms:4d}ms | lin={f['lin_a']:.3f}g, jerk={f['jerk_mps3']:.1f}"
            print(msg); log.debug(msg)

        time.sleep(DT_S)

    print("Sim end.")
    log.info("Sim end.")


if __name__ == "__main__":
    main()
