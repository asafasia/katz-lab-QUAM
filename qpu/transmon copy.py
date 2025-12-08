from quam.components import *
from quam.examples.superconducting_qubits import Transmon, Quam

from params import QPUConfig

params = QPUConfig()


machine = Quam()

transmon = Transmon(id="10")
qubit_params = params.qubits["q10"]


machine.qubits[transmon.name] = transmon

transmon.xy = IQChannel(
    opx_output_I=("con1", 3),
    opx_output_Q=("con1", 4),
    frequency_converter_up=FrequencyConverter(
        mixer=Mixer(),
        local_oscillator=LocalOscillator(frequency=qubit_params.qubit.qubit_LO),
    ),
    intermediate_frequency=qubit_params.qubit.IF_freq,
)

transmon.resonator = InOutIQChannel(
    id=transmon.name,
    opx_output_I=("con1", 1),
    opx_output_Q=("con1", 2),
    opx_input_I=("con1", 1),
    opx_input_Q=(
        "con1",
        2,
    ),
    frequency_converter_up=FrequencyConverter(
        mixer=Mixer(),
        local_oscillator=LocalOscillator(frequency=qubit_params.resonator.resonator_LO),
    ),
    time_of_flight=qubit_params.resonator.time_of_flight,
    smearing=qubit_params.resonator.smearing,
    intermediate_frequency=qubit_params.resonator.IF_freq,
)


machine.save()
config = machine.generate_config()


if __name__ == "__main__":

    import pprint

    pprint.pprint(config)
    print("OK !!!")
    pass
