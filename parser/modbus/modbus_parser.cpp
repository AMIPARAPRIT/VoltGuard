#include "modbus_parser.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <chrono>
#include <ctime>
#include <algorithm>

namespace voltguard {
namespace modbus {

std::string ModbusParser::current_iso_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto in_time_t = std::chrono::system_clock::to_time_t(now);
    
    std::tm buf{};
#if defined(_WIN32) || defined(_WIN64)
    gmtime_s(&buf, &in_time_t);
#else
    gmtime_r(&in_time_t, &buf);
#endif

    std::ostringstream ss;
    ss << std::put_time(&buf, "%Y-%m-%dT%H:%M:%SZ");
    return ss.str();
}

std::vector<uint8_t> ModbusParser::hex_to_bytes(const std::string& hex) {
    std::vector<uint8_t> bytes;
    std::string clean_hex;
    
    for (char c : hex) {
        if (std::isxdigit(static_cast<unsigned char>(c))) {
            clean_hex += c;
        }
    }

    if (clean_hex.length() % 2 != 0) {
        return bytes; // Invalid length
    }

    for (size_t i = 0; i < clean_hex.length(); i += 2) {
        std::string byteString = clean_hex.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(strtol(byteString.c_str(), nullptr, 16));
        bytes.push_back(byte);
    }
    return bytes;
}

models::NormalizedCommand ModbusParser::parse_hex(const std::string& hex_string,
                                                   const std::string& source_ip,
                                                   const std::string& dest_ip) {
    std::vector<uint8_t> bytes = hex_to_bytes(hex_string);
    if (bytes.empty() && !hex_string.empty()) {
        models::NormalizedCommand err_cmd;
        err_cmd.timestamp = current_iso_timestamp();
        err_cmd.source_ip = source_ip;
        err_cmd.destination_ip = dest_ip;
        err_cmd.protocol = "Modbus/TCP";
        err_cmd.success = false;
        err_cmd.error = "Malformed hex payload string format.";
        return err_cmd;
    }
    return parse_bytes(bytes, source_ip, dest_ip);
}

models::NormalizedCommand ModbusParser::parse_bytes(const std::vector<uint8_t>& bytes,
                                                    const std::string& source_ip,
                                                    const std::string& dest_ip) {
    models::NormalizedCommand cmd;
    cmd.timestamp = current_iso_timestamp();
    cmd.source_ip = source_ip;
    cmd.destination_ip = dest_ip;
    cmd.protocol = "Modbus/TCP";

    // Modbus/TCP minimum length: 7 bytes (MBAP Header) + 1 byte (FC) + minimum payload
    if (bytes.size() < 8) {
        cmd.success = false;
        cmd.error = "Invalid Modbus/TCP packet length (minimum 8 bytes required).";
        return cmd;
    }

    // Extract MBAP Header
    uint16_t transaction_id = (bytes[0] << 8) | bytes[1];
    uint16_t protocol_id    = (bytes[2] << 8) | bytes[3];
    uint16_t length         = (bytes[4] << 8) | bytes[5];
    uint8_t unit_id         = bytes[6];
    uint8_t function_code   = bytes[7];

    cmd.function_code = function_code;

    // Validate length vs received packet bytes
    if (bytes.size() < static_cast<size_t>(6 + length)) {
        cmd.success = false;
        cmd.error = "Modbus packet length header mismatch (truncated payload).";
        return cmd;
    }

    std::clog << "[PARSER] Modbus/TCP packet received (Transaction ID: " << transaction_id << ")\n";

    if (function_code == FunctionCode::READ_HOLDING_REGISTERS) { // FC 03
        if (bytes.size() < 12) {
            cmd.success = false;
            cmd.error = "Invalid payload length for FC 03 (Read Holding Registers).";
            return cmd;
        }
        uint16_t reg_addr = (bytes[8] << 8) | bytes[9];
        uint16_t reg_qty  = (bytes[10] << 8) | bytes[11];
        
        RegisterDefinition reg_def = m_register_map.get_mapping(reg_addr);
        cmd.device_id = reg_def.default_device_id;
        cmd.register_address = reg_addr;
        cmd.command = "READ_REGISTERS";
        cmd.value = static_cast<double>(reg_qty);
        cmd.unit = "COUNT";

        std::clog << "[PARSER] Device = " << cmd.device_id << "\n";
        std::clog << "[PARSER] Function = READ_HOLDING_REGISTERS\n";
        std::clog << "[PARSER] Register = " << reg_addr << "\n";
        std::clog << "[PARSER] Value = " << reg_qty << "\n";
        std::clog << "[NORMALIZER] Command = READ_REGISTERS\n";
        std::clog << "[NORMALIZER] Unit = COUNT\n";

    } else if (function_code == FunctionCode::WRITE_SINGLE_REGISTER) { // FC 06
        if (bytes.size() < 12) {
            cmd.success = false;
            cmd.error = "Invalid payload length for FC 06 (Write Single Register).";
            return cmd;
        }
        uint16_t reg_addr = (bytes[8] << 8) | bytes[9];
        uint16_t reg_val  = (bytes[10] << 8) | bytes[11];

        RegisterDefinition reg_def = m_register_map.get_mapping(reg_addr);
        cmd.device_id = reg_def.default_device_id;
        cmd.register_address = reg_addr;
        cmd.command = reg_def.command;
        cmd.value = static_cast<double>(reg_val);
        cmd.unit = reg_def.unit;

        std::clog << "[PARSER] Device = " << cmd.device_id << "\n";
        std::clog << "[PARSER] Function = WRITE_SINGLE_REGISTER\n";
        std::clog << "[PARSER] Register = " << reg_addr << "\n";
        std::clog << "[PARSER] Value = " << reg_val << "\n";
        std::clog << "[NORMALIZER] Command = " << cmd.command << "\n";
        std::clog << "[NORMALIZER] Unit = " << cmd.unit << "\n";

    } else if (function_code == FunctionCode::WRITE_MULTIPLE_REGISTERS) { // FC 16 (0x10)
        if (bytes.size() < 13) {
            cmd.success = false;
            cmd.error = "Invalid payload length for FC 16 (Write Multiple Registers).";
            return cmd;
        }
        uint16_t reg_addr = (bytes[8] << 8) | bytes[9];
        uint16_t reg_qty  = (bytes[10] << 8) | bytes[11];
        uint8_t byte_cnt  = bytes[12];

        if (bytes.size() < static_cast<size_t>(13 + byte_cnt)) {
            cmd.success = false;
            cmd.error = "Invalid payload length for FC 16 register byte data.";
            return cmd;
        }

        uint16_t first_val = (bytes[13] << 8) | bytes[14];
        RegisterDefinition reg_def = m_register_map.get_mapping(reg_addr);
        cmd.device_id = reg_def.default_device_id;
        cmd.register_address = reg_addr;
        cmd.command = reg_def.command;
        cmd.value = static_cast<double>(first_val);
        cmd.unit = reg_def.unit;

        std::clog << "[PARSER] Device = " << cmd.device_id << "\n";
        std::clog << "[PARSER] Function = WRITE_MULTIPLE_REGISTERS\n";
        std::clog << "[PARSER] Register = " << reg_addr << "\n";
        std::clog << "[PARSER] Value = " << first_val << "\n";
        std::clog << "[NORMALIZER] Command = " << cmd.command << "\n";
        std::clog << "[NORMALIZER] Unit = " << cmd.unit << "\n";

    } else {
        cmd.success = false;
        cmd.error = "Unsupported function code: " + std::to_string(function_code);
        return cmd;
    }

    return cmd;
}

} // namespace modbus
} // namespace voltguard
