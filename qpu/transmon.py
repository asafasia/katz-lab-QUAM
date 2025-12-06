from quam.components import *

from quam.examples.superconducting_qubits import Transmon, Quam
from quam.components.pulses import GaussianPulse
from quam.components.pulses import SquareReadoutPulse
from qm.qua import program

from params.params_class import QPUConfig


qpu_config = QPUConfig.from_dict()
q10_params = qpu_config.nodes["q10"]


machine = Quam()


# Create transmon qubit component
transmon = Transmon(id=0)
machine.qubits[transmon.name] = transmon


# Add xy drive line channel
transmon.xy = IQChannel(
    opx_output_I=("con1", q10_params.qubit.IQ_input.I),
    opx_output_Q=("con1", q10_params.qubit.IQ_input.Q),
    opx_output_offset_I=q10_params.qubit.IQ_bias.I,
    opx_output_offset_Q=q10_params.qubit.IQ_bias.Q,
    frequency_converter_up=FrequencyConverter(
        mixer=Mixer(),
        local_oscillator=LocalOscillator(frequency=q10_params.qubit.qubit_LO),
    ),
    intermediate_frequency=qpu_config.qubit_IF_freq("q10"),
)


# Add resonator channel
transmon.resonator = InOutIQChannel(
    id=0,
    opx_output_I=("con1", q10_params.resonator.IQ_input.I),
    opx_output_Q=("con1", q10_params.resonator.IQ_input.Q),
    opx_input_I=("con1", q10_params.resonator.IQ_input.I),
    opx_input_Q=("con1", q10_params.resonator.IQ_input.Q),
    frequency_converter_up=FrequencyConverter(
        mixer=Mixer(),
        local_oscillator=LocalOscillator(frequency=q10_params.resonator.resonator_LO),
    ),
    intermediate_frequency=qpu_config.resonator_IF_freq("q10"),
)


gaussian_pulse = GaussianPulse(length=20, amplitude=0.2, sigma=3)
readout_pulse = SquareReadoutPulse(length=1000, amplitude=0.1)

machine.qubits["q0"].xy.operations["X90"] = gaussian_pulse
machine.qubits["q0"].resonator.operations["readout"] = readout_pulse

qua_config = machine.generate_config()


# machine.save("state.json")


# machine.print_summary()
