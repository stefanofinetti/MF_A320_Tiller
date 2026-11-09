# Tiller assembly

A living document, in the style of the Glareshield `docs/assembly.md`. Steps
are added while the parts are designed, and each one is checked when the unit
is actually built. Unchecked steps are the plan, not experience. Started
2026-10-31. Nothing in it has been printed or tested yet.

It is also the working memory of the design: what we are after, what was
decided and why, where the files are. Read it first after a break or a
context compaction. Decisions are dated; a later one overrides an earlier one.

## Goal

A complete A319/A320/A321 nosewheel steering tiller for the sim: handle,
mechanism and case, with
- the **PEDALS DISC** pushbutton in the handle (push and lock);
- **springs that bring the handle back to zero** when released;
- a linear rotary potentiometer as the sensor;
- an **RP2040** board (Pico form factor) inside the case, a plain USB game controller.

## Requirements

| Problem to avoid | What the design must do |
|---|---|
| Too little room for the push-and-lock button | Size the handle pocket from the real button, with room for its body, travel and wires |
| No return mechanism | Return-to-centre springs, with a clear neutral |
| Tolerances too tight for FDM | Clearances designed for FDM, no fine modelled threads (heat-set inserts, nut traps or tapped holes instead) |
| Weak mechanism that jams | A stiff shaft and support, something the springs cannot twist or tilt |

## Decisions

- **2026-10-31 — The PEDALS DISC button turns with the handle.** It is
  not anchored to the case. Its cap slides in the handle recess, kept from
  turning (since 2026-11-02 by the base guides, the base by two pegs). So its wires turn ±travel with the handle.
- **2026-10-31 — Button later.** An earlier, unchecked version used a
  **7 × 7 self-locking G-Switch**: its pins are PCB pins about 0.2 mm
  thick, and with wires soldered straight to them a couple of twists broke
  a pin. Whatever button v2 uses, its wires must not pull on its pins
  (a small carrier PCB or a strain relief). The base and the mechanism come
  first.
- **2026-11-02 — PEDALS DISC: a printed push-push button with a reed switch.**
  The user wants it to latch down 5 mm (flush with the handle, felt and
  seen) and come back up on the next push. No bought latching button sinks
  that far, so the latch is printed (since 2026-11-03 a heart cam, below) and the state
  is read by a **reed switch** (2.5 × 14, in hand from 2026-11-03) with a
  3 × 2 magnet in the cap: no contact, so the overtravel of the latch does no
  harm. The cap stays Ø29.5, in the Ø30.5 handle recess (the real button's size is
  not known to us). The lettering: see 2026-11-03 below.
- **2026-11-03 — PEDAL DISC lettering in the model, a flush two-colour inlay.**
  The cap prints face down, so Bambu Studio cannot add the text. Each letter
  (OpenBus, `cad/fonts/`, 3.5 high, 0.55 extra spacing so at least 0.5 of
  cap stays between letters) is pocketed 0.4 into the face, two 0.2 layers;
  the same letters are the `ButtonCapLegend` body, printed in white. Both
  bodies sit in the App::Part `ButtonCapAssembly`, which Tiller links. PEDAL
  on top and DISC below follow the rim, their mid-height on a circle r 10
  (the user wants them near the edge: about 3 of black left outside), reading
  from the seat (+Y up); the `leg_*` values in
  `build_mechanism.py` set size, arcs and turn. In Bambu Studio load
  `Tiller-ButtonCap.stl` and `Tiller-ButtonCapLegend.stl` as one object with
  two parts, then flip the whole object.
- **2026-11-03 — PEDALS DISC latch: a heart cam and a steel wire, no rotor.**
  The pen-style rotor printed and the spring worked, but it never stayed
  down: with a 0.4 nozzle its 1.4 mm lugs came out round, and the 1.2 mm
  notch under each rib (an overhang, on supports) came out as a slanted
  bump the lug slid over. A bigger pen latch does not fit: with 4 ribs and
  lugs and a notch big enough to print, the crown, the notch and the
  overtravel need about 5 mm more height than the recess has. The user
  ruled out a 0.2 nozzle with PETG. Now: a plate inside the cap skirt at
  157° (between two barbs, 135° from the reed) carries a heart-shaped
  groove 1.3 × 0.8 on a vertical face; a 0.8 music wire, its short leg
  turning in a radial hole in a boss on the base, rides in it with its tip.
  Press, release: the tip drops into the cleft of the heart and the cap
  stays flush. Press, release: it runs down the other side and the cap comes
  up 5 mm. Overtravel 1.8 (was 3.2); the bottom of the push is the cap tube
  on the relief floor. Skirt, tab, magnet, collar and tab guides stay where
  the reed was bench-tested. Rotor, crown, barrel and ribs are gone; the
  cap must not turn (the tab guides keep it). Drawing:
  `docs/img/button_heart.png`, written by `check_button.py`.

- **2026-11-04 — PEDALS DISC latch: the mechanism of a click pen, whole.**
  The heart cam failed at the first fitting: the two tab guides on the base
  (1.2 × 1.6, 12 high) stood alone once the pen-rotor barrel was gone, and
  broke; the 0.8 wire had to be threaded into the groove blind. Rule from now
  on, for every printed part: nothing freestanding and slender, no wall under
  about 1.6 mm unless it is a closed ring or backed by another part, and no
  fitting step that needs aligning by eye. So the latch is bought, not drawn:
  a click pen. Its body (Ø9.1, cut 17.4 from its top) stands on the shaft
  axis in a hole of the handle, on a ledge; the cap is glued on its button
  stem (cut to stand 11.5 above the body with the pen closed); a refill piece
  (58.8) goes down the shaft bore onto a printed cup, the pen spring 4 × 27,
  and a cap glued on the shaft end. The pen's own travel is 5 mm. The pen holds
  the cap, so no barbs and no lip; the pen button does not turn, so no guides.
  Reed and magnet moved to 247° (the pen body took their place), same distances
  as bench-tested. The user: the travel does not matter, it must work and not
  break.

- **2026-11-04 — PEDALS DISC: a bought 7 × 7 self-locking switch (G-Switch).**
  The click pen does not fit: its fixed teeth run 10.2 … 22.3 below the body
  top and the rotor drops below them when pushed, so the body needs 25 … 27 mm
  where the hub has about 21.6. Back to the plain answer: the user's G-Switch
  (7 × 7 × 7; 12.5 high off, 11.4 latched, 10.65 pushed home; head 3 × 2 × 1).
  Its thin PCB pins (a millefori does not match their pitch) are kept from
  pulling by potting them, with the solder joints, in a well under the switch;
  the wires leave along a groove in the recess floor to the wire bore. The cap
  is glued on the switch head: it shows 1.1 mm up when off and sits flush when
  latched. No reed, no magnet, no pen parts. The reeds bought for the earlier
  designs are not used.

- **2026-10-31 — Travel ±75°**, as the aircraft.
- **2026-10-31 — Centring by cam and compression spring**: a V cam on the
  shaft, a roller pushed onto it by a spring. Gives a felt centre and an
  adjustable force.
- **2026-10-31 — Bearings: 2 × 6001Z (12 × 28 × 8)**, which the user has in
  hand. The user also has 608ZZ (8 × 22 × 7): too small a bore for a
  hollow shaft, but right for the **cam roller**. 6803 only if 6001 proves
  too tight for the wires.
- **2026-10-31 — Potentiometer: to buy**, a 16 mm linear B10K with a 6 mm
  shaft. Exact part to be picked when the bracket is drawn.
- **2026-11-04 — Potentiometer: the user's B10K, in hand** (measured):
  - M7 bushing 6.75 × 6.5 high;
  - knurled split shaft Ø5.82 … 5.83 over the knurls (measured again
    2026-11-06; first read 5.6), 5.5 under them, about 14 teeth,
    13.3 above the bushing; the slot is 1.1 … 1.2 wide and about 11 deep;
  - frame 17.25 × 10.9, 9 from the frame top to the can bottom; can Ø16.8,
    about 17 with the board hooks;
  - pins on the side (pitch 4, 4.5 … 5 under the frame top, 5 out of the
    small board);
  - anti-rotation tab at 90° to the pins, 1.3 radial × 2.3, its inner edge
    4 from the thread, about 2 high;
  - about 270° of rotation; nut 9.9 × 2, washer Ø11.35 × 0.35.

  The shaft is **not cut**. The pot frame sits 1 mm lower, under a 5 mm deck
  (2026-11-06: was a 4 mm deck with a 1 mm boss under it, which kept the deck
  off the bed and needed supports under all of it), so the shaft top ends 0.2 under the gear top and 1.2 under the stop lug.
  The gear is pushed onto the knurls. Its round bore is drawn Ø6.03 and
  prints about 5.83 (2026-11-06: drawn 5.6 it came out 5.4 and did not go
  on); the split shaft springs into it.

- **2026-11-01 — The tiller stands on a desk or a stand**, on TPU or
  anti-slip feet. No fixing to the sim.
- **2026-11-01 — Concept accepted** as drawn below. Gears are fine; extra
  parts do not matter.
- **2026-11-01 — Case on a square plan**, straight walls: a pyramid only
  wastes inner volume.
- **2026-11-01 — Feel.** The centre must be felt without looking (eyes out
  of the window, hand finds "wheels straight"), but **not a hard snap**.
  The end stops must be felt too, but **not hard**, or the user forces them
  and breaks something. So:
  - cam: a force that grows with angle, plus a **shallow, rounded dip at
    centre** (a soft detent: depth well under 1 mm, to tune);
  - the cam ramp steepens over the last 10–15° before ±75°, as a warning;
  - the stop lug hits **TPU bumpers**, not hard plastic.
- **2026-11-01 — Materials** (the user asked for a proposal):
  - **PETG** for everything that carries load or works all the time: shaft,
    cam, roller arm, gears, bearing tower, handle. PLA creeps under a
    constant load (the spring preload never goes away) and breaks brittle;
    PETG is tougher.
  - **PLA** for the case, plates and scale disc: no load, stiffer, more
    accurate.
  - **TPU** for the end-stop bumpers and the feet.
- **2026-11-01 — Part files are PartDesign Bodies with sketches**, so the
  user can change them in the GUI (the button seat in the handle above all).
  Sizes stay on the **Params** sheet of each file; sketch dimensions are
  named constraints bound to it. Measuring works inside a part file; it does
  not work on the links in `Tiller.FCStd`.
- **2026-11-01 — Board: maybe an RP2040** (RP2040-Zero or Pico) instead of
  the Leonardo; to decide with the case. Native USB HID joystick
  (arduino-pico `Joystick.h`), 3.3 V: the pot runs from 3.3 V; its ADC is
  good for ~9–10 clean bits, enough with averaging.

- **2026-11-02 — Board: the RP2040** (Pico form factor clone, in hand),
  not the Leonardo. Like the Leonardo it has native USB, so with the
  arduino-pico core and its built-in `Joystick` library it shows up in
  Windows and MSFS 2024 as a plain USB HID game controller. Printed cradle
  as in the open points, USB-C straight through the case wall.
- **2026-11-05 — Firmware: `firmware/Airbus_Tiller_RP2040`**, a USB
  joystick called "Airbus Tiller" with its own HID descriptor, only one
  axis and one button (the core's Joystick library always reports six
  axes, a hat and 32 buttons, and MSFS binds things to them; Adafruit
  TinyUSB stack instead): axis X is the tiller, calibrated
  (centre and both ends, in flash, each side scaled on its own, a dead
  band) over the USB serial port; button 1 is PEDALS DISC, pressed while
  the G-Switch is latched. The user flies the **Fenix A320**: MSFS has no
  control for its pedal disconnect, so the axis goes to Nose Wheel Steering
  Axis in MSFS and the button to the Fenix variable through **MobiFlight**,
  reading the joystick button (no MobiFlight firmware on the board). Wiring,
  flashing, calibration and the bindings: `firmware/README.md`.

- **2026-11-02 — Case layout**: square plan, axis at the centre, **the
  mechanism turned by 34°** inside it (`mech_rot`), so its long end (spring,
  post, preload screw) goes to the back-right corner: 163 × 163 outside instead of
  about 206 with the mechanism square to the walls. The back is
  +Y and the handle, at centre, points at the back-left corner. The shaft and
  the handle are not turned: the Rotor's D bore and grub screw are turned by
  −34° in its own file, so the flat stays where it was. The USB-C goes out of
  the back wall, the RP2040 sits in the back-left corner.

## Base and mechanism: concept (draft, 2026-10-31)

Assembly frame: Z up along the steering axis, the axis at X = Y = 0,
**Z = 0 on the top face of the case**. The handle sits above, the
mechanism hangs below.

```
        handle hub ───────────── Z ≈ +1 (mounting face, just above the scale disc)
        shaft flange, 3 × M3 into heat-set inserts in the hub
 ═══════ case top + scale disc ═══ Z 0
        ┌ bearing tower ┐
        │  6001Z upper  │          bearing spacing about 30 mm
        │  6001Z lower  │
        └───────────────┘
        V cam + stop lug   ◄── 608ZZ roller on a pivot arm, compression spring
        gear (shaft)  ──── gear (pot), 16 mm B10K on an adjustable bracket
        wire exit, loose loop ──► RP2040 on the case bottom
```

- **Shaft**: printed, OD 12 in the bearings, bore about Ø7 for the button
  wires (two wires and a small plug pass). It carries the cam, the stop lug
  and the gear, keyed on a flat, clamped from below.
- **Handle to shaft**: no printed thread. A flange on the shaft and 3 × M3
  into heat-set inserts in the handle hub, so the handle comes off with a
  screwdriver.
- **Bearing tower**: one printed piece under the case top holding both
  6001Z, bored for a light press fit to be tuned with a test print.
- **Centring**: V cam, 608ZZ roller on an arm pivoting on a pin, spring
  between arm and case. The cam profile sets the feel: steeper at centre
  for a clear neutral, flatter towards ±75°.
- **End stops**: a lug on the shaft against two fixed stops at ±75°, so the
  cam, the gears and the potentiometer never reach their own limits.
- **Potentiometer drive**: gears 36 : 24, module 1, centre distance 30,
  so ±75° turns the pot ±112.5° (225°) of its ~270° (the pot in hand):
  about 22° to spare at each end, with the pot set centred. (First drawn 36 : 20,
  270°: too close to the useful track of a 16 mm pot; changed 2026-11-01.)
  The deck slot sets the mesh with no backlash.
- **Controller**: an RP2040 board (Pico form factor) in a printed cradle
  on the case bottom, its USB-C through the back wall (decided 2026-11-02).

## Fixed points

- FreeCAD 1.1, Part workbench and macros, same as the Glareshield.
- Sensor: a **linear (B taper) rotary potentiometer**, not logarithmic. A
  Hall sensor was considered and set aside for cost (2026-10-31).
- Controller: **RP2040**, Pico form factor (native USB HID). Firmware in
  `firmware/` (arduino-pico core).

## Coordinates

Handle frame (`cad/Handle.FCStd`):
- origin on the hub axis, on the mounting face (the shaft flange side);
- +Z along the hub axis, towards the grip (up, in the cockpit);
- the index tab at −45° in XY.

**Assembly frame** (all v2 parts, `cad/Tiller.FCStd`): Z up along the
steering axis, the axis at X = Y = 0, **Z = 0 on the top face of the case**.
The roller sits on +X, the potentiometer on −X. The handle frame is linked
at Z = +4: handle Z = assembly Z − 4.

## Design status

### Handle

`cad/Handle.FCStd` is the master and is edited only in FreeCAD; no script
rebuilds it (2026-11-09). The grip body is the stored shape `HandleBase`,
the base feature of the `Handle` body; everything cut into it (shaft flange
pocket, insert holes, wire bore, the PEDALS DISC recess, peg holes, wire
groove, switch well) is a sketch on the Params sheet.

### Mechanism v2: first full draft (2026-11-01)

Generated by `tools/freecad/build_mechanism.py` (run it with freecadcmd); the
values at its top seed the **Params** spreadsheet in every part file. Each
part is a **PartDesign Body** named like its file: XY sketches at a Z offset
(pads up, pockets down unless reversed), YZ sketches for the features along
X. Every sketch is fully constrained and its dimensions are named
constraints bound to Params, so a part is changed from the sheet or by
opening a sketch. Helpers: `tools/freecad/fcb.py` (`PDoc`, `Sk`).
Saving keeps the colours, materials and visibility set in the GUI
(`tools/freecad/keep_gui.py`). To rebuild only some parts, set
`TILLER_ONLY=build_button_cap` (function names, comma separated): those part
files are rewritten, their bodies exported to `stl/Tiller-<body>.stl`, and
the Tiller links into them repointed if `LINK_TARGET` says so; nothing else
is touched.

Fixed shapes: the cam profile (a blocked B-spline in `CamSketch`, from
`cam.py`) and the handle grip (`HandleBase`, stored in `Handle.FCStd`; the
handle is not built by the script).

**From now on the FCStd files are the master.** Running the script again
overwrites them, and with them any change made in the GUI: run it only for a
new cam, or before anything is edited by hand.

`tools/freecad/check_assembly.py` checks the assembly over the travel. Picture:
`docs/img/mechanism_v2.png`. `tools/freecad/animate_tiller.py` (run with
`freecad.exe`, it needs the GUI) renders the mechanism over ±75° with the same
kinematics, the case and deck hidden, into `media/tiller.gif` (not in git);
Tiller.FCStd is not saved.

| File (`cad/`) | Part | Material |
|---|---|---|
| `Tiller.FCStd` | Assembly: App::Link to every part below | |
| `Handle.FCStd` | Handle, grip body `HandleBase` stored in the file; Ø30.4 × 4.2 pocket for the shaft flange, 3 × M3 insert holes Ø4 × 6 on r 11, wire bore Ø7.5 up to the recess. Button seat: recess Ø30.5 down to Z 12.8 (was 20; 2.6 above the flange inserts), 2 peg holes, a groove 3.6 × 1.8 in the floor from the switch well to the wire bore (two 24 AWG silicone wires, 1.5 outside), and the well going on 1.8 into the floor (8.0 under the switch body; 0.8 above the flange insert) | PETG |
| `ButtonBase.FCStd` | App::Part `ButtonBaseAssembly`: body `ButtonBase`, disc Ø30.2 × 1.5 on the recess floor with 2 pegs, the collar round the cap skirt, a solid pedestal 10.9 square with the cup for the switch body (7.3 square, 4 deep, the body bottom at Z 19.0 on two ledges where there are no pins) and the well under it, 5.2 × 7.3, open down to the floor, for the potted pins and joints; body `Switch`, the G-Switch as bought (no STL). Section: `docs/img/button_switch.png` | PLA, upright |
| `ButtonCap.FCStd` | App::Part `ButtonCapAssembly`: body `ButtonCap`, Ø29.5 top with the legend pockets, the Ø29.5 ring under it 5.5 high so the recess shows no gap with the cap up (was 2.5, 2026-11-05; 0.78 above the collar pushed home), skirt Ø26.4 in the collar (0.7 of play a side), a square sleeve 14.5 outside, 11.3 inside, down to Z 15.5 round the base pedestal (10.9): the up-down guide, 0.2 of play a side, 7.5 on the pedestal when latched (added 2026-11-05: the cap wobbled), boss Ø6 in the middle with the socket 3.2 × 2.2 × 2.5 the switch head is glued in, its long side along X, parallel to the pin rows (turned 90° on 2026-11-04 so the legend reads right; the base and the switch are unchanged) (rectangular: the cap cannot turn; 0.6 of plate left under the letters); letters 5.0 high on arcs of radius 10.5; body `ButtonCapLegend`, the white letters | PLA, top on the bed |
| `Shaft.FCStd` | Hollow shaft, Ø12.00 / Ø7, flange Ø30 × 4 (Z +4 … +8, in the handle pocket) with 3 × Ø3.4 on r 11 countersunk from below Ø6.9 × 90° (PartDesign Hole) for M3 ISO 10642, shoulder Ø15.5 (Z −1.5 … −3.5) on the upper inner race, 0.5 straight then a 45° cone to Ø12.5 so it prints flange down without supports, D flat at 5.0 from Z −44 to the end at −67 | PETG |
| `Chassis.FCStd` | Plate 134 × 88 × 7 (Z −3 … −10) under the case top, trimmed to the case square (1 mm in), 4 × M3 inserts on (±25, ±25) for the case screws; bearing tower Ø36 to Z −43.5 (seats Ø28.15, shoulder bore Ø22); posts down to the deck at Z −70: pivot (31, −35) Ø14 then pin Ø10 below Z −41.5, stops at (1.76, ±35.96) Ø10, spring post (80, 18) Ø16 with a Ø3.4 hole along X at Z −47 and an M3 nut trap in its front face, corner up (5.8 across flats, 2.8 deep; the spring pushes the nut into it; 3.2 of wall either side), since 2026-11-06; M3 inserts in every post foot | PETG |
| `Rotor.FCStd` | One piece on the shaft flat: boss Ø15.5 on the lower inner race (Z −43.5), cam Z −45 … −54 with the stop lug at 180° (r 10 … 40, 8 wide; it starts inside the cam's back arc, at r 14 it was a loose second solid), gear 36 teeth module 1 (Z −55 … −61), hub Ø24 to −67 with the grub screw (M3 × 5 on the flat) through an M3 nut trapped in the hub: the slot opens on the hub bottom, 2.7 wide, at r 7.15 … 9.85 (2.0 of wall to the flat, 2.1 to the hub side), up to Z −61.1; the grub ends 1.9 under the hub side (since 2026-11-06, was an insert). The D bore and the grub hole are turned by −34° (`mech_rot`), see *Decisions* | PETG |
| `RollerArm.FCStd` | Pivot hub Ø18 / Ø10.3 (Z −41.5 … −52.5), beam over the cam, roller pin Ø7.95 at (31, 0) for the 608ZZ (Z −45.3 … −52.3) with a Ø2.6 hole 8.5 deep at its end for the M3 × 8 (since 2026-11-06, was an insert), spring spigot Ø7.3 × 4 at (36, 18, −47) | PETG |
| `Deck.FCStd` | Lower plate 134 × 88 × 5 (Z −70 … −75), flat bottom on the bed, trimmed to the case and cut clear of the RP2040 corner, screwed to the post feet (counterbores 4.2 deep, 0.8 of deck under the head); boss under the arm hub; Ø30 wire hole. Pot at (−30, 0): slot for the bushing, ±1.5 mm along X to set the mesh; the pot frame on the deck bottom; a recess on the top, 12.5 wide, 1.5 deep, for washer and nut (3.5 of deck under the nut, 0.65 of thread to spare over it); a slot 3 deep from below for the anti-rotation tab, at +Y | PETG |
| `PotGear.FCStd` | 24 teeth module 1 (Z −55 … −61), hub Ø12 down to −67 (2.1 over the pot nut), round bore Ø6.03 through (prints about 5.83): pushed onto the knurled split shaft, 11.8 of it in the bore | PETG |
| `SpringCup.FCStd` | Disc Ø14 × 5 at X 66 … 71 between the spring and the M3 preload screw, spigot Ø7.3 × 4 into the spring, blind centring hole Ø3.4 × 2 in its back for the screw tip (3 solid under it); back face 1 mm short of the spring post. For the spring in hand preloaded to 30.0 (2026-11-09) | PETG, 100 % infill, back face on the bed |
| `Bumper.FCStd` | End-stop sleeve Ø14 / Ø10.3 × 9, on the stop posts at cam height (Z −54 … −45), standing on the StopSpacer | TPU |
| `StopSpacer.FCStd` | Tube Ø13 / Ø10.4 × 16 (Z −70 … −54), 2 of them: on each stop post, from the deck up to the bumper, which nothing else holds at cam height (added 2026-11-07; a TPU bumper that tall prints badly). 1 mm under the bumper, so the lug never meets it | PETG |
| `Hardware.FCStd` | 6001Z, 608ZZ, spring (drawn preloaded), the B10K pot in hand (Z 0 = frame top; board edge 13.5 from the axis estimated from the photo) | not printed |
| `FitTest.FCStd` | Test print on one plate 140 × 64 × 4: seats Ø27.95 / 28.05 / 28.15 / 28.25, shafts Ø11.85 / 11.95 / 12.05, insert holes Ø3.9 / 4.0 / 4.1, left to right | PETG |
| `CaseShell.FCStd` | Top and walls in one piece, 163 × 163 outside (157 inside, walls 3, corners r 6), Z 0 … −93, top 3 thick. Ø18 hole for the shaft, 4 × Ø3.4 for the chassis screws; corner columns Ø8 at (±74.5, ±74.5) with M3 inserts Ø4.0 × 6 at their ends for the bottom; USB-C notch 15 wide up from the bottom edge of the back wall at X −55 | PLA, upside down (top on the bed) |
| `CaseBottom.FCStd` | Bottom plate 163 × 163 × 3 (Z −93 … −96), 4 × M3 countersunk from below, 4 recesses Ø16.4 × 1 for the feet. Rim 2 high, 1.6 thick, 0.2 inside the shell walls (lines the bottom up, keeps the walls from bending in; it stops 0.5 short of the columns and leaves the cradle end of the back wall to the USB tongue, 2026-11-03). RP2040 cradle at X −55, board along Y with the USB edge at Y 77.6: side rails 2.4 thick 23.0 apart (they only guide), central rib 6 wide 8 high under the board, groove blocks beside the connector at the USB end (the board slides 1.5 mm under them, clear of the two LEDs), solid stops and a snap latch at the far end; tongue filling the lower part of the wall notch so the window is 15 × 8; 2 zip-tie bridges in front | PLA, flat |
| `ScaleDisc.FCStd` | App::Part `ScaleDiscAssembly`: body `ScaleDisc`, Ø110 × 3 on the case top (Z 0 … +3; was Ø92, the numbers go outside the screw heads), Ø18 hole, held by the 4 chassis screws (countersunk); body `ScaleDiscLegend`, the white inlay 0.4 deep: ticks at 0, ±10, ±30, ±50, ±75° round the handle index tab at −45° (the centre one longer), the numbers 10 30 50 75 each side and LH / RH beyond the ends (LH counter-clockwise from above, `SCALE['lh_sign']`), every one read from outside the disc, its top towards the centre (user 2026-11-05). Picture: `docs/img/scale_disc.png` | PLA, face on the bed, the legend as the second part |
| `Foot.FCStd` | Ø16 × 4, 1 mm in the bottom recess, glued, 4 at (±62, ±62) | TPU |
| `FitTestPLA.FCStd` | Test print for the case parts, plate 110 × 50 × 3: insert holes Ø3.9 / 4.0 / 4.1 (back row), RP2040 board gauges, rails 3 × 4 × 20 with gaps 23.0 / 23.1 / 23.2 for the 22.85 board (front row), left to right | PLA |

Mechanism parts are drawn in the mechanism frame (as before) and turned by
`mech_rot` = 34° about Z in `Tiller.FCStd`; handle, shaft, bearings and the
case parts are in the case frame. Plan views and the cradle section:
`docs/img/case_sections.png` (first layout study: `docs/img/case_layout_top.png`).

Stack-up along the axis:

| Z | What |
|---|---|
| +8 … +4 | shaft flange, inside the handle hub |
| +3 … 0 | scale disc on the case top |
| 0 … −3 | case top (Ø18 hole, the Ø15.5 shoulder passes) |
| −3 … −10 | chassis plate |
| −3.5 … −11.5 | upper 6001Z |
| −35.5 … −43.5 | lower 6001Z (32 mm between the two) |
| −41.5 … −52.5 | roller arm |
| −45 … −54 | cam and stop lug; roller −45.3 … −52.3 |
| −55 … −61 | gears 36 : 24 |
| −61 … −67 | rotor hub, grub screw; shaft end and wire exit at −67 |
| −70 … −75 | deck |
| −75 … −84 | potentiometer, under the deck (bushing through it), pins to −X at about −79.8 |
| −85 … −81.4 | RP2040 on its cradle (board −85 … −83.4), USB-C centre at about −81.8 |
| −93 … −96 | case bottom; feet to −99 |

How it holds together:
- **Down** (pressing the handle or the button): handle → flange → shaft
  shoulder → upper inner race → outer race → tower shoulder.
- **Up** (pulling the handle): rotor boss → lower inner race → tower shoulder.
  The rotor is pushed up against the bearing and locked by the grub screw on
  the flat, which also carries the torque.

**Cam and spring** (`tools/freecad/cam.py`, run it for the table): the cam
is synthesised from the wanted torque, with the 608ZZ roller on a 35 mm arm
and the spring line 53 mm from the pivot. Cam radius 20.0 at centre, 25.9 at
75° (26.0 since 2026-11-09).

| Angle | Torque | At the grip (r ≈ 60) | Spring compression beyond preload | Spring force |
|---|---|---|---|---|
| 0° | 0 | 0 | 0 | 16.5 N |
| 3° | 52 Nmm | 0.9 N | 0.1 mm | 16.6 N |
| 10° | 80 Nmm | 1.3 N | 0.6 mm | 17.4 N |
| 30° | 120 Nmm | 2.0 N | 2.4 mm | 20.4 N |
| 60° | 181 Nmm | 3.0 N | 5.9 mm | 25.8 N |
| 75° (stop) | 428 Nmm | 7.1 N | 8.4 mm | 29.8 N |

The torque jumps in the first 3° (the felt centre), grows slowly, and doubles
over the last 15° (the warning). Since 2026-11-09 it is drawn for the
**spring in hand: k 1.6 N/mm, 16.5 N preload** (`spring_k`, `spring_preload`
in `build_mechanism.py`, which set `cam.P`): free length 40.3, 30.0 long
preloaded, 21.6 at the stops. The preload screw changes the preload; a
different spring changes everything, so recompute with its rate.

**Checks on the model** (`tools/freecad/check_assembly.py`, every 15° from
−75° to +75°, arm turned by the cam): no part overlaps another; the roller
touches the cam at every angle; the lug meets the bumpers exactly at ±75°
and clears them by 2.5 mm or more elsewhere; the gears stay in mesh.

### Case, electronics (first draft, 2026-11-02)

- **Shell**: top and walls in one PLA piece, printed upside down so the top
  face comes off the bed smooth. The chassis plate is screwed under the top;
  the 4 screws go through the scale disc as well (M3 × 10 countersunk), so the
  disc, the top and the chassis are clamped together.
- **Bottom**: a plate with the RP2040 cradle, 4 × M3 × 8 countersunk from below
  into inserts in the corner columns. Taking it off opens the whole case from
  below (spring preload, wires, board).
- **RP2040 cradle** (rules in *Open points*): the board drops in between the
  rails, its USB end goes under the two groove blocks, then the far end is
  pressed down past the latch, which snaps over it. Plugging the cable pushes
  the board onto the solid stops at the far end; unplugging pulls it against
  the groove blocks. The connector sits about 0.1 mm inside the back wall, the
  plug enters the 15 × 8 window.
- **Height**: 96 mm from the top face to under the bottom, 99 on the feet,
  102 to the top of the scale disc (handle excluded).
- **Check** (`check_assembly.py`, now with the case): no overlaps over ±75°.

## Parts that are not printed

Planned. "In hand" means the user has it.

| Part | For | Notes |
|---|---|---|
| Self-locking switch 7 × 7 (G-Switch), in hand | PEDALS DISC | potted in the base well; wires soldered to the pins first |
| Hot glue or 2-part epoxy | potting the switch pins | |
| Two wires 24 AWG, silicone, 1.5 outside (in hand) | switch to the RP2040, down the shaft bore | inside the well the potting insulates the joints: no heat-shrink there; one sleeve over both wires outside the groove if wanted |
| 2 × ball bearing 6001Z, 12 × 28 × 8 | shaft | in hand |
| Ball bearing 608ZZ, 8 × 22 × 7 | cam roller | in hand |
| Compression spring 1 × 10 × 40, 9 coils (ordered 2026-11-04, in hand 2026-11-09). Measured: wire 1.05, OD 9.96, ID 7.8, free length 40.3, 7 active coils, closed ends not ground; 2.5 kg at 25 mm long, k ≈ 1.6 N/mm | centring | in hand |
| Linear rotary potentiometer B10K, M7 bushing, knurled split shaft Ø5.83 × 13.3, ~270° | steering angle | in hand, 1 piece; the shaft stays whole |
| 15 × M3 heat-set insert (the type of the fit tests, 4–6 long), plus spares | PETG: handle 3, chassis plate 4, post feet 4; PLA: case columns 4 | hole Ø3.9 × 6 in PETG, Ø4.0 × 6 in PLA (fit tests); each one reached straight by the iron's tip, its shoulder (~Ø5–6) on a free face |
| 3 × M3 nut | 1: rotor grub screw, in a nut trap in the hub (the iron cannot reach under the gear); 2: spring preload, one in a nut trap in the spring post, one as a lock nut | in hand |
| 3 × M3 × 8 countersunk (ISO 10642) | shaft flange into the handle | flange 4, so 4 into the inserts (holes 6 deep); an M3 × 10 would reach the bottom of the hole (2026-11-09) |
| 4 × M3 × 10 countersunk (ISO 10642) | scale disc and case top into the chassis plate | disc 3 + top 3, so 4 into the inserts (holes 6 deep); an M3 × 12 would reach the bottom of the hole (2026-11-09) |
| 4 × M3 × 8 countersunk (ISO 10642) | case bottom into the corner columns | |
| 4 × M3 × 6 socket head (ISO 4762) | deck to the post feet, from below | head in a Ø6 × 4.2 counterbore, 0.8 of deck under it, 5.2 into the inserts (holes 6 deep); was M3 × 10 button head before the 5 mm deck (2026-11-09) |
| 1 × M3 × 8 socket head (ISO 4762) + 1 × M3 washer DIN 9021 (OD 9) | keeps the 608 on its pin | cuts its own thread in a Ø2.6 hole (prints about 2.45): an insert would swell the 2 mm wall of the pin; the washer must cover the inner race. Sketch: `docs/img/roller_pin.png` |
| 1 × M3 × 5 grub screw, flat point | rotor on the shaft flat | |
| 1 × M3 × 25 socket head | spring preload, from the back of the spring post into its nut trap, lock nut on the back face (was an M4 insert and M4 × 20, user 2026-11-04). With the lock nut, the head stays clear of the corner column for a cup back face at X 66 … 71, a spring 26 … 31 long preloaded: the spring post stays at X 80 for a free length of 35 or 40 | |
| Controller: RP2040 board, Pico form factor (clone, in hand, no mounting holes) | joystick HID | chosen 2026-11-02, in the printed cradle |
| USB cable | PC | |
| TPU filament | bumpers, 4 feet | |
| Glue for the feet (CA or contact) | | |

## 1. Printing

- [x] **FitTest first**, in PETG (printed 2026-11-01, 0.4 nozzle): seat
  Ø28.15, shaft Ø11.85 (later 12.00, see below), insert hole Ø3.9. Set on the Params sheets
  (`seat_d` Chassis, `shaft_d` Shaft, `ins_d` Chassis, Handle, PotGear,
  RollerArm, Rotor) and in `L`; check_assembly unchanged.
- [x] **Shaft re-sized** (2026-11-01): the 6001 bore measures 11.94 and the
  PETG pins print about 0.2 small (11.85 → 11.65, 11.95 → 11.72,
  12.05 → 11.82 by calliper). The shaft at 11.85 printed 11.70 and played
  in the bearing, 11.95 still had play, 12.05 does not go in (seam and
  ovality). `shaft_d` is now 12.00; print it with the seam aligned at the
  back and file that ridge if it binds.
- [x] **FitTestPLA** before the case (printed 2026-11-01): insert hole
  Ø4.0 in PLA (`ins_d_pla`, PETG takes 3.9), RP2040 rails gap 23.0 for the
  22.85 board (`board_gap`). Both in `L`, for the case parts.
- [ ] Shaft: standing, flange down, so the bearing surfaces are round.
- [ ] Chassis: plate on the bed, tower and posts up, no supports.
- [ ] Rotor: gear side down (hub on the bed).
- [ ] Handle: orientation and supports to be decided (the button seat is
  drawn; the grip needs supports).
- [x] Button, pen-rotor version (printed 2026-11-03): the spring worked, the
  latch never held. Replaced by the heart cam (Decisions, 2026-11-03).
- [x] Button, heart-cam version (printed 2026-11-03): the tab guides broke at
  the first fitting, the wire could not be threaded. Replaced by the pen
  mechanism (Decisions, 2026-11-04).
- [x] Button, click-pen version: not printed; the pen is too long for the hub.
- [x] **Button, G-Switch version**, in PLA: ButtonBase (upright), ButtonCap (top
  on the bed, legend as the second part of the same object). Printed and
  tried 2026-11-04: it latches and releases; the fits are tight, the switch
  stays in its cup and the cap holds on the head even without glue. Travel
  1.1, much less than first planned: accepted by the user.
- [ ] CaseShell (PLA): upside down, top face on the bed, no supports (the
  USB notch is open at the top of the print).
- [ ] CaseBottom (PLA): flat, cradle up. The latch arm is 1.2 thick: it
  prints as solid walls.
- [ ] ScaleDisc (PLA): flat, ticks up. Foot × 4 (TPU).

## 2. Handle

- [ ] Three M3 inserts in the hub.
- [ ] G-Switch: solder the two wires to the pins (latching contact), pass
  them down through the base well, along the floor groove and down the wire
  bore.
- [ ] Base into the recess (pegs). Fill the well with hot glue or epoxy round
  the pins and joints, press the switch into its cup; let it set.
- [ ] Cap on the switch head: glue in the socket.
- [ ] Check: push, it stays flush; push again, it comes up 1.1 mm; the tester
  on the wires closes and opens with it.

## 3. Mechanism

Plan, not yet built:

- [ ] Inserts: chassis plate (4), post feet (4). Nuts: one in the spring
  post trap (front face), one in the rotor hub slot (from the hub bottom).
- [ ] Press the two 6001Z into the tower: the upper one from above, the
  lower one from below, each against its shoulder.
- [ ] Roller arm on the pivot pin, 608ZZ on its pin, washer and screw.
- [ ] Bumpers on the stop posts, then a StopSpacer behind each (chassis upside
  down); the deck closes them in.
- [ ] Inserts in the 4 shell columns.
- [ ] Chassis under the case top, scale disc on top, 4 × M3 × 10 countersunk
  through the disc and the top into the chassis plate.
- [ ] Shaft to handle: 3 × M3 × 8 countersunk through the flange into the inserts. Pass
  the button wires through the shaft first.
- [ ] Handle and shaft down through the case top and both bearings.
- [ ] Rotor from below onto the flat (the D fits one way only). Push it up
  against the lower bearing and tighten the grub.
- [ ] Spring between the arm spigot and the cup; M3 × 25 from the back of the
  spring post with the lock nut on it, through the trapped nut, its tip in
  the cup's centring hole. Start with the tip **3.0 mm** out of the post's
  front face (16.5 N); set the feel with the Chassis out of the case (see
  *Preload screw access*), then the lock nut.
- [ ] Pot from below: frame on the boss, the tab in its slot, pins to −X
  (away from the shaft); washer and nut in the recess on top. Turn the
  shaft to the middle of its travel with the handle centred, then push the
  pot gear onto the knurls (no glue unless it slips). Slide the pot along
  the slot until the gears mesh without play, then tighten.
- [ ] Deck onto the post feet (4 × M3 × 6 socket head from below).
- [ ] Check: handle returns to centre from both sides, centre felt with the
  eyes closed, soft stop at ±75°, no binding anywhere.

## 4. Case and electronics

- [ ] RP2040: headers soldered, wires on. Into the cradle: USB end under the
  groove blocks first, then press the far end down past the latch.
- [ ] Wires to the pot and the button loop, tied at the bridges (pins in
  `firmware/README.md`: pot on 3V3 / AGND / GP26, button on GP2 / GND).
- [ ] Bottom on (4 × M3 × 8), feet glued in the recesses.
- [ ] Firmware on the board (`firmware/bin/Airbus_Tiller_RP2040.uf2` onto the
  BOOTSEL drive). Plug in: the board must not move; Windows shows the game
  controller "Airbus Tiller".

## 5. Calibration

- [ ] Over the serial port: `c` at the centre, `l` and `r` at the stops,
  `w` (`firmware/README.md`).
- [ ] MSFS: axis X → Nose Wheel Steering Axis. MobiFlight: button 1 →
  `L:S_FC_CAPT_TILLER_PEDAL_DISCONNECT`, 1 on press, 0 on release
  (`firmware/README.md`).

## Open points

- **Assembly by hand (problem, user 2026-11-09)**: the first full fit worked
  but was much harder than it should be. The Rotor goes onto the shaft from
  below, and the shaft goes in from above through the bearings in the
  Chassis tower, so the inner mechanism cannot be put together on its own:
  everything is built inside the Chassis, and once the Deck closes it, no
  adjustment is possible. The PotGear is hard to fit, and its hub stands
  over the pot nut, so the mesh slot cannot be used without taking the gear
  off. The design was checked for fit and clashes only, never for hands and
  tools. No change wanted (user, 2026-11-09): it is assembled and works.
  For any new part, check the assembly steps by hand and tool first.
- **Rule for threads** (user, 2026-11-04): a heat-set insert only where the iron's tip
  goes in straight with its shoulder on a free face; anywhere else an M3 nut in a
  nut trap. Done 2026-11-06: the Rotor grub and the spring preload screw in nut
  traps, the RollerArm pin a Ø2.6 hole an ordinary M3 cuts its own thread in.

- **ScaleDisc** (redrawn 2026-11-04 with numbers and LH / RH): the handle's index
  tab ends at about r 31 and the ticks start at r 41 (the 4 screw heads sit at
  r 32 … 39), so the tab points at the scale from about 10 mm inside it.
- **PEDALS DISC button** (G-Switch, drawn 2026-11-04; `check_button.py`: no
  overlaps off, latched and pushed home, handle included; the switch touches
  the cup, ledges and socket without overlapping). Pin length 3.7 and their
  insets are read from the photos: check them against the well (5.2 × 7.3)
  before potting.
- **Spring** (2026-11-09, the spring in hand, see the shopping list):
  k 1.6 N/mm measured, so 30.0 long preloaded (16.5 N, the most the cup
  leaves: its back face 1 mm short of the post), 21.6 at the stops (29.8 N),
  63 % of its travel to solid (about 10.5), about 690 MPa at the stops. The
  cam came out within 0.1 mm of the one for 2 N/mm. Rotor, RollerArm (spigot
  on ID 7.8) and SpringCup rebuilt; the Chassis and the Deck unchanged.
- **Preload screw access**: the screw points at the back-right corner, about
  11 mm from the post to the column, and in the case the deck covers it. So
  the preload is set once, on the bench (user, 2026-11-07): the Chassis out
  of the case, the deck on, the Rotor, arm and spring fitted, the handle and
  shaft in the bearings. The case is not in the load path (the shaft hangs
  on the upper bearing in the Chassis tower). Turn the screw for the feel at
  the handle, note the tip's protrusion, tighten the lock nut, then take the
  handle and shaft out and fit the Chassis into the case.
- **RP2040 groove blocks** (checked 2026-11-02): the clone has two LEDs about
  2 mm from the USB edge, so the blocks reach only **1.5 mm** over the board
  top with the board pushed home (`lip`, 1.4 at the nominal position),
  5.3 … 8.3 mm either side of the board centre line. The latch reaches 0.8 mm
  over the far edge, 8 mm wide at the centre.
- **SpringCup** (decided 2026-11-08, drawn 2026-11-09): disc 5 thick (was
  4), with a blind centring hole Ø3.4 × 2 in its back for the preload screw
  tip, so the cup cannot walk off the tip as the spring tilts or the screw
  turns; 3 mm of solid plastic stay under the tip. PETG at 100 % infill.
- **Handle on the shaft before the shaft goes in**: the M3 heads are under
  the flange, 1 mm above the scale disc, so they are reached only with the
  shaft out of the case. Countersunk (done 2026-11-01), they stay inside
  the flange.
- **RP2040 board** (cradle drawn 2026-11-02 to these rules): no mounting holes, so a printed cradle
  (slide-in rails plus a latch). Measured 2026-11-01: **22.85 × 53.30**,
  USB-C on a short side, sticking out less than 1 mm. The user wants that
  USB-C as the case connector, no extension: the board sits with its USB
  edge at the inside of a case wall, the wall has an opening for the plug
  overmold (about 15 × 8, cables vary), and the cradle has a solid stop
  behind the board, so plugging in pushes on the case and not on the
  solder joints. PCB 1.6, nothing on the underside, USB-C centred on the
  short side. **Pin headers will be soldered** on top. Seen from above the
  pins stay inside the board outline (nothing sticks out sideways), but
  underneath the solder joints stand at least about 2 mm, along both long
  edges. So the cradle:
  - **side walls** along the long edges, touching the board edges (they
    only guide it sideways), **no lip over the top face**;
  - **no ledge under the long edges** (the solder joints are there): the
    board rests on a **central rib** between the two pin rows and on the
    short ends, at least 3 mm above the floor;
  - held down only at the short edges: a groove at the USB end (with the
    solid stop behind it) and a snap latch at the far end;
  - strain relief for the wires next to it.
- **Gear backlash**: the gears are drawn at exactly 30 mm, with no
  backlash; the deck slot sets the real mesh. If printed teeth bind, open
  the centre distance a little.
- **PotGear bore**: drawn Ø6.03 (`pot_shaft_d` 5.83 + `bore_clear` 0.2)
  for a press fit on the knurls; if it prints too tight or too loose,
  change `bore_clear` in PotGear only.
- **Button wires**: they turn with the handle (decided above). Down the
  hollow shaft, out at Z −67 through the Ø30 deck hole, then a loose loop
  that takes ±75°, with strain relief at both ends.
- Not yet opened in the FreeCAD GUI: the files are built and checked
  headless only.
- **Firmware**: still to check with the pot mounted: the axis noise at rest,
  the calibration.
