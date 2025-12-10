from dataclasses import dataclass, field
from typing import List, Dict, Any

from params import Params

from params.loader import HARDWARE_PATH, CALIBRATIONS_PATH

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

    def thremo(self):
        return self.T1 * 6


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


class QPUConfig:
    qubits: Dict[str, QPUNode]

    def __init__(self):
        self.qubits = self._from_dict()

    @staticmethod
    def _from_dict(hardware=None, calibrations=None):

        if hardware is None:
            hardware = Params(HARDWARE_PATH).__dict__["data"]
        if calibrations is None:
            calibrations = Params(CALIBRATIONS_PATH).__dict__["data"]

        parsed = {}

        for qubit_id in hardware.keys():

            calibrations = calibrations[qubit_id]
            hardware = hardware[qubit_id]

            calibrations_q = calibrations["qubit"]
            calibrations_r = calibrations["resonator"]
            calibrations_g = calibrations["gates"]

            hardware_q = hardware["qubit"]
            hardware_r = hardware["resonator"]

            # ---- qubit output channels ----
            q_out = hardware_q["output"]
            q_chan = q_out["channel"]
            q_off = q_out["offset"]

            qubit_cfg = QubitConfig(
                IQ_input=IQInput(
                    I=q_chan.get("I", 0),
                    Q=q_chan.get("Q", 0),
                ),
                IQ_bias=IQBias(
                    I=q_off.get("I", 0.0),
                    Q=q_off.get("Q", 0.0),
                ),
                correction_gain=hardware_q.get("correction_gain"),
                correction_phase=hardware_q.get("correction_phase"),
                qubit_LO=hardware_q.get("LO_frequency"),
                qubit_ge_freq=calibrations_q.get("qubit_ge_freq"),
                qubit_ef_freq=calibrations_q.get("qubit_ef_freq"),
                T1=calibrations_q.get("T1"),
                T2=calibrations_q.get("T2"),
                thermalization_time=calibrations_q.get("thermalization_time"),
            )

            # # # ---- resonator output channels ----
            hw_res = hardware_r["output"]
            r_chan = hw_res["channel"]
            r_off = hw_res["offset"]

            resonator_cfg = ResonatorConfig(
                IQ_input=IQInput(
                    I=r_chan.get("I", 0),
                    Q=r_chan.get("Q", 0),
                ),
                IQ_bias=IQBias(
                    I=r_off.get("I", 0.0),
                    Q=r_off.get("Q", 0.0),
                ),
                correction_gain=hardware_r.get("correction_gain"),
                correction_phase=hardware_r.get("correction_phase"),
                resonator_LO=hardware_r.get("LO_frequency"),
                resonator_freq=calibrations_r.get("resonator_freq"),
                time_of_flight=calibrations_r.get("time_of_flight"),
                smearing=calibrations_r.get("smearing"),
                rotation_angle=calibrations_r.get("rotation_angle"),
                threshold=calibrations_r.get("threshold"),
            )

            # # # ---- gates ----
            calibrations_g = calibrations["gates"]

            gates_cfg = GatesConfig(
                square_gate=SquareGate(**calibrations_g["square_gate"]),
                gaussian_gate=GaussianGate(**calibrations_g["gaussian_gate"]),
                cos_gate=CosGate(**calibrations_g["cos_gate"]),
                drag_cos_gate=DragCosGate(**calibrations_g["drag_cos_gate"]),
                drag_gaussian_gate=DragGaussianGate(
                    **calibrations_g["drag_gaussian_gate"]
                ),
                saturation_pulse=SaturationPulse(**calibrations_g["saturation_pulse"]),
                readout_pulse=ReadoutPulse(**calibrations_g["readout_pulse"]),
            )

            parsed[qubit_id] = QPUNode(
                qubit=qubit_cfg,
                resonator=resonator_cfg,
                gates=gates_cfg,
            )

        return parsed


if __name__ == "__main__":

    qpu_config = QPUConfig()

    q10_params = qpu_config.qubits["q10"]

    print(q10_params.resonator.resonator_freq)
