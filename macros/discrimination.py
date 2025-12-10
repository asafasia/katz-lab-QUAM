from qm.qua import *
from qpu.transmon import KatzTransmon


def discriminate(qubit: KatzTransmon, I: fixed, state: fixed):
    print(qubit)
    thr = qubit.parameters.resonator.threshold
    with if_(I > thr):
        assign(state, 1)
    with else_():
        assign(state, 0)
    return state
