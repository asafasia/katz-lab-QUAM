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
        self.frequencies = frequencies
        qubit_LO = qubit.frequency_converter_up.LO_frequency
        qubit_RF = qubit.RF_frequency
        qubit_IF = qubit_LO - qubit_RF
        self.frequencies_IF = qubit_IF + self.frequencies
        # self.frequencies_RF = qubit_LO - self.frequencies

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
            variable_list = ["I1", "Q1", "I2", "Q2"]
            results = fetching_tool(job, data_list=variable_list)

            I1, Q1, I2, Q2 = results.fetch_all()

            # Average over shots (n_avg)
            I1 = np.mean(I1, axis=0)
            Q1 = np.mean(Q1, axis=0)
            I2 = np.mean(I2, axis=0)
            Q2 = np.mean(Q2, axis=0)

            self.data = {
                "frequencies": self.frequencies,
                "I1": I1,
                "Q1": Q1,
                "I2": I2,
                "Q2": Q2,
            }

    # --------------------------------------------------
    # Analysis
    # --------------------------------------------------
    def analyze_results(self):
        if self.options.simulate:
            return

        freqs = self.data["frequencies"]
        I1 = self.data["I1"]
        Q1 = self.data["Q1"]
        I2 = self.data["I2"]
        Q2 = self.data["Q2"]

        state1 = I1 + 1j * Q1
        state2 = I2 + 1j * Q2

        amp1 = np.abs(state1)
        amp2 = np.abs(state2)
        diff = np.abs(state1 - state2)

        idx_max = int(np.argmax(diff))
        f_max = float(freqs[idx_max])

        self.data["state1"] = state1
        self.data["state2"] = state2
        self.data["amp1"] = amp1
        self.data["amp2"] = amp2
        self.data["diff"] = diff
        self.data["f_max"] = f_max
        self.data["idx_max"] = idx_max

    # --------------------------------------------------
    # Plotting
    # --------------------------------------------------
    def plot_results(self):
        if self.options.simulate:
            # Plot the simulated samples (same style as your script)
            sim = self.data["simulation"]
            sim.con1.plot()
            return

        freqs = self.data["frequencies"]
        amp1 = self.data["amp1"]
        amp2 = self.data["amp2"]
        diff = self.data["diff"]
        f_max = self.data["f_max"]

        plt.figure()
        plt.plot(freqs, amp1, label="|state1| (ground)")
        plt.plot(freqs, amp2, label="|state2| (excited)")
        plt.plot(freqs, diff, label="|state1 - state2|")

        plt.axvline(f_max, linestyle="--", label=f"max diff: {f_max/1e9:.6f} GHz")

        plt.xlabel("Frequency [Hz]")
        plt.ylabel("Amplitude")
        plt.legend()
        plt.grid(True)

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

        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f, frequencies_IF)):
                # ---------- Ground state measurement ----------
                qubit.xy.align()
                qubit.update_frequency(f)
                qubit.xy.play("saturation", duration=10 * u.us)
                rr.measure("readout", qua_vars=(I, Q))
                rr.wait(300 * u.us)
                save(I, I_st)
                save(Q, Q_st)

        with stream_processing():
            I_st.buffer(len(frequencies_IF)).buffer(n_avg).save("I1")
            Q_st.buffer(len(frequencies_IF)).buffer(n_avg).save("Q1")

    return resonator_spec


# -------------------------------------------------------------------------
# Example main (matching your IQBlobs style)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    qubit = "q10"

    options = QubitSpecOptions()
    options.simulate = False
    # or True if you want simulation
    params = QPUConfig()

    # # Example: adjust readout pulse from params if you want
    params.qubits[qubit].gates.readout_pulse.amplitude = 0.05
    params.qubits[qubit].gates.readout_pulse.length = 2000 * u.ns

    span = 100 * u.MHz
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
    plt.show()
