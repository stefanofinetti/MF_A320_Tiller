// Airbus A320 nosewheel tiller - RP2040 (Raspberry Pi Pico form factor) USB joystick.
//
// Core: arduino-pico (Earle Philhower), board "Raspberry Pi Pico", USB stack "Adafruit TinyUSB".
// The board shows up as the USB game controller "Airbus Tiller" with only:
//   - axis X:   the tiller (potentiometer), -32767 full left ... 0 centre ... +32767 full right
//   - button 1: PEDALS DISC (G-Switch, self-locking: latched = pressed, released = not pressed)
// (its own HID descriptor: no unused axes, hat or buttons for MSFS to bind things to), plus a USB
// serial port (115200) for calibration, see help() below and firmware/README.md.
//
// Wiring (Pico pin numbers in brackets):
//   pot ends   -> 3V3 OUT (36) and AGND (33), wiper -> GP26 / ADC0 (31)
//   G-Switch   -> GP2 (4) and GND (3); internal pull-up, closed = pressed
//
// Calibration (centre and both ends, a dead band round the centre) lives in flash.

#include <Adafruit_TinyUSB.h>
#include <EEPROM.h>

// ---- USB -----------------------------------------------------------------------------------
// Own VID/PID pair, not the plain Pico one: Windows caches a controller's layout and name by VID/PID.
const uint16_t USB_VID = 0x2E8A, USB_PID = 0x10F1;
const char *USB_NAME = "Airbus Tiller";

// one joystick: X axis 16 bit signed, one button, 7 bits of padding
uint8_t const hidReport[] = {
  0x05, 0x01,              // Usage Page (Generic Desktop)
  0x09, 0x04,              // Usage (Joystick)
  0xA1, 0x01,              // Collection (Application)
  0x09, 0x01,              //   Usage (Pointer)
  0xA1, 0x00,              //   Collection (Physical)
  0x09, 0x30,              //     Usage (X)
  0x16, 0x01, 0x80,        //     Logical Minimum (-32767)
  0x26, 0xFF, 0x7F,        //     Logical Maximum (32767)
  0x75, 0x10,              //     Report Size (16)
  0x95, 0x01,              //     Report Count (1)
  0x81, 0x02,              //     Input (Data, Variable, Absolute)
  0xC0,                    //   End Collection
  0x05, 0x09,              //   Usage Page (Button)
  0x19, 0x01,              //   Usage Minimum (1)
  0x29, 0x01,              //   Usage Maximum (1)
  0x15, 0x00,              //   Logical Minimum (0)
  0x25, 0x01,              //   Logical Maximum (1)
  0x75, 0x01,              //   Report Size (1)
  0x95, 0x01,              //   Report Count (1)
  0x81, 0x02,              //   Input (Data, Variable, Absolute)
  0x75, 0x07,              //   Report Size (7)
  0x95, 0x01,              //   Report Count (1)
  0x81, 0x03,              //   Input (Constant): padding to a whole byte
  0xC0                     // End Collection
};
struct __attribute__((packed)) Report {
  int16_t x;
  uint8_t buttons;
};
Adafruit_USBD_HID usbHid;

// ---- pins ----------------------------------------------------------------------------------
const uint8_t PIN_POT = 26;              // GP26 = ADC0
const uint8_t PIN_BUTTON = 2;            // GP2

// ---- filtering -----------------------------------------------------------------------------
// Raw readings are kept as the sum of OVERSAMPLE 12-bit samples (0 ... 65520), then smoothed.
const uint8_t OVERSAMPLE = 16;
const uint8_t EMA_SHIFT = 3;             // exponential average, weight 1/8 per 1 ms step
const int32_t HYSTERESIS = 8;            // in raw units (1/2 of one 12-bit step): no jitter at rest
const uint16_t DEBOUNCE_MS = 20;
const uint32_t KEEPALIVE_MS = 100;       // resend the report at least this often
const int32_t RAW_FULL = 4095L * OVERSAMPLE;

// ---- calibration ---------------------------------------------------------------------------
struct Cal {
  uint32_t magic;
  uint16_t version;
  int32_t left, centre, right;           // raw values at full left, centre, full right
  uint16_t dead;                         // dead band round the centre, per mille of half travel
  uint16_t pad;
  uint32_t check;
};
const uint32_t CAL_MAGIC = 0x54494C4C;   // "TILL"
const uint16_t CAL_VERSION = 1;
Cal cal;

uint32_t calCheck(const Cal &c) {
  const uint8_t *p = (const uint8_t *)&c;
  uint32_t h = 2166136261UL;             // FNV-1a over everything but the check word
  for (size_t i = 0; i < offsetof(Cal, check); i++) h = (h ^ p[i]) * 16777619UL;
  return h;
}

void calDefaults() {
  // The gears turn the pot 225 deg for +-75 deg of handle, of its ~270 deg: about 83 % of the
  // track, centred. Good enough to fly before calibrating.
  int32_t c = RAW_FULL / 2, h = (int32_t)((int64_t)RAW_FULL / 2 * 225 / 270);
  cal = {CAL_MAGIC, CAL_VERSION, c - h, c, c + h, 20, 0, 0};
}

bool calValid(const Cal &c) {
  int32_t dl = c.left - c.centre, dr = c.right - c.centre;
  const int32_t MIN_SPAN = 200L * OVERSAMPLE;   // each side at least 200 12-bit steps
  return ((dl < 0 && dr > 0) || (dl > 0 && dr < 0)) && labs(dl) >= MIN_SPAN && labs(dr) >= MIN_SPAN &&
         c.dead <= 200;
}

void calLoad() {
  EEPROM.get(0, cal);
  if (cal.magic != CAL_MAGIC || cal.version != CAL_VERSION || cal.check != calCheck(cal) || !calValid(cal)) {
    calDefaults();
    Serial.println(F("No calibration in flash: defaults in use."));
  }
}

bool calSave() {
  if (!calValid(cal)) return false;
  cal.check = calCheck(cal);
  EEPROM.put(0, cal);
  return EEPROM.commit();
}

// ---- input ---------------------------------------------------------------------------------
int32_t readRaw() {
  int32_t s = 0;
  for (uint8_t i = 0; i < OVERSAMPLE; i++) s += analogRead(PIN_POT);
  return s;
}

int32_t filtered = 0;                    // smoothed raw, << EMA_SHIFT for precision
int32_t steady = 0;                      // raw value after the hysteresis

void updateRaw() {
  int32_t r = readRaw();
  filtered += r - (filtered >> EMA_SHIFT);
  int32_t f = filtered >> EMA_SHIFT;
  if (labs(f - steady) > HYSTERESIS) steady = f - (f > steady ? HYSTERESIS : -HYSTERESIS);
}

int32_t averageRaw(uint16_t ms) {        // for calibration: the mean over ms milliseconds
  int64_t s = 0;
  uint32_t n = 0, t0 = millis();
  while (millis() - t0 < ms) {
    s += readRaw();
    n++;
  }
  return (int32_t)(s / n);
}

// raw -> axis: each side of the centre scaled on its own, so the felt centre is always 0
int16_t toAxis(int32_t r) {
  int32_t end = ((r - cal.centre) > 0) == ((cal.right - cal.centre) > 0) ? cal.right : cal.left;
  float t = (float)(r - cal.centre) / (float)(end - cal.centre);   // 0 at centre, 1 at that end
  if (t > 1.0f) t = 1.0f;
  float d = cal.dead / 1000.0f;
  t = t <= d ? 0.0f : (t - d) / (1.0f - d);
  float sign = (end == cal.right) ? 1.0f : -1.0f;
  return (int16_t)lroundf(sign * t * 32767.0f);
}

bool buttonState = false, buttonRaw = false;
uint32_t buttonChanged = 0;

void updateButton() {
  bool now = digitalRead(PIN_BUTTON) == LOW;
  if (now != buttonRaw) {
    buttonRaw = now;
    buttonChanged = millis();
  }
  if (buttonRaw != buttonState && millis() - buttonChanged >= DEBOUNCE_MS) buttonState = buttonRaw;
}

// ---- serial commands -----------------------------------------------------------------------
bool monitor = false;
char line[32];
uint8_t lineLen = 0;

void printStatus() {
  Serial.printf("raw %ld (12-bit %ld)  axis %d  button %s\n", (long)steady, (long)(steady / OVERSAMPLE),
                toAxis(steady), buttonState ? "LATCHED" : "off");
  Serial.printf("cal: left %ld  centre %ld  right %ld  dead band %u.%u %%  %s\n", (long)cal.left,
                (long)cal.centre, (long)cal.right, cal.dead / 10, cal.dead % 10,
                calValid(cal) ? "valid" : "NOT VALID (left and right must be on opposite sides)");
}

void help() {
  Serial.println(F(
    "Airbus Tiller - commands (end with Enter):\n"
    "  s        status: raw value, axis, button, calibration\n"
    "  m        monitor on/off (status 10 times a second)\n"
    "  c        handle at centre (let go of it): store the centre\n"
    "  l        handle held at the left stop: store the left end\n"
    "  r        handle held at the right stop: store the right end\n"
    "  d N      dead band round the centre, N per mille of half travel (0 ... 200, default 20)\n"
    "  w        write the calibration to flash\n"
    "  x        back to the defaults (not written until w)\n"
    "  ?        this help"));
}

void command(char *s) {
  while (*s == ' ') s++;
  switch (s[0]) {
    case 's': printStatus(); break;
    case 'm': monitor = !monitor; break;
    case 'c': cal.centre = averageRaw(500); printStatus(); break;
    case 'l': cal.left = averageRaw(500); printStatus(); break;
    case 'r': cal.right = averageRaw(500); printStatus(); break;
    case 'd': {
      long n = atol(s + 1);
      if (n >= 0 && n <= 200) cal.dead = (uint16_t)n;
      printStatus();
      break;
    }
    case 'w': Serial.println(calSave() ? F("Written.") : F("NOT written: calibration not valid.")); break;
    case 'x': calDefaults(); printStatus(); break;
    case '?': case 'h': help(); break;
    case 0: break;
    default: Serial.println(F("? for help"));
  }
}

void readSerial() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\r' || ch == '\n') {
      line[lineLen] = 0;
      if (lineLen) command(line);
      lineLen = 0;
    } else if (lineLen < sizeof(line) - 1) {
      line[lineLen++] = ch;
    }
  }
}

// ---- main ----------------------------------------------------------------------------------
void setup() {
  if (!TinyUSBDevice.isInitialized()) TinyUSBDevice.begin(0);
  TinyUSBDevice.setID(USB_VID, USB_PID);
  TinyUSBDevice.setManufacturerDescriptor("DIY");
  TinyUSBDevice.setProductDescriptor(USB_NAME);
  usbHid.setPollInterval(1);
  usbHid.setReportDescriptor(hidReport, sizeof(hidReport));
  usbHid.setStringDescriptor(USB_NAME);
  usbHid.begin();
  Serial.begin(115200);
  if (TinyUSBDevice.mounted()) {        // enumerated before the HID was added: do it again
    TinyUSBDevice.detach();
    delay(10);
    TinyUSBDevice.attach();
  }
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  analogReadResolution(12);
  EEPROM.begin(256);
  calLoad();

  filtered = readRaw() << EMA_SHIFT;
  steady = readRaw();
  buttonRaw = buttonState = digitalRead(PIN_BUTTON) == LOW;
}

void loop() {
  static uint32_t lastStep = 0, lastSend = 0, lastMon = 0;
  static int16_t sentAxis = 0x7fff;
  static bool sentButton = false;

  uint32_t now = millis();
  if (now == lastStep) {
    readSerial();
    return;
  }
  lastStep = now;

  updateRaw();
  updateButton();
  int16_t axis = toAxis(steady);
  if ((axis != sentAxis || buttonState != sentButton || now - lastSend >= KEEPALIVE_MS) && usbHid.ready()) {
    Report rep = {axis, (uint8_t)(buttonState ? 1 : 0)};
    if (usbHid.sendReport(0, &rep, sizeof(rep))) {
      sentAxis = axis;
      sentButton = buttonState;
      lastSend = now;
    }
  }
  if (monitor && now - lastMon >= 100) {
    lastMon = now;
    printStatus();
  }
  readSerial();
}
