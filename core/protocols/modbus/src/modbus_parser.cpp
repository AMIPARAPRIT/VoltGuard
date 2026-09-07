#include "modbus_parser.hpp"
#include <iomanip>
#include <sstream>

namespace voltguard {
namespace modbus {

std::vector<uint8_t> ModbusParser::hex_to_bytes(const std::string& hex) {
    std::vector<uint8_t> bytes;
    for (size_t i = 0; i < hex.length(); i += 2) {
        std::string byteString = hex.substr(i, 2);
        uint8_t byte = (uint8_t) strtol(byteString.c_str(), nullptr, 16);
        bytes.push_back(byte);
    }
    return bytes;
}

ModbusCommand ModbusParser::parse_bytes(const std::vector<uint8_t>& bytes) {
    if (bytes.size() < 12) { // Minimum size for a Write Single Register (FC 06)
        throw std::invalid_argument("Packet too short to be a valid Modbus TCP Write Single Register command.");
    }

    ModbusCommand cmd;
    cmd.transaction_id = (bytes[0] << 8) | bytes[1];
    cmd.protocol_id = (bytes[2] << 8) | bytes[3];
    cmd.length = (bytes[4] << 8) | bytes[5];
    cmd.unit_id = bytes[6];
    cmd.function_code = bytes[7];

    if (cmd.function_code == 6) { // Write Single Register
        cmd.register_address = (bytes[8] << 8) | bytes[9];
        cmd.value = (bytes[10] << 8) | bytes[11];
    } else {
        throw std::runtime_error("Unsupported function code.");
    }

    return cmd;
}

ModbusCommand ModbusParser::parse_hex(const std::string& hex_string) {
    std::vector<uint8_t> bytes = hex_to_bytes(hex_string);
    return parse_bytes(bytes);
}

} // namespace modbus
} // namespace voltguard
