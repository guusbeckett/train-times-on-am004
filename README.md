# LED Train Departure Display

This project controls an LED display to show the next departing train from a specified station in the Netherlands. It fetches real-time departure information from the Dutch Railways (NS) API.

## Features

- Fetches upcoming train departures from a configured station.
- Displays the departure time, track, and destination on an LED display.
- Includes a separate script for sending raw text to the display for testing or other purposes.

## Hardware

This project is designed for an LED display that accepts serial communication, such as the Velleman MMLXXX series.

## Requirements

- Python 3
- `pyserial` library

Install the required library using pip:

```bash
pip install pyserial
```

## Configuration

Configuration for the scripts is hardcoded within the files themselves.

### `set-next-departing-train.py`

- **Serial Port**: Modify the `DEVICE` variable to match your serial port.
- **Departure Station**: Modify the `station` parameter in the API URL to your desired departure station code (e.g., `amsterdam` -> `asd`, `breda` -> `bd`, `utrecht` -> `ut`).

### `send_raw.py`

- **Serial Port**: Modify the `DEVICE` variable to match your serial port.

### Platform Notes

The hardcoded path to the serial device (`/dev/cu.usbserial-0001`) is specific to macOS. You will need to change this path to match your device's path on other operating systems, such as Linux (e.g., `/dev/ttyUSB0`).

## Usage

### Displaying Next Departing Train

To run this script, simply execute it with Python after configuring the serial port and station in the file.

```bash
python3 set-next-departing-train.py
```

### Sending Raw Text

The `send_raw.py` script sends a raw command string to the display. The string must be provided as a command-line argument.

**Synopsis:**
```bash
./send_raw.py "<COMMAND_STRING>"
```

**Example:**
```bash
./send_raw.py "<L1><PC><FE><MQ><WJ><FE>Hello world"
```

## Licence

This project is licensed under the terms of the EUPL Licence. See the `LICENCE.md` file for details.
