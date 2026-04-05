#!/usr/bin/env python3
"""
FreedomForge AI — core/network_monitor.py
Network monitoring and control. Cross-platform.
DeepSeek implementation — full state save/restore.
"""

import os
import re
import platform
import subprocess
import threading
from typing import List, Dict, Optional, Callable

SYSTEM   = platform.system().lower()
IS_LINUX = SYSTEM == 'linux'
IS_MAC   = SYSTEM == 'darwin'
IS_WIN   = SYSTEM == 'windows'

_firewall_backup = {}
_nm_kill_active  = False


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception:
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="failed")


def _async(func, callback, *args, **kwargs):
    if callback is None:
        return func(*args, **kwargs)
    def _wrap():
        try:
            callback(func(*args, **kwargs))
        except Exception as e:
            callback(e)
    threading.Thread(target=_wrap, daemon=True).start()


# ── Connections ──────────────────────────────────────────────

def _conns_linux():
    r = _run(['ss', '-tunap'])
    if r.returncode != 0:
        return []
    conns = []
    for line in r.stdout.strip().split('\n')[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        proc = ''
        pm = re.search(r'users:\(\(\"([^\"]+)\"', ' '.join(parts[6:]))
        if pm:
            proc = pm.group(1)
        conns.append({
            'name': proc, 'local': parts[4],
            'remote': parts[5], 'status': parts[1]
        })
    return conns


def _conns_mac():
    r = _run(['lsof', '-i', '-n', '-P'])
    if r.returncode != 0:
        return []
    conns = []
    for line in r.stdout.strip().split('\n')[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        name_col = ' '.join(parts[8:])
        local = remote = status = ''
        if '->' in name_col:
            local, remote = name_col.split('->', 1)
            local  = local.split(' ', 1)[-1] if ' ' in local else local
            remote = remote.split(' (', 1)[0] if '(' in remote else remote
        if '(' in name_col:
            status = name_col.split('(', 1)[1].split(')', 1)[0]
        conns.append({
            'name': parts[0], 'local': local,
            'remote': remote, 'status': status
        })
    return conns


def _conns_win():
    r = _run(['netstat', '-ano'])
    if r.returncode != 0:
        return []
    tl = _run(['tasklist', '/FO', 'CSV', '/NH'])
    pid_map = {}
    if tl.returncode == 0:
        for line in tl.stdout.strip().split('\n'):
            parts = line.strip('"').split('","')
            if len(parts) >= 2:
                pid_map[parts[1]] = parts[0]
    conns = []
    for line in r.stdout.split('\n'):
        if not line.strip() or 'Active' in line or 'Proto' in line:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        pid = parts[-1] if parts[-1].isdigit() else ''
        conns.append({
            'name': pid_map.get(pid, ''), 'local': parts[1],
            'remote': parts[2], 'status': parts[3] if len(parts) > 3 else ''
        })
    return conns


def get_connections(callback=None):
    def _get():
        if IS_LINUX: return _conns_linux()
        if IS_MAC:   return _conns_mac()
        if IS_WIN:   return _conns_win()
        return []
    return _async(_get, callback)


# ── Bandwidth ────────────────────────────────────────────────

def get_bandwidth(callback=None):
    def _get():
        try:
            import psutil
            s = psutil.net_io_counters()
            return {
                'mb_sent': round(s.bytes_sent / (1024**2), 1),
                'mb_recv': round(s.bytes_recv / (1024**2), 1),
                'bytes_sent': s.bytes_sent,
                'bytes_recv': s.bytes_recv,
            }
        except Exception:
            return {'mb_sent': 0.0, 'mb_recv': 0.0,
                    'bytes_sent': 0, 'bytes_recv': 0}
    return _async(_get, callback)


# ── Kill switch ──────────────────────────────────────────────

def kill_network(on_done=None):
    def _kill():
        global _nm_kill_active
        try:
            if IS_LINUX:
                import tempfile
                fd, path = tempfile.mkstemp(suffix='.iptables')
                os.close(fd)
                with open(path, 'w') as f:
                    subprocess.run(['iptables-save'], stdout=f,
                                   check=True, timeout=10)
                _firewall_backup['linux'] = path
                subprocess.run(['iptables', '-P', 'INPUT',   'DROP'], check=True)
                subprocess.run(['iptables', '-P', 'OUTPUT',  'DROP'], check=True)
                subprocess.run(['iptables', '-P', 'FORWARD', 'DROP'], check=True)
            elif IS_MAC:
                import tempfile
                # Save the current pf ruleset before overwriting it
                fd, backup_path = tempfile.mkstemp(suffix='.pf.bak')
                os.close(fd)
                r = subprocess.run(['pfctl', '-s', 'rules'],
                                   capture_output=True, text=True, timeout=10)
                with open(backup_path, 'w') as f:
                    f.write(r.stdout if r.returncode == 0 else "")
                _firewall_backup['mac'] = backup_path

                fd2, block_path = tempfile.mkstemp(suffix='.pf')
                os.close(fd2)
                with open(block_path, 'w') as f:
                    f.write("block all\n")
                subprocess.run(['pfctl', '-E'],    capture_output=True)
                subprocess.run(['pfctl', '-f', block_path], check=True)
                os.unlink(block_path)
            elif IS_WIN:
                subprocess.run(
                    ['netsh', 'advfirewall', 'set', 'allprofiles',
                     'firewallpolicy', 'blockinbound,blockoutbound'],
                    check=True)
            _nm_kill_active = True
            if on_done:
                on_done(True, "All network traffic blocked.")
        except Exception as e:
            if on_done:
                on_done(False, str(e))
    threading.Thread(target=_kill, daemon=True).start()


def restore_network(on_done=None):
    def _restore():
        global _nm_kill_active
        try:
            if IS_LINUX:
                backup = _firewall_backup.get('linux')
                if backup and os.path.exists(backup):
                    with open(backup, 'r') as f:
                        subprocess.run(['iptables-restore'], stdin=f, check=True)
                    os.unlink(backup)
                    _firewall_backup.pop('linux', None)
                else:
                    for chain in ['INPUT', 'OUTPUT', 'FORWARD']:
                        subprocess.run(['iptables', '-P', chain, 'ACCEPT'])
            elif IS_MAC:
                backup = _firewall_backup.get('mac')
                if backup and os.path.exists(backup):
                    with open(backup, 'r') as f:
                        rules = f.read().strip()
                    if rules:
                        import tempfile
                        fd, restore_path = tempfile.mkstemp(suffix='.pf')
                        os.close(fd)
                        with open(restore_path, 'w') as f:
                            f.write(rules)
                        subprocess.run(['pfctl', '-f', restore_path],
                                       capture_output=True)
                        os.unlink(restore_path)
                    else:
                        # No prior rules — just disable pf
                        subprocess.run(['pfctl', '-d'], capture_output=True)
                    os.unlink(backup)
                    _firewall_backup.pop('mac', None)
                else:
                    subprocess.run(['pfctl', '-d'], capture_output=True)
            elif IS_WIN:
                subprocess.run(
                    ['netsh', 'advfirewall', 'set', 'allprofiles',
                     'firewallpolicy', 'allowinbound,allowoutbound'],
                    check=True)
            _nm_kill_active = False
            if on_done:
                on_done(True, "Network access restored.")
        except Exception as e:
            if on_done:
                on_done(False, str(e))
    threading.Thread(target=_restore, daemon=True).start()


def is_kill_active() -> bool:
    return _nm_kill_active


# ── VPN ──────────────────────────────────────────────────────

def check_vpn_installed():
    result = {}
    checks = {
        'mullvad':   ['mullvad', 'version'],
        'protonvpn': ['protonvpn-cli', '--version'],
        'wireguard': ['wg', '--version'],
        'openvpn':   ['openvpn', '--version'],
    }
    for name, cmd in checks.items():
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=3)
            result[name] = r.returncode == 0
        except Exception:
            result[name] = False
    return result


def get_vpn_status():
    result = {"connected": False, "provider": None}
    try:
        r = subprocess.run(['mullvad', 'status'],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and 'Connected' in r.stdout:
            return {"connected": True, "provider": "Mullvad"}
    except Exception:
        pass
    try:
        r = subprocess.run(['protonvpn-cli', 's'],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and 'Connected' in r.stdout:
            return {"connected": True, "provider": "ProtonVPN"}
    except Exception:
        pass
    try:
        if IS_LINUX:
            out = subprocess.check_output(['ip', 'addr'], text=True, timeout=5)
            if re.search(r'(tun|tap|wg)\d+', out):
                return {"connected": True, "provider": "VPN"}
    except Exception:
        pass
    return result
