#!/usr/bin/python3

import labgrid
import logging

from labgrid.logging import basicConfig, StepLogger

basicConfig(level=logging.INFO)

StepLogger.start()


env = labgrid.Environment("env.yaml")
target = env.get_target()
strategy = target.get_driver("Strategy")

strategy.transition("shell")

strategy.shell.run("systemctl status")
