#pragma once

#include <string>
#include <sstream>
#include <iomanip>

namespace voltguard {
namespace models {

/**
 * NormalizedCommand represents a protocol-agnostic industrial command.
 * 
 * Converting protocol-specific frames (Modbus/TCP, DNP3, etc.) into this structure
 * decouples downstream modules (Physics Engine, Decision Engine, Analytics)
 * from raw network payload formats.
 */
struct NormalizedCommand {
    std::string timestamp;        // ISO 8601 timestamp string
    std::string source_ip;        // Source IP address (e.g., "192.168.1.20")
    std::string destination_ip;   // Destination IP address (e.g., "192.168.1.50")
    std::string device_id;        // Identifier of target OT device (e.g., "Pump-01")
    std::string protocol;         // Protocol type ("Modbus/TCP", "DNP3")
    uint8_t function_code = 0;    // Function code (e.g., 3, 6, 16 for Modbus; 1, 2 for DNP3)
    uint16_t register_address = 0;// Register / Point index
    std::string command;          // Normalized command name (e.g., "SET_RPM", "SET_VALVE")
    double value = 0.0;           // Extracted physical target value (e.g., 50000.0)
    std::string unit;             // Physical unit ("RPM", "%", "bar", "°C")
    
    bool success = true;          // Parsing status
    std::string error;            // Error message if success is false

    /**
     * Convert the NormalizedCommand object into a JSON string format.
     */
    std::string to_json() const {
        std::ostringstream ss;
        ss << "{\n";
        ss << "  \"timestamp\": \"" << escape_json(timestamp) << "\",\n";
        ss << "  \"source_ip\": \"" << escape_json(source_ip) << "\",\n";
        ss << "  \"destination_ip\": \"" << escape_json(destination_ip) << "\",\n";
        ss << "  \"device_id\": \"" << escape_json(device_id) << "\",\n";
        ss << "  \"protocol\": \"" << escape_json(protocol) << "\",\n";
        ss << "  \"function_code\": " << static_cast<int>(function_code) << ",\n";
        ss << "  \"register\": " << register_address << ",\n";
        ss << "  \"command\": \"" << escape_json(command) << "\",\n";
        ss << "  \"value\": " << value << ",\n";
        ss << "  \"unit\": \"" << escape_json(unit) << "\",\n";
        ss << "  \"success\": " << (success ? "true" : "false");
        if (!success) {
            ss << ",\n  \"error\": \"" << escape_json(error) << "\"";
        }
        ss << "\n}";
        return ss.str();
    }

private:
    static std::string escape_json(const std::string& str) {
        std::ostringstream ss;
        for (char c : str) {
            if (c == '"') ss << "\\\"";
            else if (c == '\\') ss << "\\\\";
            else if (c == '\b') ss << "\\b";
            else if (c == '\f') ss << "\\f";
            else if (c == '\n') ss << "\\n";
            else if (c == '\r') ss << "\\r";
            else if (c == '\t') ss << "\\t";
            else ss << c;
        }
        return ss.str();
    }
};

} // namespace models
} // namespace voltguard
