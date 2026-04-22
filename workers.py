"""Worker logic for snapshot execution.

This module handles connecting to devices, executing commands concurrently,
collecting outputs, and generating reports in text or Excel format.

File path: workers.py
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
    """Execute snapshot collection across multiple devices."""
    output_data = {}

    def snapshot_task(device):
        """Run snapshot commands on a single device."""
        try:
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

        except Exception as exc:
            ctx.log(f"Error processing {device}: {exc}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(snapshot_task, devices)

    generate_report(output_data, output_type, ctx)
    ctx.log("Snapshot execution finished")


def generate_report(output_data, output_type, ctx=None):
    """Generate output files from collected snapshot data."""
    from netcore import XLBW

    if output_type == "Text":
        for device, data in output_data.items():
            prompt = data["prompt"]
            filename = (
                f"{prompt[:-1]}_{datetime.now():%Y-%m-%d_%H.%M}.txt"
            )

            content = "".join(
                f"{prompt}{cmd}\n{out}\n{'-' * 79}\n"
                for cmd, out in data["command_output"].items()
            )

            ctx.save_file(filename, content.encode())

    else:
        dump_data = {
            i: {"Device": data["prompt"][:-1], **data["command_output"]}
            for i, (_, data) in enumerate(output_data.items(), start=1)
        }

        filename = f"Snapshot_{datetime.now():%Y-%m-%d_%H.%M}.xlsx"
        path = os.path.join(ctx.output_dir, filename)

        wb = XLBW(path)
        ws = wb.add_worksheet("Snapshot")
        wb.dump(dump_data, ws)
        wb.close()
