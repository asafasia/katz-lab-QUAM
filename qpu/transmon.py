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

from qualang_tools.units import unit


u = unit(coerce_to_integer=True)

params = QPUConfig()


def create_machine(params):
    machine = Quam()
    controller = "con1"
    transmon = Transmon(id="10")
    qubit_params = params.qubits["q10"].qubit
    resonator_params = params.qubits["q10"].resonator

    transmon.xy = IQChannel(
        opx_output_I=(controller, qubit_params.IQ_input.I),
        opx_output_Q=(controller, qubit_params.IQ_input.Q),
        opx_output_offset_I=qubit_params.IQ_bias.I,
        opx_output_offset_Q=qubit_params.IQ_bias.Q,
        frequency_converter_up=FrequencyConverter(
            mixer=Mixer(),
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
            mixer=Mixer(),
            local_oscillator=LocalOscillator(frequency=resonator_params.resonator_LO),
        ),
        time_of_flight=resonator_params.time_of_flight,
        smearing=resonator_params.smearing,
        intermediate_frequency=resonator_params.IF_freq,
    )

    # Assuming qubit_xy is configured as an IQChannel
    transmon.xy.operations["X180"] = pulses.SquarePulse(
        length=40, amplitude=0.0, axis_angle=0  # Phase angle on the IQ plane
    )

    transmon.resonator.operations["readout"] = pulses.SquareReadoutPulse(
        length=1000, amplitude=0.1, integration_weights=[(1, 500)]
    )

    machine.qubits[transmon.name] = transmon

    return machine


if __name__ == "__main__":

    machine = create_machine(params)

    machine.save()
    config = machine.generate_config()

    machine.load()
