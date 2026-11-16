#!/usr/bin/env python3
# read_drive.py — human-readable turn-by-turn from a DRIVE response.json

import json

with open('response.json') as f:
    data = json.load(f)

leg = data['routes'][0]['legs'][0]

print(f"Duration: {leg['localizedValues']['duration']['text']} "
      f"({leg['localizedValues']['distance']['text']})")
print()

for step in leg['steps']:
    inst = step.get('navigationInstruction', {}).get('instructions')
    if not inst:
        continue
    dist = step['localizedValues']['distance']['text']
    print(f"- {inst} ({dist})")

