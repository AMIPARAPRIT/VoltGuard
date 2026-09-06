#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include "dnp3_types.h"
#include "../models/normalized_command.h"

namespace voltguard {
namespace dnp3 {

class Dnp3Parser {
public:
    Dnp3Parser() = default;

    /**
     * Parse a hex string representation of a DNP3 packet into NormalizedCommand.
     */
    models::NormalizedCommand parse_hex(const std::string& hex_string,
                                        const std::string& default_src_ip = "192.168.1.50",
                                        const std::string& default_dest_ip = "192.168.1.10");

    /**
     * Parse raw binary bytes of a DNP3 packet into NormalizedCommand.
     */
    models::NormalizedCommand parse_bytes(const std::vector<uint8_t>& bytes,
                                         const std::string& default_src_ip = "192.168.1.50",
                                         const std::string& default_dest_ip = "192.168.1.10");

private:
    static std::vector<uint8_t> hex_to_bytes(const std::string& hex);
    static std::string current_iso_timestamp();
};

} // namespace dnp3
} // namespace voltguard
