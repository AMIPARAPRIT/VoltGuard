import argparse
import random
import time
from datetime import datetime
import json
import uuid
import struct

def generate_modbus_tcp_write_single_register(transaction_id, unit_id, register, value):
    """
    Generates a raw Modbus TCP packet (hex string) for Write Single Register (FC 06)
    """
    protocol_id = 0
    length = 6
    function_code = 6
    
    # Modbus Application Protocol (MBAP) header: 7 bytes
    # Transaction ID (2), Protocol ID (2), Length (2), Unit ID (1)
    mbap = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)
    
    # Protocol Data Unit (PDU): 4 bytes for FC 06
    # Function Code (1), Register Address (2), Value (2)
    pdu = struct.pack('>BHH', function_code, register, value)
    
    packet = mbap + pdu
    return packet.hex().upper()

def generate_event(register, value, is_malicious=False):
    transaction_id = random.randint(1, 65535)
    unit_id = 1
    
    raw_packet_hex = generate_modbus_tcp_write_single_register(transaction_id, unit_id, register, value)
    
    event_id = f"VG-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
    import datetime as dt
    timestamp = datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    
    event = {
        "raw_packet": raw_packet_hex,
        "metadata": {
            "schema_version": "1.0",
            "event_id": event_id,
            "timestamp": timestamp,
            "source": {
                "ip": "192.168.10.20",
                "port": random.randint(40000, 60000)
            },
            "destination": {
                "ip": "192.168.10.50",
                "port": 502
            },
            "protocol": "modbus_tcp"
        },
        "description": "Malicious overspeed" if is_malicious else "Normal operation"
    }
    return event

def main():
    parser = argparse.ArgumentParser(description="VoltGuard Mock Modbus Traffic Generator")
    parser.add_argument('--count', type=int, default=1, help='Number of packets to generate')
    parser.add_argument('--malicious', action='store_true', help='Generate malicious traffic')
    args = parser.parse_args()

    for i in range(args.count):
        if args.malicious:
            # 50,000 RPM (0xC350)
            event = generate_event(register=100, value=50000, is_malicious=True)
        else:
            # Normal speed around 2500 RPM (0x09C4)
            event = generate_event(register=100, value=2500 + random.randint(-100, 100), is_malicious=False)
        
        print(json.dumps(event, indent=2))
        if i < args.count - 1:
            time.sleep(0.5)

if __name__ == '__main__':
    main()
