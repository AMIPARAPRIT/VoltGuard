@echo off
echo Building VoltGuard C++ Protocol Parser...
if not exist build mkdir build
g++ -std=c++20 -Iparser -Iparser/modbus -Iparser/dnp3 -Iparser/models parser/modbus/modbus_parser.cpp parser/dnp3/dnp3_parser.cpp parser/cli/main.cpp -o build/voltguard_parser.exe
if %ERRORLEVEL% EQU 0 (
    echo Build successful! Binary created at build/voltguard_parser.exe
) else (
    echo Build failed with error code %ERRORLEVEL%
)
