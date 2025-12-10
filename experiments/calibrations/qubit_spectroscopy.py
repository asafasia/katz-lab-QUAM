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
from utils import Options
from utils import u


# -------------------------------------------------------------------------
# OPTIONS
# -------------------------------------------------------------------------
@dataclass
class QubitSpecOptions(Options):
    n_avg: int = 200


# -------------------------------------------------------------------------
# EXPERIMENT
# -------------------------------------------------------------------------
class QubitSpectroscopyExperiment(BaseExperiment):
    def __init__(
        self,
        qubit: str,
        frequencies: np.ndarray,
        options: QubitSpecOptions = QubitSpecOptions(),
        params: QPUConfig = None,
    ):
        super().__init__(qubit=qubit, options=options, params=params)

        qubit_LO = self.qubit.xy.LO_frequency
        qubit_IF = self.qubit.xy.intermediate_frequency
        self.qubit_RF = qubit_LO - qubit_IF

        self.frequencies = frequencies
        self.frequencies_IF = frequencies + qubit_IF
        self.frequencies_RF = -frequencies + self.qubit_RF

    # --------------------------------------------------
    # QUA program
    # --------------------------------------------------
    def define_program(self):

        self.program = _program(
            qubit=self.qubit,
            options=self.options,
            frequencies_IF=self.frequencies_IF,
        )

    # --------------------------------------------------
    # Execution
    # --------------------------------------------------
    def execute_program(self):
        self.qm = self.qmm.open_qm(self.config)

        if self.options.simulate:
            job = self.qm.simulate(
                self.program,
                SimulationConfig(duration=int(self.options.simulate_duration)),
            )
            self.data = {"simulation": job.get_simulated_samples()}
        else:
            job = self.qm.execute(self.program)
            variable_list = ["I", "Q", "state"]
            results = fetching_tool(job, data_list=variable_list)

            I, Q, state = results.fetch_all()

            # Average over shots (n_avg)
            I = np.mean(I, axis=0)
            Q = np.mean(Q, axis=0)
            state = np.mean(state, axis=0)

            self.data = {
                "frequencies": self.frequencies_RF,
                "I": I,
                "Q": Q,
                "state": state,
            }

    # --------------------------------------------------
    # Analysis
    # --------------------------------------------------
    def analyze_results(self):
        if self.options.simulate:
            return

        I = self.data["I"]
        Q = self.data["Q"]
        state = self.data["state"]

        self.data["state"] = state
        self.data["frequencies"] = self.frequencies_RF

        max_freq = np.argmin(np.abs(I))
        self.data["max_freq"] = self.frequencies_RF[max_freq]

    # --------------------------------------------------
    # Plotting
    # --------------------------------------------------
    def plot_results(self):

        freqs = self.data["frequencies"]
        states = self.data["state"]
        max_freq = self.data["max_freq"]
        print(int(max_freq))

        plt.figure()
        plt.plot(freqs, states, label="|state|")
        plt.axvline(max_freq, color="r", linestyle="--", label="max_freq")
        plt.axvline(
            self.qubit_RF, color="g", linestyle="--", label="current qubit freq"
        )
        plt.xlabel("Frequency [Hz]")
        plt.ylabel("state")
        plt.legend()
        plt.grid(True)
        plt.show()

    def save_results(self):
        # TODO: hook into your usual saving mechanism
        pass

    def update_params(self):
        # TODO: e.g., update resonator frequency in params based on f_max
        pass


# -------------------------------------------------------------------------
# QUA program factory
# -------------------------------------------------------------------------
def _program(qubit, options: QubitSpecOptions, frequencies_IF):
    rr = qubit.resonator
    n_avg = options.n_avg

    with program() as resonator_spec:
        n = declare(int)  # averaging loop
        f = declare(int)  # IF frequency

        I = declare(fixed)
        Q = declare(fixed)

        I_st = declare_stream()
        Q_st = declare_stream()
        state = declare(int)

        state_st = declare_stream()

        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f, frequencies_IF)):
                # ---------- Ground state measurement ----------
                qubit.xy.update_frequency(f)
                qubit.xy.play("saturation")
                qubit.xy.align()
                rr.measure("readout", qua_vars=(I, Q))
                rr.wait(300 * u.us)
                save(I, I_st)
                save(Q, Q_st)

                with if_(I > qubit.parameters.resonator.threshold):
                    assign(state, 1)
                with else_():
                    assign(state, 0)
                save(state, state_st)

        with stream_processing():
            I_st.buffer(len(frequencies_IF)).buffer(n_avg).save("I")
            Q_st.buffer(len(frequencies_IF)).buffer(n_avg).save("Q")
            state_st.buffer(len(frequencies_IF)).buffer(n_avg).save("state")

    return resonator_spec


# -------------------------------------------------------------------------
# Example main (matching your IQBlobs style)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    qubit = "q10"

    options = QubitSpecOptions()
    options.n_avg = 300
    options.simulate = False
    # or True if you want simulation
    params = QPUConfig()

    # Example: adjust saturation pulse from params if you want
    params.qubits[qubit].gates.saturation_pulse.amplitude = 0.001
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
