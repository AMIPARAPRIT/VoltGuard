#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <stdexcept>

namespace voltguard {
namespace modbus {

struct ModbusCommand {
    uint16_t transaction_id;
    uint16_t protocol_id;
    uint16_t length;
    uint8_t unit_id;
    uint8_t function_code;
    uint16_t register_address;
    uint16_t value;
};

class ModbusParser {
public:
    static ModbusCommand parse_hex(const std::string& hex_string);
    static ModbusCommand parse_bytes(const std::vector<uint8_t>& bytes);

private:
    static std::vector<uint8_t> hex_to_bytes(const std::string& hex);
};

} // namespace modbus
} // namespace voltguard
