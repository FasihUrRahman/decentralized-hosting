# peer_cli.py

import click
import json
import os
import subprocess
import signal
import time

CONFIG_FILE = "peer_config.json"
PID_FILE = "peer.pid"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

@click.group()
def cli():
    """A CLI to manage your decentralized hosting peer node."""
    pass

@cli.command()
def configure():
    """
    Creates or updates the configuration file for your peer node.
    """
    click.echo("--- Peer Node Setup ---")
    config_path = os.path.join(PROJECT_ROOT, CONFIG_FILE)
    if os.path.exists(config_path):
        if not click.confirm(f"A configuration file ('{CONFIG_FILE}') already exists. Overwrite?"):
            click.echo("Configuration cancelled.")
            return

    config_data = {}
    config_data['storage_gb'] = click.prompt("Storage to allocate (GB)?", type=int, default=100)
    config_data['node_port'] = click.prompt("Network port for this peer node?", type=int, default=8000)
    
    # --- MODIFIED: Ask for host and port in separate questions ---
    config_data['registry_host'] = click.prompt(
        "What is the HOSTNAME of the registry server? (e.g., localhost, or an IP address)",
        type=str,
        default="localhost"
    )
    config_data['registry_port'] = click.prompt(
        "What is the PORT of the registry server?",
        type=int,
        default=6000
    )
    config_data['peer_hostname'] = click.prompt(
        "This peer's reachable IP or DNS name? (e.g., your public IP)",
        type=str
    )
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        click.secho(f"\n✅ Configuration saved successfully to '{config_path}'!", fg='green')
    except Exception as e:
        click.secho(f"\n❌ Error saving configuration: {e}", fg='red')


@cli.command()
def start():
    """Starts the peer node as a background process."""
    config_path = os.path.join(PROJECT_ROOT, CONFIG_FILE)
    pid_path = os.path.join(PROJECT_ROOT, PID_FILE)

    if not os.path.exists(config_path):
        click.secho(f"Configuration file not found. Please run 'configure' first.", fg='red')
        return

    if os.path.exists(pid_path):
        click.secho("Peer node appears to be already running. Check 'status' or 'stop' it first.", fg='yellow')
        return

    with open(config_path, 'r') as f:
        config = json.load(f)

    env = os.environ.copy()
    env["NODE_PORT"] = str(config['node_port'])
    env["REGISTRY_HOST"] = config['registry_host']
    # --- NEW: Pass the registry port as an environment variable ---
    env["REGISTRY_PORT"] = str(config['registry_port'])
    env["PEER_HOSTNAME"] = config['peer_hostname']
    env["PYTHONPATH"] = PROJECT_ROOT
    
    command = ["python3", "-m", "client_node.shard_api"]
    log_path = os.path.join(PROJECT_ROOT, "peer.log")

    try:
        process = subprocess.Popen(command, env=env, cwd=PROJECT_ROOT, stdout=open(log_path, 'w'), stderr=subprocess.STDOUT)
        
        with open(pid_path, 'w') as f:
            f.write(str(process.pid))
            
        click.secho(f"✅ Peer node started in the background with PID: {process.pid}", fg='green')
        click.echo(f"Logs are being written to '{log_path}'.")
    except Exception as e:
        click.secho(f"❌ Failed to start peer node: {e}", fg='red')


@cli.command()
def stop():
    """Stops the running peer node process."""
    pid_path = os.path.join(PROJECT_ROOT, PID_FILE)
    if not os.path.exists(pid_path):
        click.secho("Peer node does not appear to be running.", fg='yellow')
        return

    with open(pid_path, 'r') as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM)
        click.secho(f"✅ Sent stop signal to peer node with PID: {pid}", fg='green')
    except ProcessLookupError:
        click.secho(f"Warning: Process with PID {pid} not found.", fg='yellow')
    except Exception as e:
        click.secho(f"❌ Error stopping process: {e}", fg='red')
    finally:
        os.remove(pid_path)


@cli.command()
def status():
    """Checks the status of the peer node."""
    pid_path = os.path.join(PROJECT_ROOT, PID_FILE)
    if not os.path.exists(pid_path):
        click.secho("⚪ Peer node is not running.", fg='white')
        return

    with open(pid_path, 'r') as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, 0)
        click.secho(f"✅ Peer node is running with PID: {pid}", fg='green')
    except OSError:
        click.secho("❌ Peer node is not running (stale PID file found).", fg='red')

if __name__ == '__main__':
    cli()