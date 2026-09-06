#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include "modbus_types.h"
#include "../models/normalized_command.h"

namespace voltguard {
namespace modbus {

class ModbusParser {
public:
    explicit ModbusParser(const RegisterMap& map = RegisterMap()) : m_register_map(map) {}

    /**
     * Parse a hex-formatted Modbus/TCP packet string into a NormalizedCommand.
     * Handles whitespace, colons, or clean hex format.
     */
    models::NormalizedCommand parse_hex(const std::string& hex_string,
                                        const std::string& source_ip = "192.168.1.20",
                                        const std::string& dest_ip = "192.168.1.50");

    /**
     * Parse raw binary bytes of a Modbus/TCP packet into a NormalizedCommand.
     */
    models::NormalizedCommand parse_bytes(const std::vector<uint8_t>& bytes,
                                         const std::string& source_ip = "192.168.1.20",
                                         const std::string& dest_ip = "192.168.1.50");

private:
    RegisterMap m_register_map;
    static std::vector<uint8_t> hex_to_bytes(const std::string& hex);
    static std::string current_iso_timestamp();
};

} // namespace modbus
} // namespace voltguard
