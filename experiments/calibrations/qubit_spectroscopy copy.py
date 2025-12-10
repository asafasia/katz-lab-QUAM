import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

from qm.qua import *
from qm import SimulationConfig
from qualang_tools.results import fetching_tool
from qualang_tools.loops import from_array

from qpu.transmon import *
from params import QPUConfig

from experiments.core.base_experiment import BaseExperiment
from utils import Options, u
from macros.discrimination import discriminate
from macros.reset import qubit_initialization


# -------------------------------------------------------------------------
# OPTIONS
# -------------------------------------------------------------------------
@dataclass
class QubitSpecOptions(Options):
    """Options for qubit spectroscopy."""

    n_avg: int = 200


# -------------------------------------------------------------------------
# EXPERIMENT
# -------------------------------------------------------------------------
class QubitSpectroscopyExperiment(BaseExperiment):
    """
    Performs single-tone qubit spectroscopy by sweeping the qubit IF frequency
    and measuring the resonator response.
    """

    def __init__(
        self,
        qubit: str,
        frequencies: np.ndarray,
        options: QubitSpecOptions = QubitSpecOptions(),
        params: QPUConfig = None,
    ):
        super().__init__(qubit=qubit, options=options, params=params)

        # LO and IF handling
        qubit_LO = self.qubit.xy.LO_frequency
        qubit_IF = self.qubit.xy.intermediate_frequency
        self.qubit_RF = qubit_LO - qubit_IF

        self.frequencies = frequencies
        self.frequencies_IF = frequencies + qubit_IF
        self.frequencies_RF = -frequencies + self.qubit_RF  # absolute frequencies

        self.amplitudes = np.linspace(0, 1, 50)

    # ------------------------------------------------------------------
    # QUA Program Definition
    # ------------------------------------------------------------------
    def define_program(self):
        self.program = _program(
            qubit=self.qubit,
            options=self.options,
            frequencies_IF=self.frequencies_IF,
            amplitudes=self.amplitudes,
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def execute_program(self):
        self.qm = self.qmm.open_qm(self.config)

        if self.options.simulate:
            job = self.qm.simulate(
                self.program,
                SimulationConfig(duration=int(self.options.simulate_duration)),
            )
            self.data = {"simulation": job.get_simulated_samples()}
            return

        # Normal hardware execution
        job = self.qm.execute(self.program)
        variables = ["I", "Q", "state"]
        results = fetching_tool(job, data_list=variables)

        I, Q, state = results.fetch_all()

        # Average over shots
        I = np.mean(I, axis=0)
        Q = np.mean(Q, axis=0)
        state = np.mean(state, axis=0)

        self.data = {
            "frequencies": self.frequencies_RF,
            "amplitudes": self.amplitudes,
            "I": I,
            "Q": Q,
            "state": state,
        }

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze_results(self):
        # if self.options.simulate:
        #     return

        # I = self.data["I"]
        # state = self.data["state"]
        # amplitudes = self.data["amplitudes"]

        # Extract minimum (transition point)
        # min_idx = np.argmin(np.abs(I))
        # self.data["max_freq"] = self.data["frequencies"][min_idx]
        pass

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------
    def plot_results(self):
        freqs = self.data["frequencies"]
        amplitudes = self.data["amplitudes"]
        states = self.data["state"]
        # max_freq = self.data["max_freq"]

        # print("Detected qubit frequency (Hz):", max_freq)

        plt.figure(figsize=(8, 5))
        plt.pcolormesh(freqs, amplitudes, states.T, label="Measured State")
        # # plt.axvline(max_freq, color="r", linestyle="--", label="Detected qubit freq")
        # plt.axvline(
        #     self.qubit_RF, color="g", linestyle="--", label="Current qubit freq"
        # )
        # plt.xlabel("Frequency    ")
        # plt.ylabel("am [Hz]")
        # plt.grid(True)
        # plt.legend()
        # plt.tight_layout()
        plt.show()

    def save_results(self):
        """Hook into your saving mechanism."""
        pass

    def update_params(self):
        """Optionally write back the extracted qubit frequency to params."""
        pass


# -------------------------------------------------------------------------
# QUA Program Factory
# -------------------------------------------------------------------------
def _program(qubit, options: QubitSpecOptions, frequencies_IF, amplitudes):
    rr = qubit.resonator
    n_avg = options.n_avg

    with program() as spec:
        n = declare(int)
        f = declare(int)
        a = declare(fixed)

        I = declare(fixed)
        Q = declare(fixed)

        I_st = declare_stream()
        Q_st = declare_stream()
        state = declare(int)
        state_st = declare_stream()

        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f, frequencies_IF)):
                qubit.xy.update_frequency(f)
                with for_(*from_array(a, amplitudes)):
                    qubit_initialization(qubit, options)

                    qubit.xy.play("saturation", a)
                    qubit.xy.align()

                    rr.measure("readout", qua_vars=(I, Q))

                    save(I, I_st)
                    save(Q, Q_st)

                    state = discriminate(qubit, I, state)
                    save(state, state_st)

        with stream_processing():
            I_st.buffer(len(amplitudes)).buffer(len(frequencies_IF)).buffer(n_avg).save(
                "I"
            )
            Q_st.buffer(len(amplitudes)).buffer(len(frequencies_IF)).buffer(n_avg).save(
                "Q"
            )
            state_st.buffer(len(amplitudes)).buffer(len(frequencies_IF)).buffer(
                n_avg
            ).save("state")

    return spec


# -------------------------------------------------------------------------
# MAIN (Example usage)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    qubit = "q10"

    options = QubitSpecOptions(
        n_avg=150,
        simulate=False,
    )

    params = QPUConfig()

    # Example: update pulse parameters
    params.qubits[qubit].gates.saturation_pulse.amplitude = 0.01
    params.qubits[qubit].gates.saturation_pulse.length = 100 * u.us

    span = 10 * u.MHz
    N = 100
    df = span // N
    frequencies = np.arange(-span / 2, span / 2, df)

    experiment = QubitSpectroscopyExperiment(
        qubit=qubit,
        frequencies=frequencies,
        options=options,
        params=params,
    )

    experiment.run()
