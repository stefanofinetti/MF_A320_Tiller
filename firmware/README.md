# Tiller firmware

| Folder | What |
|---|---|
| `Airbus_Tiller_RP2040/` | Firmware for the v2 tiller: RP2040 board, Pico form factor |
| `bin/Airbus_Tiller_RP2040.uf2` | Ready-built firmware, made by `build.ps1` |

## What the RP2040 does

The board is a USB game controller called **Airbus Tiller** (VID 2E8A, PID 10F1). Its own HID
descriptor has only the axis and the button below, so MSFS finds nothing else to bind:

- **Axis X** is the tiller: −32767 full left, 0 at the centre, +32767 full right. Each side of the
  centre is scaled on its own, so the centre you feel is always 0. A dead band round the centre
  (default 2 % of half travel) can be changed.
- **Button 1** is PEDALS DISC. The G-Switch is self-locking, so the button reads pressed while it is
  latched and released when it is out. That matches the real button, which disconnects the pedals
  for as long as it is held.
- **USB serial port**, 115200 baud, for calibration.

The readings are averaged and filtered (16 samples every 1 ms, smoothed, with a small hysteresis), so
the axis is steady with the handle at rest.

## Wiring

The pin numbers in brackets are the physical pins of a Pico. Check them on the clone's silkscreen.

| From | To |
|---|---|
| Pot, one end | 3V3 OUT (36) |
| Pot, other end | AGND (33) |
| Pot, wiper (middle pin) | GP26 / ADC0 (31) |
| G-Switch, one wire | GP2 (4) |
| G-Switch, other wire | GND (3) |

The internal pull-up is used, so the switch needs no resistor. If the axis turns the wrong way,
swap the two ends of the pot, or invert the axis in MSFS.

## Putting the firmware on the board

- **The first time, without tools:** hold BOOTSEL and plug the board in. A drive called RPI-RP2
  appears. Copy `bin/Airbus_Tiller_RP2040.uf2` onto it; the board restarts as Airbus Tiller.
- **From the source:** run `.\build.ps1`, or `.\build.ps1 -Upload` for a board in BOOTSEL, or
  `.\build.ps1 -Upload -Port COMx` for a board already running the tiller. It uses the
  arduino-cli of Arduino IDE 2 and needs the core "Raspberry Pi Pico/RP2040" from the Boards
  Manager.
- **From the Arduino IDE:** board "Raspberry Pi Pico", USB stack **"Adafruit TinyUSB"** (with "Pico
  SDK" it does not compile). The name and the VID/PID are set in the sketch.
- **If Windows still shows the old layout** (many axes and 32 buttons, from the first version), it is
  its cache: in Device Manager uninstall the "Airbus Tiller" game controller and plug the board in
  again.

## Calibration

Open the serial port (the IDE Serial Monitor at 115200, line ending "Newline") and type:

1. `c`, with the handle let go at its centre;
2. `l`, with the handle held at the left stop;
3. `r`, with the handle held at the right stop;
4. `d 20`, the dead band in per mille of half travel (0 … 200), if a different one is wanted;
5. `w` to write it to flash.

`s` shows the raw value, the axis and the button state, `m` repeats that ten times a second, and `x`
goes back to the defaults. Until a calibration is written, the defaults assume the pot centred,
using 225° of its ~270°.

## Fenix A320 in MSFS 2024

- **Tiller:** in the MSFS controls, Airbus Tiller axis X → **Nose Wheel Steering Axis**. The rudder
  pedals stay on Rudder Axis.
- **PEDALS DISC:** MSFS has no standard control for it, and the Fenix handles it with its own
  variable. In **MobiFlight**, add an input on the joystick Airbus Tiller, button 1: on press set
  `L:S_FC_CAPT_TILLER_PEDAL_DISCONNECT` to 1, on release set it to 0. The MobiFlight firmware is
  **not** used: MobiFlight reads the button straight off the joystick.

  The variable name is confirmed on HubHop (user, 2026-11-05). The HubHop preset
  "FNX320 Misc Tiller Pedal Disconnect Captain Press" is only MobiFlight's ready-made code for
  writing it; the sim sees the variable either way.
