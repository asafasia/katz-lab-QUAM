from dataclasses import dataclass, field
from typing import List, Dict, Any

from params.params import Params

# ---------- Basic Structures ----------


@dataclass
class IQInput:
    I: int
    Q: int


@dataclass
class IQBias:
    I: float
    Q: float


@dataclass
class Gate:
    length: float
    amplitude: float


@dataclass
class SquareGate:
    length: float
    length_ef: float
    length_gf: float
    amplitude_180: float
    amplitude_90: float
    amplitude_180_ef: float
    amplitude_180_gf: float


@dataclass
class GaussianGate:
    length: float
    amplitude: float
    sigma: float


@dataclass
class CosGate:
    length: float
    amplitude: float


@dataclass
class DragGate:
    length: float
    amplitude: float
    drag_coef: float


@dataclass
class SaturationPulse:
    length: float
    amplitude: float


# ---------- Qubit Block ----------


@dataclass
class QubitConfig:
    IQ_input: IQInput
    IQ_bias: IQBias
    correction_gain: float
    correction_phase: float
    qubit_LO: float
    qubit_ge_freq: float
    qubit_ef_freq: float
    qubit_anharmonicity: float
    sweet_spot_flag: int
    qubit_freq_sweet_spot: float
    qubit_freq_zero_bias: float
    flux_bias_channel: int
    flux_sweet_spot: float

    reset_gate: Gate
    square_gate: SquareGate
    gaussian_gate: GaussianGate
    cos_gate: CosGate
    drag_gate: DragGate
    saturation_pulse: SaturationPulse

    T1: float
    T2: float
    thermalization_time: float


# ---------- Resonator Block ----------


@dataclass
class ResonatorConfig:
    IQ_input: IQInput
    IQ_bias: IQBias
    correction_gain: float
    correction_phase: float
    resonator_LO: float
    resonator_freq: float
    readout_pulse_length: float
    readout_pulse_amplitude: float
    time_of_flight: float
    smearing: float
    rotation_angle: float
    threshold: float


# ---------- Top-level QPU Object ----------


@dataclass
class QPUNode:
    qubit: QubitConfig
    resonator: ResonatorConfig


@dataclass
class QPUConfig:
    """
    A dictionary of qubit IDs ("q10", "q11", ...) → QPUNode
    """

    nodes: Dict[str, QPUNode]

    @staticmethod
    def from_dict(data: Dict[str, Any] = None) -> "QPUConfig":

        if data is None:
            data = Params().__dict__["data"]
        parsed = {}
        for name, node in data.items():

            qub = node["qubit"]
            res = node["resonator"]

            parsed[name] = QPUNode(
                qubit=QubitConfig(
                    IQ_input=IQInput(**qub["IQ_input"]),
                    IQ_bias=IQBias(**qub["IQ_bias"]),
                    correction_gain=qub["correction_gain"],
                    correction_phase=qub["correction_phase"],
                    qubit_LO=qub["qubit_LO"],
                    qubit_ge_freq=qub["qubit_ge_freq"],
                    qubit_ef_freq=qub["qubit_ef_freq"],
                    qubit_anharmonicity=qub["qubit_anharmonicity"],
                    sweet_spot_flag=qub["sweet_spot_flag"],
                    qubit_freq_sweet_spot=qub["qubit_freq_sweet_spot"],
                    qubit_freq_zero_bias=qub["qubit_freq_zero_bias"],
                    flux_bias_channel=qub["flux_bias_channel"],
                    flux_sweet_spot=qub["flux_sweet_spot"],
                    reset_gate=Gate(**qub["reset_gate"]),
                    square_gate=SquareGate(**qub["square_gate"]),
                    gaussian_gate=GaussianGate(**qub["gaussian_gate"]),
                    cos_gate=CosGate(**qub["cos_gate"]),
                    drag_gate=DragGate(**qub["drag_gate"]),
                    saturation_pulse=SaturationPulse(**qub["saturation_pulse"]),
                    T1=qub["T1"],
                    T2=qub["T2"],
                    thermalization_time=qub["thermalization_time"],
                ),
                resonator=ResonatorConfig(
                    IQ_input=IQInput(**res["IQ_input"]),
                    IQ_bias=IQBias(**res["IQ_bias"]),
                    correction_gain=res["correction_gain"],
                    correction_phase=res["correction_phase"],
                    resonator_LO=res["resonator_LO"],
                    resonator_freq=res["resonator_freq"],
                    readout_pulse_length=res["readout_pulse_length"],
                    readout_pulse_amplitude=res["readout_pulse_amplitude"],
                    time_of_flight=res["time_of_flight"],
                    smearing=res["smearing"],
                    rotation_angle=res["rotation_angle"],
                    threshold=res["threshold"],
                ),
            )

        return QPUConfig(nodes=parsed)

    def qubit_IF_freq(self, qubit_name: str) -> float:
        qubit_LO = self.nodes[qubit_name].qubit.qubit_LO
        qubit_ge_freq = self.nodes[qubit_name].qubit.qubit_ge_freq
        return qubit_LO - qubit_ge_freq

    def resonator_IF_freq(self, qubit_name: str) -> float:
        resonator_LO = self.nodes[qubit_name].resonator.resonator_LO
        resonator_freq = self.nodes[qubit_name].resonator.resonator_freq
        return resonator_LO - resonator_freq


if __name__ == "__main__":

    qpu_config = QPUConfig.from_dict()

    # Example: access q10
    q10_params = qpu_config.nodes["q10"]
    print(q10_params.qubit.qubit_ge_freq)
    print(q10_params.resonator.resonator_freq)
