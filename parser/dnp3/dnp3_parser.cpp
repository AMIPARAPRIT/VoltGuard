#include "dnp3_parser.h"
#include <iostream>
#include <iomanip>
#include <sstream>
#include <chrono>
#include <ctime>
#include <cctype>

namespace voltguard {
namespace dnp3 {

std::string Dnp3Parser::current_iso_timestamp() {
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

std::vector<uint8_t> Dnp3Parser::hex_to_bytes(const std::string& hex) {
    std::vector<uint8_t> bytes;
    std::string clean_hex;
    for (char c : hex) {
        if (std::isxdigit(static_cast<unsigned char>(c))) {
            clean_hex += c;
        }
    }
    if (clean_hex.length() % 2 != 0) return bytes;

    for (size_t i = 0; i < clean_hex.length(); i += 2) {
        std::string byteString = clean_hex.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(strtol(byteString.c_str(), nullptr, 16));
        bytes.push_back(byte);
    }
    return bytes;
}

models::NormalizedCommand Dnp3Parser::parse_hex(const std::string& hex_string,
                                                   const std::string& default_src_ip,
                                                   const std::string& default_dest_ip) {
    std::vector<uint8_t> bytes = hex_to_bytes(hex_string);
    if (bytes.empty() && !hex_string.empty()) {
        models::NormalizedCommand err_cmd;
        err_cmd.timestamp = current_iso_timestamp();
        err_cmd.protocol = "DNP3";
        err_cmd.success = false;
        err_cmd.error = "Malformed hex string format for DNP3 frame.";
        return err_cmd;
    }
    return parse_bytes(bytes, default_src_ip, default_dest_ip);
}

models::NormalizedCommand Dnp3Parser::parse_bytes(const std::vector<uint8_t>& bytes,
                                                    const std::string& default_src_ip,
                                                    const std::string& default_dest_ip) {
    models::NormalizedCommand cmd;
    cmd.timestamp = current_iso_timestamp();
    cmd.source_ip = default_src_ip;
    cmd.destination_ip = default_dest_ip;
    cmd.protocol = "DNP3";

    // Minimum DNP3 Data Link Header length is 10 bytes (0x05 0x64 + len + ctrl + dest + src + crc)
    if (bytes.size() < 10) {
        cmd.success = false;
        cmd.error = "Invalid DNP3 frame length (minimum 10 bytes required for link layer header).";
        return cmd;
    }

    // Check Sync Bytes (0x05 0x64)
    if (bytes[0] != 0x05 || bytes[1] != 0x64) {
        cmd.success = false;
        cmd.error = "Invalid DNP3 sync bytes (expected 0x05 0x64).";
        return cmd;
    }

    uint8_t len = bytes[2];
    uint8_t ctrl = bytes[3];
    uint16_t dest_addr = bytes[4] | (bytes[5] << 8); // Little endian
    uint16_t src_addr  = bytes[6] | (bytes[7] << 8); // Little endian

    cmd.device_id = "RTU-" + (dest_addr < 10 ? "0" + std::to_string(dest_addr) : std::to_string(dest_addr));
    
    // Application Layer parsing if available
    uint8_t func_code = 0;
    uint16_t point_index = 0;
    double val = 0.0;
    std::string command_name = "DNP3_COMMAND";
    std::string unit = "RAW";

    if (bytes.size() >= 13) { // Link header (10) + Transport (1) + App Header (2)
        // Skip link CRC (bytes 8, 9) and transport header (byte 10)
        // Byte 11: App Control, Byte 12: App Function Code
        func_code = bytes[12];
        cmd.function_code = func_code;

        if (func_code == Dnp3FunctionCode::READ) {
            command_name = "READ_ANALOG_INPUT";
            unit = "COUNT";
        } else if (func_code == Dnp3FunctionCode::WRITE || 
                   func_code == Dnp3FunctionCode::SELECT || 
                   func_code == Dnp3FunctionCode::OPERATE || 
                   func_code == Dnp3FunctionCode::DIRECT_OPERATE) {
            
            command_name = "SET_ANALOG_OUTPUT";
            unit = "RPM";

            // If object group/variation and value are present
            if (bytes.size() >= 18) {
                uint8_t group = bytes[13];
                uint8_t variation = bytes[14];
                point_index = bytes[15];
                int16_t raw_val = static_cast<int16_t>(bytes[16] | (bytes[17] << 8));
                val = static_cast<double>(raw_val);
                cmd.register_address = point_index;

                if (point_index == 0 || point_index == 1) {
                    command_name = "SET_RPM";
                    unit = "RPM";
                    cmd.device_id = "Pump-01";
                } else if (point_index == 2) {
                    command_name = "SET_VALVE";
                    unit = "%";
                    cmd.device_id = "Valve-01";
                }
            }
        }
    }

    cmd.command = command_name;
    cmd.value = val;
    cmd.unit = unit;

    std::clog << "[PARSER] DNP3 frame received (Src: " << src_addr << " Dest: " << dest_addr << ")\n";
    std::clog << "[PARSER] Device = " << cmd.device_id << "\n";
    std::clog << "[PARSER] Function Code = " << static_cast<int>(func_code) << "\n";
    std::clog << "[NORMALIZER] Command = " << cmd.command << "\n";
    std::clog << "[NORMALIZER] Unit = " << cmd.unit << "\n";

    return cmd;
}

} // namespace dnp3
} // namespace voltguard
