#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>

namespace voltguard {
namespace modbus {

enum FunctionCode : uint8_t {
    READ_HOLDING_REGISTERS = 0x03,
    WRITE_SINGLE_REGISTER  = 0x06,
    WRITE_MULTIPLE_REGISTERS = 0x10
};

struct MbapHeader {
    uint16_t transaction_id;
    uint16_t protocol_id;
    uint16_t length;
    uint8_t unit_id;
};

struct RegisterDefinition {
    std::string command;      // e.g. "SET_RPM"
    std::string description;  // e.g. "Pump RPM"
    std::string unit;         // e.g. "RPM"
    std::string default_device_id; // e.g. "Pump-01"
};

class RegisterMap {
public:
    RegisterMap() {
        // Initialize standard VoltGuard industrial register mappings
        m_map[40001] = {"SET_RPM", "Pump RPM", "RPM", "Pump-01"};
        m_map[40002] = {"SET_VALVE", "Valve Position", "%", "Valve-01"};
        m_map[40003] = {"SET_PRESSURE", "Pressure Setpoint", "bar", "Pressure-Sensor-01"};
        m_map[40004] = {"SET_TEMPERATURE", "Temperature Setpoint", "°C", "Temp-Sensor-01"};
    }

    void register_mapping(uint16_t reg, const std::string& command, const std::string& desc, const std::string& unit, const std::string& device_id = "PLC-01") {
        m_map[reg] = {command, desc, unit, device_id};
    }

    bool has_mapping(uint16_t reg) const {
        return m_map.find(reg) != m_map.end();
    }

    RegisterDefinition get_mapping(uint16_t reg) const {
        auto it = m_map.find(reg);
        if (it != m_map.end()) {
            return it->second;
        }
        return {"UNKNOWN_COMMAND", "Unknown Register", "RAW", "PLC-01"};
    }

private:
    std::unordered_map<uint16_t, RegisterDefinition> m_map;
};

} // namespace modbus
} // namespace voltguard
