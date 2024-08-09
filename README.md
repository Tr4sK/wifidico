# WiFi Connection Script

## Description

This Python script scans available WiFi networks, attempts to connect using generated or provided passwords, and logs the results into CSV files. The script can also ignore specific SSIDs based on regular expressions defined in an `ignore.txt` file.

## Features

- **WiFi Scanning**: Scans available WiFi networks and sorts them by signal strength.
- **Automatic Connection**: Attempts to connect to networks using generated passwords (based on the SSID) or those provided in a file.
- **Success and Failure Logging**: Logs successful connections in `success.csv` and failed attempts in `failed.csv`.
- **SSID Ignoring**: Ignores specific SSIDs or those matching regex patterns defined in `ignore.txt`.
- **Cleanup of Failed Connections**: Removes failed connections from NetworkManager.

## Prerequisites

- Python 3.x
- NetworkManager (`nmcli`)

## Files

- **`wifi_script.py`**: Main script for managing WiFi connections.
- **`passwords.txt`**: File containing passwords to try for each SSID.
- **`failed.csv`**: Logs failed connection attempts.
- **`success.csv`**: Logs successful connections.
- **`ignore.txt`**: Lists SSIDs to ignore (can include regular expressions).

## Usage

1. **Clone the Repository**:
   ```bash
   git clone <REPOSITORY_URL>
   cd <REPOSITORY_NAME>
