cmake_minimum_required(VERSION 3.20)
project(VoltGuard VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/parser
    ${CMAKE_CURRENT_SOURCE_DIR}/parser/modbus
    ${CMAKE_CURRENT_SOURCE_DIR}/parser/dnp3
    ${CMAKE_CURRENT_SOURCE_DIR}/parser/models
)

# VoltGuard Protocol Parser Library
add_library(voltguard_parser_lib
    parser/modbus/modbus_parser.cpp
    parser/dnp3/dnp3_parser.cpp
)

# Standalone Parser Executable
add_executable(voltguard_parser
    parser/cli/main.cpp
)

target_link_libraries(voltguard_parser PRIVATE voltguard_parser_lib)
