"""
Snapshot routes module.

Provides the SnapshotScript class for handling user input and executing
snapshot collection tasks across network devices. It validates inputs,
renders templates, and triggers worker execution.

File path: routes.py
"""

import logging
import os

from flask import render_template_string

from .workers import run_snapshot

logger = logging.getLogger(__name__)


class SnapshotScript:
    """Script to collect command outputs from network devices."""

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
        """Initialize SnapshotScript with context."""
        self.ctx = ctx

    @classmethod
    def required(self):
        return ["connector"]

    @classmethod
    def input(self):
        """Render input HTML template."""
        input_template = os.path.join(
            os.path.dirname(__file__),
            "templates",
            "input.html",
        )

        try:
            with open(input_template, encoding="utf-8") as file:
                template_content = file.read()
            return render_template_string(template_content)
        except Exception:
            logger.exception("Failed to load input template")
            raise

    def run(self, inputs):
        """Execute snapshot collection based on user inputs."""
        devices = [
            d.strip()
            for d in inputs.get("devices", "").splitlines()
            if d.strip()
        ]
        commands = [
            c.strip()
            for c in inputs.get("commands", "").splitlines()
            if c.strip()
        ]
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

        try:

            run_snapshot(
                devices=devices,
                commands=commands,
                output_type=output_type,
                connector=connector,
                ctx=self.ctx,
            )

        except Exception:
            raise

        self.ctx.finish()
