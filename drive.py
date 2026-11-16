#!/usr/bin/env python3
# drive.py — bottle wrapper around drivemap, reads response.json directly

import json
import subprocess
from bottle import route, request, run, template, static_file

FAVS_FILE = 'favs'
CONFIG_FILE = 'config'
RESPONSE_FILE = 'response.json'

SWITCH_SERVICES = {
    'mail': 't9amail-web.service',
    'map': 't9amap-web.service',
    'drive': 't9adrive-web.service',
}


def load_config():
    return dict(
        line.strip().split('=', 1)
        for line in open(CONFIG_FILE)
        if '=' in line and not line.strip().startswith('#')
    )


def load_favs():
    favs = {}
    with open(FAVS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or '=' not in line:
                continue
            name, addr = line.split('=', 1)
            favs[name.strip()] = addr.strip()
    return favs


def resolve(value, favs, cfg):
    value = value.strip()
    if value in favs:
        return favs[value]
    if ',' in value:
        return value
    return f"{value}, {cfg['CITY']}, {cfg['COUNTRY']}"


def load_favs_raw():
    """Load favs as an ordered list of (name, value) for display."""
    favs = []
    with open(FAVS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or '=' not in line:
                continue
            name, value = line.split('=', 1)
            favs.append((name.strip(), value.strip()))
    return favs


def add_fav(name, value):
    with open(FAVS_FILE, 'a') as f:
        f.write(f'{name.strip()}={value.strip()}\n')


def delete_fav(name):
    name = name.strip()
    lines = []
    with open(FAVS_FILE) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith(f'{name}='):
                continue
            lines.append(line)
    with open(FAVS_FILE, 'w') as f:
        f.writelines(lines)


def build_drive_data(origin, dest):
    """Read response.json directly and build a dict for drive_result.tpl."""
    with open(RESPONSE_FILE) as f:
        data = json.load(f)

    if 'routes' not in data or not data['routes']:
        return None

    leg = data['routes'][0]['legs'][0]

    duration = leg['localizedValues']['duration']['text']
    distance = leg['localizedValues']['distance']['text']

    steps = []
    for step in leg['steps']:
        inst = step.get('navigationInstruction', {}).get('instructions')
        if not inst:
            continue
        # collapse embedded newlines (e.g. "...\nDestination will be on the left")
        inst = inst.replace('\n', ' ')
        dist = step['localizedValues']['distance']['text']
        steps.append({'instruction': inst, 'distance': dist})

    return {
        'origin': origin,
        'dest': dest,
        'duration': duration,
        'distance': distance,
        'steps': steps,
    }


@route('/')
def form():
    return template('templates/input')


@route('/query', method='POST')
def query():
    cfg = load_config()
    favs = load_favs()
    origin = resolve(request.forms.get('origin', ''), favs, cfg)
    dest = resolve(request.forms.get('dest', ''), favs, cfg)

    if not origin or not dest:
        return template('templates/error', message='Missing origin or destination.')

    subprocess.run(
        ['./drivemap', origin, dest],
        capture_output=True,
        text=True
    )

    data = build_drive_data(origin, dest)

    if data is None:
        return template('templates/error', message='Could not compute route.')

    if not data['steps']:
        return template('templates/error', message='No route found.')

    return template('templates/drive_result', **data)


@route('/static/<filename>')
def serve_static(filename):
    return static_file(filename, root='static')


CITY_CHOICES = ['Auckland', 'Hamilton', 'Raglan', 'Tauranga', 'Wellington']


def set_config_value(key, value):
    lines = []
    found = False
    with open(CONFIG_FILE) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith(f'{key}=') and not stripped.startswith('#'):
                lines.append(f'{key}={value}\n')
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f'{key}={value}\n')
    with open(CONFIG_FILE, 'w') as f:
        f.writelines(lines)


@route('/admin')
def admin():
    cfg = load_config()
    favs = load_favs_raw()
    return template('templates/admin',
                     city=cfg.get('CITY', ''),
                     country=cfg.get('COUNTRY', ''),
                     favs=favs)


@route('/set_city', method='POST')
def set_city():
    city = request.forms.get('city', '').strip()
    if city:
        set_config_value('CITY', city)
    return '<p>City updated.</p><p><a href="/admin">back</a></p>'


@route('/set_country', method='POST')
def set_country():
    country = request.forms.get('country', '').strip()
    if country:
        set_config_value('COUNTRY', country)
    return '<p>Country updated.</p><p><a href="/admin">back</a></p>'


@route('/add_fav', method='POST')
def add_fav_confirm():
    name = request.forms.get('name', '').strip()
    value = request.forms.get('value', '').strip()
    if not (name and value):
        return template('templates/error', message='Name and value required.')
    return template('templates/add_fav_confirm', name=name, value=value)


@route('/add_fav_commit', method='POST')
def add_fav_commit():
    name = request.forms.get('name', '').strip()
    value = request.forms.get('value', '').strip()
    if name and value:
        add_fav(name, value)
    return '<p>Fav added.</p><p><a href="/admin">back</a></p>'


@route('/delete_fav', method='POST')
def delete_fav_route():
    name = request.forms.get('name', '').strip()
    if name:
        delete_fav(name)
    return '<p>Fav deleted.</p><p><a href="/admin">back</a></p>'


RESTART_SCRIPT = '/root/restart'

@route('/switch/<name>', method='POST')
def switch(name):
    if name not in SWITCH_SERVICES:
        return "unknown service"

    # fire-and-forget: the restart script stops this very process
    # as part of its work. Launched via systemd-run so it lives in
    # its own transient unit, outside drive's cgroup — otherwise
    # systemd kills it along with drive before it can finish.
    subprocess.Popen(['systemd-run', '--unit=t9aswitch', RESTART_SCRIPT, name])

    return '<p>Switching... <a href="/">Wait a few seconds then click to reload</a></p>'


if __name__ == '__main__':
    run(host='0.0.0.0', port=80)
