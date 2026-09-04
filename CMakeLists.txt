cmake_minimum_required(VERSION 3.20)
project(VoltGuard VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Enable testing
enable_testing()

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/core/protocols/modbus/include
)

# VoltGuard Core Library
add_library(voltguard_core
    core/protocols/modbus/src/modbus_parser.cpp
)

# Subdirectories
add_subdirectory(tests/unit)
