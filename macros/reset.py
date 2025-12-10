from qm.qua import *
from macros.discrimination import discriminate
from utils import u
from qpu.transmon import KatzTransmon


def active_reset(qubit: KatzTransmon):
    I = declare(fixed)
    Q = declare(fixed)
    state = declare(int)

    for _ in range(2):
        qubit.resonator.measure("readout", qua_vars=(I, Q))
        state = discriminate(qubit, I, state)
        qubit.xy.play("X180")
        qubit.resonator.wait(1 * u.us)


def passive_reset(qubit):
    thermalization_time = qubit.parameters.qubit.thermalization_time * u.ns
    qubit.xy.align(qubit.resonator.name)
    wait(thermalization_time, qubit.name)
    qubit.xy.align(qubit.resonator.name)


def qubit_initialization(qubit, options):
    if options.active_reset:
        active_reset(qubit)
    else:
        passive_reset(qubit)
