# mpxg2cli

CLI to control the [Lexicon MPX-G2](https://stecrecords.com/gear/mpxg2/doc/MPXG2_MIDI_Impl.htm) via MIDI.

## Requirements

- [uv](https://astral.sh/uv)
- A MIDI interface connected to the MPX-G2 (default: `UM-ONE`)

## Usage

```
mpxg2.py [-d DEVICE] <subcommand> ...
```

### Select program

```
mpxg2.py pc <1-300>
```

### Set panning

```
mpxg2.py pan [l | lm | m | mr | r | p]
```

Default: `m`. Run `pan p` once per session before using pan - it selects program 262, which enables CC110 panning control.

### Toggle effect button

```
mpxg2.py fx <effect> <on|off>
```

Effects: `delay`, `reverb`, `eff1`, `eff2`, `gain`, `bypass`

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-d`, `--device` | `UM-ONE` | MIDI output device name (case-insensitive substring match) |

## Examples

```sh
mpxg2.py pc 262
mpxg2.py pan l
mpxg2.py fx reverb off
mpxg2.py -d iac pan r
```
