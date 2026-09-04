#include <gtest/gtest.h>
#include "modbus_parser.hpp"

using namespace voltguard::modbus;

TEST(ModbusParserTest, ParseValidWriteSingleRegisterHex) {
    // Transaction 01, Protocol 0, Length 6, Unit 1, FC 6, Reg 100, Val 2500
    // hex: 0001 0000 0006 01 06 0064 09C4
    std::string hex_payload = "0001000000060106006409C4";
    
    ModbusCommand cmd = ModbusParser::parse_hex(hex_payload);

    EXPECT_EQ(cmd.transaction_id, 1);
    EXPECT_EQ(cmd.protocol_id, 0);
    EXPECT_EQ(cmd.length, 6);
    EXPECT_EQ(cmd.unit_id, 1);
    EXPECT_EQ(cmd.function_code, 6);
    EXPECT_EQ(cmd.register_address, 100);
    EXPECT_EQ(cmd.value, 2500);
}

TEST(ModbusParserTest, ParseMaliciousWriteSingleRegisterHex) {
    // hex: 0002 0000 0006 01 06 0064 C350 (Value: 50000)
    std::string hex_payload = "00020000000601060064C350";
    
    ModbusCommand cmd = ModbusParser::parse_hex(hex_payload);

    EXPECT_EQ(cmd.transaction_id, 2);
    EXPECT_EQ(cmd.value, 50000);
}

TEST(ModbusParserTest, ParseInvalidShortPacket) {
    std::string hex_payload = "000100000006010600";
    
    EXPECT_THROW({
        ModbusParser::parse_hex(hex_payload);
    }, std::invalid_argument);
}
