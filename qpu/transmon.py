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

from params.params_class import QPUConfig
from qualang_tools.units import unit

u = unit(coerce_to_integer=True)

qpu_config = QPUConfig.from_dict()
q10_params = qpu_config.nodes["q10"]


@quam_dataclass
class Quam(FluxTunableQuam):
    pass


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
        mixer=Mixer(
            intermediate_frequency=qpu_config.qubit_IF_freq("q10"),
            local_oscillator_frequency=q10_params.qubit.qubit_LO,
            correction_gain=q10_params.qubit.correction_gain,
            correction_phase=q10_params.qubit.correction_phase,
        ),
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
    opx_input_offset_I=q10_params.resonator.IQ_bias.I,
    opx_input_offset_Q=q10_params.resonator.IQ_bias.Q,
    frequency_converter_up=FrequencyConverter(
        mixer=Mixer(
            intermediate_frequency=qpu_config.resonator_IF_freq("q10"),
            local_oscillator_frequency=q10_params.resonator.resonator_LO,
            correction_gain=q10_params.resonator.correction_gain,
            correction_phase=q10_params.resonator.correction_phase,
        ),
        local_oscillator=LocalOscillator(frequency=q10_params.resonator.resonator_LO),
    ),
    intermediate_frequency=qpu_config.resonator_IF_freq("q10"),
)


gaussian_pulse = SquarePulse(
    length=q10_params.qubit.square_gate.length,
    amplitude=q10_params.qubit.square_gate.amplitude_180,
)
readout_pulse = SquareReadoutPulse(
    length=q10_params.resonator.readout_pulse_length,
    amplitude=q10_params.resonator.readout_pulse_amplitude,
)

machine.qubits["q0"].xy.operations["X180"] = gaussian_pulse
machine.qubits["q0"].resonator.operations["readout"] = readout_pulse


qua_config = machine.generate_config()


machine.save("state.json")


# # machine.print_summary()


# print(machine.active_qubits)
