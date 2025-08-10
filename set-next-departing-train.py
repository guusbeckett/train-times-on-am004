#!/usr/bin/env python3

# Copyright (c) 2025 Guus Beckett
# Licensed under the EUPL, Version 1.2 or later;
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# https://joinup.ec.europa.eu/software/page/eupl

import urllib.request, json
import sys
import serial
import time
import re


def calculate_xor_checksum(data_packet):
	"""
	Calculates the XOR checksum as required by the manual (Page 4).
	The checksum is the XOR sum of all bytes in the data packet,
	formatted as a two-character uppercase hex string.
	"""
	checksum_val = 0
	for byte in data_packet:
		checksum_val ^= byte
	
	# Format as a two-character, zero-padded, uppercase hex string
	checksum_hex = f'{checksum_val:02X}'
	checksum = str(checksum_hex.encode('ascii'))
	checksum = re.sub('\'', '', checksum)
	checksum = re.sub('b', '', checksum)
	return checksum

def shorten_destination(destination):
	# ICD Amersfoort Schothorst
	# ECC Brussel-Zuid
	destination = destination.replace("Centraal", "C").replace("'s-Hertogenbosch", "IC Den Bosch")
	destination = (destination[:12] + '') if len(destination) > 12 else destination
	return destination

def build_payload_station(page_letter):
	# Datasheet https://asset.conrad.com/media10/add/160267/c1/-/en/000590996DS01/datablad-590996-mc-crypt-am03127-h13.pdf
	payload = '<L1>'				# Always use Line 1 as my display has only 1 line
	payload += f"<P{page_letter}>"	# Include page letter so we can have multiple trains in the playlist
	payload += '<FI>'				# Move in animation, slide in from the bottom to the top
	payload += f"<MA>"				# Set fast animation speed
	payload += '<WJ>'				# Keep the text on screen for 9 seconds
	payload += '<FI>'				# Move out animation, slide out from the bottom to the top
	payload += '<AC>'				# Make the text narrower to fit more char on display
	return payload

def build_payload_stops(page_letter):
	# Datasheet https://asset.conrad.com/media10/add/160267/c1/-/en/000590996DS01/datablad-590996-mc-crypt-am03127-h13.pdf
	payload = '<L1>'				# Always use Line 1 as my display has only 1 line
	payload += f"<P{page_letter}>"	# Include page letter so we can have multiple trains in the playlist
	payload += '<FE>'				# Move in animation, in from the right
	payload += f"<MQ>"				# Set animation normal speed
	payload += '<WC>'				# Keep the text on screen for 9 seconds
	payload += '<FE>'				# Move out animation, move out to the left
	payload += '<AC>'				# Make the text narrower to fit more char on display
	return payload

DEVICE = "/dev/cu.usbserial-0001"
BAUD_RATE = 9600

ser=serial.Serial(
port=DEVICE,
baudrate = BAUD_RATE,
parity=serial.PARITY_NONE,
stopbits=serial.STOPBITS_ONE,
bytesize=serial.EIGHTBITS,
)

try:
	url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures?lang=nl&station=Bd&maxJourneys=5"

	hdr ={
	# Request headers
	'Cache-Control': 'no-cache',
	'Ocp-Apim-Subscription-Key': '####_YOUR_API_KEY_####',
	}

	req = urllib.request.Request(url, headers=hdr)

	req.get_method = lambda: 'GET'
	response = urllib.request.urlopen(req)

	data = json.loads(response.read())
	page_letter = 'A'

	for departure in data['payload']['departures']:

		destination = shorten_destination(departure['direction'])
		long_destination = departure['direction']

		train_category = departure['trainCategory']
		long_train_category = departure['product']['shortCategoryName']
		
		actual_time = departure['actualDateTime']
		departure__time_text = actual_time[11:16] # Slices the string to get 'HH:MM'

		
		departure_platform = departure['actualTrack']
		if(departure['cancelled']):
			departure__time_text = "Ann."

		# Print train info
		output_string = f"{train_category} {destination} <N55>{departure__time_text} {departure_platform}"
		first_payload = build_payload_station(page_letter) + output_string
		checksum = calculate_xor_checksum(first_payload.encode('latin-1', 'replace'))
		payload = f"<ID00>{first_payload}{checksum}<E>"
		page_letter = chr(ord(page_letter) + 1)
		
		ser.write(payload.encode('ascii'))
		print(f"Sent: {payload}")
		time.sleep(0.4)

		stops = ''
		for station in departure['routeStations']:
			stops += f"{station['mediumName']}, "
		
		stops = stops[:-2]

		if(departure['cancelled']):
			output_string = f"De {long_train_category} naar {destination} van {departure__time_text} rijdt niet."
			first_payload = build_payload_stops(page_letter) + output_string
			checksum = calculate_xor_checksum(first_payload.encode('latin-1', 'replace'))
			payload = f"<ID00>{first_payload}{checksum}<E>"
			page_letter = chr(ord(page_letter) + 1)

			ser.write(payload.encode('ascii'))
			print(f"Sent: {payload}")
			time.sleep(0.4)
			continue

		# Print stops info
		output_string = f"De {long_train_category} naar {long_destination} van {departure__time_text} stopt te {stops} en eindbestemming {long_destination}"
		first_payload = build_payload_stops(page_letter) + output_string
		checksum = calculate_xor_checksum(first_payload.encode('latin-1', 'replace'))
		payload = f"<ID00>{first_payload}{checksum}<E>"
		page_letter = chr(ord(page_letter) + 1)

		ser.write(payload.encode('ascii'))
		print(f"Sent: {payload}")
		time.sleep(0.4)

		# Print train info
		output_string = f"{train_category} {destination} <N55>{departure__time_text} {departure_platform}"
		first_payload = build_payload_station(page_letter) + output_string
		checksum = calculate_xor_checksum(first_payload.encode('latin-1', 'replace'))
		payload = f"<ID00>{first_payload}{checksum}<E>"
		page_letter = chr(ord(page_letter) + 1)

		ser.write(payload.encode('ascii'))
		print(f"Sent: {payload}")
		time.sleep(0.4)

	# Set a playlist to include 3 pages (as we only fetch 3 trains)
	playlist_id = 'A'			# Denotes the schedule no. form A-E (we can use A as we don't need multiple playlists)
	start_date = '0001010101'	# YYMMDDHHmm
	end_date = '9901010101'		# YYMMDDHHmm
	pages_in_order = 'ABCDE'		# First show page A, then B, then C
	playlist_payload = f"<T{playlist_id}>{start_date}{end_date}{pages_in_order}"
	checksum_playlist = calculate_xor_checksum(playlist_payload.encode('latin-1', 'replace'))
	payload = f"<ID00>{playlist_payload}{checksum_playlist}<E>" # formatted as start date, end date, playlist, checksum 
	ser.write(payload.encode('ascii'))
	print(f"Sent: {payload}")
	time.sleep(1)

except Exception as e:
	print(e)