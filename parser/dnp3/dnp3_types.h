#pragma once

#include <cstdint>
#include <string>

namespace voltguard {
namespace dnp3 {

enum Dnp3FunctionCode : uint8_t {
    READ            = 0x01,
    WRITE           = 0x02,
    SELECT          = 0x03,
    OPERATE         = 0x04,
    DIRECT_OPERATE  = 0x05,
    RESPONSE        = 0x81
};

struct Dnp3Header {
    uint16_t sync;               // 0x0564
    uint8_t length;
    uint8_t control;
    uint16_t dest_address;       // Little-endian
    uint16_t src_address;        // Little-endian
    uint16_t header_crc;
    uint8_t function_code;
    uint8_t group;
    uint8_t variation;
};

} // namespace dnp3
} // namespace voltguard
