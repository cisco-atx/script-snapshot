"""
This module contains the core worker logic for the Snapshot script.
- Connects to devices
- Runs commands concurrently
- Collects output
- Generates reports
"""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from netcore import GenericHandler

def run_snapshot(
    devices,
    commands,
    output_type,
    connector,
    ctx
):
    """
    Execute snapshot collection across multiple devices.

    Args:
        devices (list[str]): Device hostnames or IPs.
        commands (list[str]): Commands to run on each device.
        output_type (str): "Text" or "Excel".
        connector (dict): Connector credentials and jump host info.
        ctx (ScriptContext): Runner context for logging and output.
    """

    output_data = {}

    def snapshot_task(device):
        ctx.log(f"Connecting to {device}...")

        output_data[device] = {
            "prompt": "",
            "command_output": {}
        }

        proxy = None
        if connector.get("jumphost_ip"):
            proxy = {
                "hostname": connector["jumphost_ip"],
                "username": connector["jumphost_username"],
                "password": connector["jumphost_password"],
            }

        handler = GenericHandler(
            hostname=device,
            username=connector["network_username"],
            password=connector["network_password"],
            proxy=proxy,
            handler="NETMIKO",
            read_timeout_override=1000
        )

        ctx.log(f"Connected to {device} successfully")
        output_data[device]["prompt"] = handler.prompt

        ctx.log(f"Running commands on {device}")
        for command in commands:
            ctx.log(f"[{device}] Running: {command}")
            result = handler.sendCommand(command).strip()
            output_data[device]["command_output"][command] = result

        handler.close()
        ctx.log(f"Finished with {device}")


    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(snapshot_task, devices)

    generate_report(output_data, output_type, ctx)
    ctx.log("Snapshot execution finished")


def generate_report(output_data, output_type, ctx=None):
    """
    Generate output files from collected snapshot data.

    Args:
        output_data (dict): Collected command output per device.
        output_type (str): "Text" or "Excel".
        ctx (ScriptContext): Optional context for emitting file events.
    """

    from netcore import XLBW


    if output_type == "Text":
        for device, data in output_data.items():
            prompt = data["prompt"]
            filename = f"{prompt[:-1]}_{datetime.now():%Y-%m-%d_%H.%M}.txt"

            content = ""
            for cmd, out in data["command_output"].items():
                content += f"{prompt}{cmd}\n{out}\n{'-'*79}\n"

            ctx.save_file(filename, content.encode())
    else:
        dump_data = {}
        for i, (device, data) in enumerate(output_data.items(), start=1):
            dump_data[i] = {"Device": data["prompt"][:-1]}
            dump_data[i].update(data["command_output"])

        filename = f"Snapshot_{datetime.now():%Y-%m-%d_%H.%M}.xlsx"

        path = os.path.join(ctx.output_dir, filename)

        wb = XLBW(path)
        ws = wb.add_worksheet("Snapshot")
        wb.dump(dump_data, ws)
        wb.close()