# Build the RP2040 tiller firmware with the arduino-cli that comes with Arduino IDE 2, and
# optionally upload it.
#   .\build.ps1                 compile; the UF2 is copied to firmware\bin\
#   .\build.ps1 -Upload         compile and upload to a board held in BOOTSEL (shows as a drive)
#   .\build.ps1 -Upload -Port COM7   compile and upload to the running tiller on that port
# Needs the core "Raspberry Pi Pico/RP2040" (rp2040:rp2040) installed in the IDE Boards Manager.
param([switch]$Upload, [string]$Port = "UF2_Board")

$cli = "C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe"
$cfg = Join-Path $env:USERPROFILE ".arduinoIDE\arduino-cli.yaml"
$fqbn = "rp2040:rp2040:rpipico:usbstack=tinyusb"
$sketch = Join-Path $PSScriptRoot "Airbus_Tiller_RP2040"
$build = Join-Path $env:TEMP "airbus_tiller_build"
$bin = Join-Path $PSScriptRoot "bin"

& $cli --config-file $cfg compile --fqbn $fqbn --warnings all --output-dir $build $sketch
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
New-Item -ItemType Directory -Force $bin | Out-Null
Copy-Item (Join-Path $build "Airbus_Tiller_RP2040.ino.uf2") (Join-Path $bin "Airbus_Tiller_RP2040.uf2") -Force

if ($Upload) {
    & $cli --config-file $cfg upload --fqbn $fqbn -p $Port --input-dir $build $sketch
    exit $LASTEXITCODE
}
