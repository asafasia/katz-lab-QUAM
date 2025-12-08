# from quam.components import *
# from quam.core import quam_dataclass

# from quam_builder.architecture.superconducting.qpu import FixedFrequencyQuam
# from quam.examples.superconducting_qubits import Quam

# from qualang_tools.units import unit


########################################################################################################################
from quam.components.channels import IQChannel
import json
import numpy as np
from pprint import pprint

from qualang_tools.units import unit
from qpu import Quam
from quam_builder.builder.superconducting.pulses import add_DragCosine_pulses
from quam.components.pulses import GaussianPulse
from quam.components.pulses import SquarePulse

from params.params_class import QPUConfig
from qualang_tools.units import unit


qpu_config = QPUConfig.from_dict()
# qubit_name = "q10"
q10_params = qpu_config.nodes[qubit_name]

u = unit(coerce_to_integer=True)


machine = Quam.load()

for k, qubit in enumerate(machine.qubits.values()):

    qubit.resonator.f_01 = q10_params.resonator.resonator_freq
    qubit.resonator.RF_frequency = (
        q10_params.resonator.resonator_freq
    )  # Readout frequency
    qubit.resonator.frequency_converter_up.LO_frequency = (
        q10_params.resonator.resonator_LO
    )
    qubit.resonator.frequency_converter_up.gain = q10_params.resonator.correction_gain
    qubit.resonator.frequency_converter_up.phase = q10_params.resonator.correction_phase

    # qubit.resonator.IQ_bias.Q = q10_params
    # qubit.resonator.frequency_converter_up.gain = q10_params.resonator.correction_gain
    # qubit.resonator.frequency_converter_up.phase = q10_params.resonator.correction_phase

for k, qubit in enumerate(machine.qubits.values()):
    qubit.xy.frequency_converter_up.LO_frequency = q10_params.qubit.qubit_LO
    # qubit.xy.f_01 = q10_params.qubit.qubit_ge_freq
    qubit.xy.RF_frequency = q10_params.qubit.qubit_ge_freq  # Readout frequency

    qubit.xy.opx_output_offset_I = q10_params.qubit.IQ_bias.I
    qubit.xy.opx_output_offset_Q = q10_params.qubit.IQ_bias.Q
    qubit.xy.frequency_converter_up.gain = q10_params.qubit.correction_gain
    qubit.xy.frequency_converter_up.phase = q10_params.qubit.correction_phase


for k, q in enumerate(machine.qubits):
    machine.qubits[q].resonator.operations["readout"].length = 3 * u.us
    machine.qubits[q].resonator.operations["readout"].amplitude = 0.0793896

    square_pulse = SquarePulse(
        length=q10_params.qubit.square_gate.length,
        amplitude=q10_params.qubit.square_gate.amplitude_180,
    )
    machine.qubits[q].xy.operations["X180"] = square_pulse


qua_config = machine.generate_config()


machine.save()
# # Visualize the QUA config and save it
# pprint(machine.generate_config())
# with open("qua_config.json", "w+") as f:
#     json.dump(machine.generate_config(), f, indent=4)


if __name__ == "__main__":
    # machine.print_summary()

    import pprint

    pprint.pprint(qua_config)
    # print("OK !!!")
    pass
