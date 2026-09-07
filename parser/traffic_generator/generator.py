"""
VoltGuard Industrial Traffic Generator CLI

Generates industrial Modbus/TCP and DNP3 payload scenarios across specified operational modes:
    - normal: Standard operational traffic within safe parameters
    - suspicious: Boundary testing, rapid setpoint shifts, unusual IPs
    - attack: High-rpm overspeed attacks, pipeline overpressure exploits
    - mixed: Interleaved blend of normal, suspicious, and attack traffic
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from parser.traffic_generator.normal_traffic import generate_normal_traffic
from parser.traffic_generator.suspicious_traffic import generate_suspicious_traffic
from parser.traffic_generator.attack_traffic import generate_attack_traffic


class IndustrialTrafficGenerator:
    """
    Orchestrates traffic generation across execution modes.
    """

    @staticmethod
    def generate(mode: str = "normal", count: int = 10) -> List[Dict[str, Any]]:
        mode = mode.lower()
        if mode == "normal":
            return generate_normal_traffic(count)
        elif mode == "suspicious":
            return generate_suspicious_traffic(count)
        elif mode == "attack":
            return generate_attack_traffic(count)
        elif mode == "mixed":
            n_normal = max(1, int(count * 0.5))
            n_suspicious = max(1, int(count * 0.3))
            n_attack = max(1, count - n_normal - n_suspicious)

            traffic = (
                generate_normal_traffic(n_normal) +
                generate_suspicious_traffic(n_suspicious) +
                generate_attack_traffic(n_attack)
            )
            random.shuffle(traffic)
            # Re-index
            for idx, item in enumerate(traffic, 1):
                item["id"] = idx
            return traffic
        else:
            raise ValueError(f"Unknown traffic generation mode: {mode}")


def main():
    parser = argparse.ArgumentParser(description="VoltGuard Industrial Traffic Generator CLI")
    parser.add_argument("--mode", type=str, choices=["normal", "suspicious", "attack", "mixed"], default="normal",
                        help="Traffic generation mode (default: normal)")
    parser.add_argument("--count", type=int, default=10, help="Number of packets to generate (default: 10)")
    parser.add_argument("--rate", type=float, default=0.0, help="Rate limit in FPS / delay between packets in seconds")
    parser.add_argument("--output", type=str, choices=["console", "json", "file"], default="console",
                        help="Output destination (default: console)")
    parser.add_argument("--file", type=str, default="generated_traffic.json", help="File path if output=file")

    args = parser.parse_args()

    print(f"[VOLTGUARD TRAFFIC GENERATOR] Generating {args.count} packets in '{args.mode.upper()}' mode...")
    traffic_items = IndustrialTrafficGenerator.generate(mode=args.mode, count=args.count)

    if args.output == "json":
        print(json.dumps(traffic_items, indent=2))
    elif args.output == "file":
        output_file = Path(args.file)
        output_file.write_text(json.dumps(traffic_items, indent=2), encoding="utf-8")
        print(f"[VOLTGUARD TRAFFIC GENERATOR] Saved {len(traffic_items)} packets to {output_file.resolve()}")
    else:  # console format
        for item in traffic_items:
            print(f"[{item['category']}] ID #{item['id']} | Protocol: {item['protocol']} | "
                  f"Src: {item['source_ip']} -> Dest: {item['destination_ip']}")
            print(f"  HEX Payload: {item['hex_payload']}")
            print(f"  Description: {item['description']}")
            print("-" * 75)

            if args.rate > 0:
                time.sleep(1.0 / args.rate if args.rate > 0 else args.rate)


if __name__ == "__main__":
    main()
