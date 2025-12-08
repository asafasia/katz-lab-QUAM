from dataclasses import dataclass, field
from typing import List, Dict, Any

from params import Params

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
class GateParams:
    length: float = 40e-9
    length_ef: float = None
    length_gf: float = None
    amplitude: float = 0.03
    amplitude_ef: float = None
    amplitude_gf: float = None


@dataclass
class SquareGate(GateParams):
    pass


@dataclass
class GaussianGate(GateParams):
    sigma: float = 1 / 3


@dataclass
class CosGate(GateParams):
    pass


@dataclass
class DragMixin:
    drag_coef: float = 0


@dataclass
class DragGaussianGate(DragMixin, GaussianGate):
    """Gaussian gate with DRAG correction."""

    pass


@dataclass
class DragCosGate(DragMixin, CosGate):
    """Cosine gate with DRAG correction."""

    pass


@dataclass
class ReadoutPulse(GateParams):
    pass


@dataclass
class SaturationPulse(GateParams):
    pass


@dataclass
class GatesConfig:
    square_gate: SquareGate
    gaussian_gate: GaussianGate
    cos_gate: CosGate
    drag_cos_gate: DragCosGate
    drag_gaussian_gate: DragGaussianGate
    saturation_pulse: SaturationPulse
    readout_pulse: ReadoutPulse


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
    T1: float
    T2: float
    thermalization_time: float

    @property
    def IF_freq(self) -> float:
        return self.qubit_LO - self.qubit_ge_freq

    @property
    def anharmonicity(self) -> float:
        return self.qubit_ef_freq - self.qubit_ge_freq

    @property
    def T_dephasing(self) -> float:
        return None


# ---------- Resonator Block ----------


@dataclass
class ResonatorConfig:
    IQ_input: IQInput
    IQ_bias: IQBias
    correction_gain: float
    correction_phase: float
    resonator_LO: float
    resonator_freq: float
    time_of_flight: float
    smearing: float
    rotation_angle: float
    threshold: float

    @property
    def IF_freq(self) -> float:
        return self.resonator_LO - self.resonator_freq


# ---------- Top-level QPU Object ----------


@dataclass
class QPUNode:
    qubit: QubitConfig
    resonator: ResonatorConfig
    gates: GatesConfig


@dataclass
class QPUConfig:
    """
    A dictionary of qubit IDs ("q10", "q11", ...) → QPUNode
    """

    qubits: Dict[str, QPUNode]

    def __init__(self):
        self.qubits = self._from_dict()

    @staticmethod
    def _from_dict(data: Dict[str, Any] = None):

        if data is None:
            data = Params().__dict__["data"]
        parsed = {}
        for name, node in data.items():

            qub = node["qubit"]
            res = node["resonator"]
            gat = node["gates"]

            parsed[name] = QPUNode(
                qubit=QubitConfig(
                    IQ_input=IQInput(**qub["IQ_input"]),
                    IQ_bias=IQBias(**qub["IQ_bias"]),
                    correction_gain=qub["correction_gain"],
                    correction_phase=qub["correction_phase"],
                    qubit_LO=qub["qubit_LO"],
                    qubit_ge_freq=qub["qubit_ge_freq"],
                    qubit_ef_freq=qub["qubit_ef_freq"],
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
                    time_of_flight=res["time_of_flight"],
                    smearing=res["smearing"],
                    rotation_angle=res["rotation_angle"],
                    threshold=res["threshold"],
                ),
                gates=GatesConfig(
                    square_gate=SquareGate(**gat["square_gate"]),
                    gaussian_gate=GaussianGate(**gat["gaussian_gate"]),
                    cos_gate=CosGate(**gat["cos_gate"]),
                    drag_cos_gate=DragCosGate(**gat["drag_cos_gate"]),
                    drag_gaussian_gate=DragGaussianGate(**gat["drag_gaussian_gate"]),
                    saturation_pulse=SaturationPulse(**gat["saturation_pulse"]),
                    readout_pulse=ReadoutPulse(**gat["readout_pulse"]),
                ),
            )

        return parsed


if __name__ == "__main__":

    qpu_config = QPUConfig()

    q10_params = qpu_config.qubits["q10"]

    q10_params.resonator.resonator_freq = 123

    print(q10_params.resonator.resonator_freq)
