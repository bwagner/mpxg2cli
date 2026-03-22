#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["mido", "python-rtmidi"]
# ///

"""
Control the Lexicon MPX-G2 via MIDI.

Reference: https://stecrecords.com/gear/mpxg2/doc/MPXG2_MIDI_Impl.htm

Subcommands:
  pc   <program_number>       Select program (1-300)
  pan  [position]             Set panning (l, lm, m, mr, r, p); default: m
                              Note: run 'pan p' once per session before using pan.
  fx   <effect> <on|off>      Toggle effect button
"""

import mido

MIDI_DEV = "UM-ONE"
MIDI_CH = 2          # 1-based; converted to 0-based for mido
BANK_SIZE = 100      # programs per bank; ref: "each bank consists of 100 programs"
PROG_MIN = 1         # ref: "Program bank 0 (1-100 Internal Presets)"
PROG_MAX = 300       # ref: "Program bank 2 (... 250-300 User definable registers)"
CC_BANK_SELECT = 32  # ref: "Controller #32 will be used to select the banks"
CC_PAN = 110

PAN_POSITIONS = {
    "l": 0,
    "lm": 32,
    "ml": 32,
    "mid": 64,
    "m": 64,
    "mr": 96,
    "rm": 96,
    "r": 127,
}
PAN_PROG = 262  # program enabling CC110 panning; select once per session via 'pan p' before using pan

# Sysex messages sampled from MPX-G2 via: receivemidi dev UM syx
# Each entry: [on_bytes, off_bytes]
_syx = lambda s: [int(x, 16) for x in s.split()]  # noqa: E731
FX_SYSEX = {
    "delay": [
        _syx("06 0F 00 01 01 00 00 00 00 00 03 00 00 00 00 00 00 00 08 01 00 00 03 00 00 00 31"),
        _syx("06 0F 00 01 01 00 00 00 01 00 03 00 00 00 00 00 00 00 08 01 00 00 03 00 00 00 32"),
    ],
    "reverb": [
        _syx("06 0F 00 01 01 00 00 00 00 00 03 00 00 00 00 00 00 00 08 01 00 00 04 00 00 00 32"),
        _syx("06 0F 00 01 01 00 00 00 01 00 03 00 00 00 00 00 00 00 08 01 00 00 04 00 00 00 33"),
    ],
    "eff1": [
        _syx("06 0F 00 01 01 00 00 00 00 00 03 00 00 00 00 00 00 00 08 01 00 00 00 00 00 00 2E"),
        _syx("06 0F 00 01 01 00 00 00 01 00 03 00 00 00 00 00 00 00 08 01 00 00 00 00 00 00 2F"),
    ],
    "eff2": [
        _syx("06 0F 00 01 01 00 00 00 00 00 03 00 00 00 00 00 00 00 08 01 00 00 01 00 00 00 2F"),
        _syx("06 0F 00 01 01 00 00 00 01 00 03 00 00 00 00 00 00 00 08 01 00 00 01 00 00 00 30"),
    ],
    "gain": [
        _syx("06 0F 00 01 01 00 00 00 00 00 03 00 00 00 00 00 00 00 08 01 00 00 06 00 00 00 34"),
        _syx("06 0F 00 01 01 00 00 00 01 00 03 00 00 00 00 00 00 00 08 01 00 00 06 00 00 00 35"),
    ],
    "bypass": [
        _syx("06 0F 00 01 01 00 00 00 01 00 03 00 00 00 01 00 00 00 08 00 00 00 08 00 00 00 37"),
        _syx("06 0F 00 01 01 00 00 00 00 00 03 00 00 00 01 00 00 00 08 00 00 00 08 00 00 00 36"),
    ],
}
FX_NAMES = list(FX_SYSEX)
FX_POSITIONS = ["on", "off"]


def _open_port(midi_dev: str):
    available = mido.get_output_names()
    try:
        port_name = next(n for n in available if midi_dev.lower() in n.lower())
    except StopIteration:
        raise RuntimeError(f"MIDI device {midi_dev!r} not found. Available: {available}") from None
    return mido.open_output(port_name)


def program_change(program_number: int, midi_dev: str = MIDI_DEV):
    if not PROG_MIN <= program_number <= PROG_MAX:
        raise ValueError(f"Program number must be {PROG_MIN}-{PROG_MAX}, got {program_number}")
    bank, pc = divmod(program_number - 1, BANK_SIZE)
    ch = MIDI_CH - 1
    with _open_port(midi_dev) as port:
        port.send(mido.Message("control_change", channel=ch, control=CC_BANK_SELECT, value=bank))
        port.send(mido.Message("program_change", channel=ch, program=pc))


def pan(position: str = "m", midi_dev: str = MIDI_DEV):
    ch = MIDI_CH - 1
    if position == "p":
        program_change(PAN_PROG, midi_dev)
    else:
        ccval = PAN_POSITIONS[position]
        with _open_port(midi_dev) as port:
            port.send(mido.Message("control_change", channel=ch, control=CC_PAN, value=ccval))


def fx(effect: str, position: str, midi_dev: str = MIDI_DEV):
    data = FX_SYSEX[effect][position == "off"]
    with _open_port(midi_dev) as port:
        port.send(mido.Message("sysex", data=data))


if __name__ == "__main__":
    import argparse
    import sys

    available = mido.get_output_names()
    if sys.stdout.isatty():
        _h, _a, _r = "\x1b[1;34m", "\x1b[1;32m", "\x1b[0m"
        epilog = f"{_h}Available MIDI output devices:{_r}\n" + "\n".join(f"  {_a}{n}{_r}" for n in available)
    else:
        epilog = "Available MIDI output devices:\n" + "\n".join(f"  {n}" for n in available)
    parser = argparse.ArgumentParser(
        description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--device", "-d", default=MIDI_DEV, help=f"MIDI output device name (default: {MIDI_DEV})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pc = sub.add_parser("pc", help=f"Select program ({PROG_MIN}-{PROG_MAX})")
    p_pc.add_argument("program_number", type=int, help=f"MPX-G2 program number ({PROG_MIN}-{PROG_MAX})")

    p_pan = sub.add_parser("pan", help="Set panning")
    p_pan.add_argument(
        "position",
        nargs="?",
        default="m",
        choices=sorted({*PAN_POSITIONS, "p"}),
        help=f"Pan position (default: m); run p once per session before panning (selects program {PAN_PROG})",
    )

    p_fx = sub.add_parser("fx", help="Toggle effect button")
    p_fx.add_argument("effect", choices=FX_NAMES, help="Effect to toggle")
    p_fx.add_argument("position", choices=FX_POSITIONS, help="on or off")

    args = parser.parse_args()
    try:
        if args.cmd == "pc":
            program_change(args.program_number, args.device)
        elif args.cmd == "pan":
            pan(args.position, args.device)
        elif args.cmd == "fx":
            fx(args.effect, args.position, args.device)
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        parser.print_usage(sys.stderr)
        sys.exit(1)
