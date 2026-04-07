import os
import sys
from flask import render_template_string
from .workers import run_snapshot

class SnapshotScript:
    meta = {
        "name": "Snapshot",
        "version": "1.0.0",
        "description": (
            "Collect command outputs from multiple network devices "
            "and save them in text or Excel format."
        ),
        "icon": "camera",
    }

    def __init__(self, ctx=None):
        self.ctx = ctx

    @classmethod
    def input(self):
        input_template = os.path.join(
            os.path.dirname(__file__),
            "templates",
            "input.html"
        )
        return render_template_string(open(input_template).read())

    def run(self, inputs):
        devices = [d.strip() for d in inputs.get("devices", "").splitlines() if d.strip()]
        commands = [c.strip() for c in inputs.get("commands", "").splitlines() if c.strip()]
        output_type = inputs.get("output_type", "Text")
        connector = self.ctx.config.get("connector", {})

        # Validation
        if not devices:
            self.ctx.error("No devices provided")
            return

        if not commands:
            self.ctx.error("No commands provided")
            return

        if not connector:
            self.ctx.error("No Connector information provided")
            return

        # Execute worker logic
        run_snapshot(
            devices=devices,
            commands=commands,
            output_type=output_type,
            connector=connector,
            ctx=self.ctx
        )

        self.ctx.finish()







