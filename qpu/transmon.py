from quam.components import (
    IQChannel,
    InOutIQChannel,
    FrequencyConverter,
    Mixer,
    LocalOscillator,
)
from quam.examples.superconducting_qubits import Transmon, Quam
from quam.components import pulses

from params import QPUConfig
from utils import u
from qpu.config import BASE_DIR


def create_machine(params: QPUConfig):
    machine = Quam()
    controller = "con1"
    transmon = Transmon(id="10")
    qubit_params = params.qubits["q10"].qubit
    resonator_params = params.qubits["q10"].resonator
    gates = params.qubits["q10"].gates

    transmon.xy = IQChannel(
        opx_output_I=(controller, qubit_params.IQ_input.I),
        opx_output_Q=(controller, qubit_params.IQ_input.Q),
        opx_output_offset_I=qubit_params.IQ_bias.I,
        opx_output_offset_Q=qubit_params.IQ_bias.Q,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(
                local_oscillator_frequency=qubit_params.qubit_LO,
                intermediate_frequency=qubit_params.IF_freq,
                correction_gain=qubit_params.correction_gain,
                correction_phase=qubit_params.correction_phase,
            ),
            local_oscillator=LocalOscillator(frequency=qubit_params.qubit_LO),
        ),
        intermediate_frequency=qubit_params.IF_freq,
    )

    transmon.resonator = InOutIQChannel(
        id=transmon.name,
        opx_input_I=(controller, 1),
        opx_input_Q=(controller, 2),
        opx_output_I=(controller, resonator_params.IQ_input.I),
        opx_output_Q=(controller, resonator_params.IQ_input.Q),
        opx_output_offset_I=resonator_params.IQ_bias.I,
        opx_output_offset_Q=resonator_params.IQ_bias.Q,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(
                local_oscillator_frequency=resonator_params.resonator_LO,
                intermediate_frequency=resonator_params.IF_freq,
                correction_gain=resonator_params.correction_gain,
                correction_phase=resonator_params.correction_phase,
            ),
            local_oscillator=LocalOscillator(
                frequency=resonator_params.resonator_LO, power=10
            ),
        ),
        # time_of_flight=resonator_params.time_of_flight,
        # smearing=resonator_params.smearing,
        intermediate_frequency=resonator_params.IF_freq,
    )

    transmon.xy.operations["X180"] = pulses.SquarePulse(
        length=gates.square_gate.length,
        amplitude=gates.square_gate.amplitude,
    )

    transmon.xy.operations["saturation"] = pulses.SquarePulse(
        length=gates.saturation_pulse.length,
        amplitude=gates.saturation_pulse.amplitude,
        axis_angle=0,
    )

    transmon.resonator.operations["readout"] = pulses.SquareReadoutPulse(
        length=gates.readout_pulse.length,
        amplitude=gates.readout_pulse.amplitude,
        integration_weights=[(1, gates.readout_pulse.length)],
        axis_angle=90,
    )

    machine.qubits[transmon.name] = transmon

    return machine


if __name__ == "__main__":

    params = QPUConfig()

    machine = create_machine(params)

    path = BASE_DIR / "params/data/state.json"

    machine.save(path)
    config = machine.generate_config()

    from pprint import pprint

    pprint(config)
    # machine.load()

    print(machine.qubits["10"].xy.inferred_intermediate_frequency)


