from quam.components import *
from quam.core import quam_dataclass

from quam_builder.architecture.superconducting.qpu import (
    FixedFrequencyQuam,
    FluxTunableQuam,
)

from quam.examples.superconducting_qubits import Transmon, Quam
from quam.components.pulses import SquarePulse
from quam.components.pulses import SquareReadoutPulse
from qm.qua import program

from qualang_tools.wirer import Instruments, Connectivity, allocate_wiring, visualize


from params.params_class import QPUConfig
from qualang_tools.units import unit

import matplotlib.pyplot as plt
from qualang_tools.wirer.wirer.channel_specs import *
from quam_config import Quam

qpu_config = QPUConfig.from_dict()
q10_params = qpu_config.nodes["q10"]

u = unit(coerce_to_integer=True)


@quam_dataclass
class Quam(FluxTunableQuam):
    pass


machine = Quam().load()


for k, qubit in enumerate(machine.qubits.values()):
    qubit.resonator.f_01 = q10_params.resonator.resonator_freq
    qubit.resonator.frequency_converter_up.LO_frequency = (
        q10_params.resonator.resonator_LO
    )
    qubit.resonator.opx_output_offset_I = q10_params.resonator.IQ_bias.I
    qubit.resonator.opx_output_offset_Q = q10_params.resonator.IQ_bias.Q
    qubit.resonator.frequency_converter_up.gain = q10_params.resonator.correction_gain
    qubit.resonator.frequency_converter_up.phase = q10_params.resonator.correction_phase

for k, qubit in enumerate(machine.qubits.values()):
    qubit.f_01 = q10_params.qubit.qubit_ge_freq
    qubit.xy.frequency_converter_up.LO_frequency = q10_params.qubit.qubit_LO
    qubit.xy.opx_output_offset_I = q10_params.qubit.IQ_bias.I
    qubit.xy.opx_output_offset_Q = q10_params.qubit.IQ_bias.Q
    qubit.xy.frequency_converter_up.gain = q10_params.qubit.correction_gain
    qubit.xy.frequency_converter_up.phase = q10_params.qubit.correction_phase

for k, q in enumerate(machine.qubits):
    # readout
    machine.qubits[q].resonator.operations["readout"].length = 2 * u.us
    machine.qubits[q].resonator.operations["readout"].amplitude = 0.05
    # Qubit saturation
    # machine.qubits[q].xy.operations["saturation"].length = 20 * u.us
    # machine.qubits[q].xy.operations["saturation"].amplitude = 0.3

    gaussian_pulse = SquarePulse(
        length=q10_params.qubit.square_gate.length,
        amplitude=q10_params.qubit.square_gate.amplitude_180,
    )

    machine.qubits[q].xy.operations["X180"] = gaussian_pulse

qua_config = machine.generate_config()


machine.save()

if __name__ == "__main__":
    machine.print_summary()


print("OK !!!")
