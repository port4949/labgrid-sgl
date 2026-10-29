import enum

import attr

from labgrid.factory import target_factory
from labgrid.step import step
from labgrid.strategy.common import Strategy, StrategyError, never_retry


class Status(enum.Enum):
    unknown = 0
    off = 1
    hss = 2
    uboot = 3
    shell = 4


@target_factory.reg_driver
@attr.s(eq=False)
class BeaglevFireStrategy(Strategy):
    """BeaglevFireStrategy - Strategy to bootstrap and switch to HSS/uboot/shell"""
    bindings = {
        "power": "PowerProtocol",
        "console": "ConsoleProtocol",
        "uboot": "UBootDriver",
        "shell": "ShellDriver",
    }

    status = attr.ib(default=Status.unknown)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()

    @never_retry
    @step(args=['status'])
    def transition(self, status, *, step):  # pylint: disable=redefined-outer-name
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.unknown:
            raise StrategyError(f"can not transition to {status}")
        elif status == self.status:
            step.skip("nothing to do")
            return  # nothing to do
        elif status == Status.off:
            self.target.deactivate(self.console)
            self.target.activate(self.power)
            self.power.off()
        elif status == Status.hss:
            self.transition(Status.off)
            self.target.activate(self.console)
            self.power.cycle()
            self.target.activate(self.shell)
        elif status == Status.uboot:
            self.transition(Status.off)
            self.target.activate(self.console)
            # cycle power
            self.power.cycle()
            # interrupt uboot
            self.target.activate(self.uboot)
        elif status == Status.shell:
            self.transition(Status.off)
            self.target.activate(self.console)
            self.power.cycle()
            self.target.activate(self.shell)
            self.shell.run("systemctl is-system-running --wait")
        else:
            raise StrategyError(
                f"no transition found from {self.status} to {status}"
            )
        self.status = status

    @never_retry
    @step(args=['status'])
    def force(self, status, *, step):  # pylint: disable=redefined-outer-name
        if not isinstance(status, Status):
            status = Status[status]
        if status == Status.unknown:
            raise StrategyError(f"can not force state {status}")
        elif status == Status.off:
            self.target.deactivate(self.shell)
            self.target.activate(self.power)
        elif status == Status.shell:
            self.target.activate(self.power)
            self.target.activate(self.shell)
        else:
            raise StrategyError(f"not setup found for {status}")
        self.status = status
