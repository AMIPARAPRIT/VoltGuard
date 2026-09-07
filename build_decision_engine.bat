@echo off
echo Building VoltGuard Rust Decision Engine...
if not exist build mkdir build
cargo build --release
if %ERRORLEVEL% EQU 0 (
    copy target\release\decision_engine.exe build\decision_engine.exe /Y
    echo Build successful! Binary copied to build/decision_engine.exe
) else (
    echo Cargo build failed with error code %ERRORLEVEL%
)
