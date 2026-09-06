#include <iostream>
#include <string>
#include <cstring>
#include "../modbus/modbus_parser.h"
#include "../dnp3/dnp3_parser.h"
#include "../models/normalized_command.h"

using namespace voltguard;

void print_help() {
    std::cout << "VoltGuard Protocol Parser CLI\n"
              << "Usage: voltguard_parser [options]\n\n"
              << "Options:\n"
              << "  --hex <hex_string>    Raw hexadecimal packet payload\n"
              << "  --protocol <modbus|dnp3> Protocol type (default: modbus)\n"
              << "  --src <source_ip>     Source IP address (default: 192.168.1.20)\n"
              << "  --dest <dest_ip>      Destination IP address (default: 192.168.1.50)\n"
              << "  --help                Show this help message\n";
}

int main(int argc, char* argv[]) {
    std::string hex_input;
    std::string protocol = "modbus";
    std::string src_ip = "192.168.1.20";
    std::string dest_ip = "192.168.1.50";

    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--hex") == 0 && i + 1 < argc) {
            hex_input = argv[++i];
        } else if (std::strcmp(argv[i], "--protocol") == 0 && i + 1 < argc) {
            protocol = argv[++i];
        } else if (std::strcmp(argv[i], "--src") == 0 && i + 1 < argc) {
            src_ip = argv[++i];
        } else if (std::strcmp(argv[i], "--dest") == 0 && i + 1 < argc) {
            dest_ip = argv[++i];
        } else if (std::strcmp(argv[i], "--help") == 0) {
            print_help();
            return 0;
        }
    }

    if (hex_input.empty()) {
        // Fallback demo packet if no hex string is provided
        // 00 01 00 00 00 06 01 06 9C 41 C3 50 (FC 06, Register 40001, Value 50000)
        hex_input = "00010000000601069C41C350";
    }

    models::NormalizedCommand result;

    if (protocol == "dnp3" || protocol == "DNP3") {
        dnp3::Dnp3Parser parser;
        result = parser.parse_hex(hex_input, src_ip, dest_ip);
    } else {
        modbus::ModbusParser parser;
        result = parser.parse_hex(hex_input, src_ip, dest_ip);
    }

    std::cout << result.to_json() << std::endl;
    return result.success ? 0 : 1;
}
