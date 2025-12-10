import numpy as np
from qm.qua import *
import matplotlib.pyplot as plt

from qualang_tools.results import fetching_tool, progress_counter
from qualang_tools.loops import from_array

from experiments.core.base_experiment import BaseExperiment
from utils import Options, u
from params import QPUConfig

from experiments.academic import echo_utils
import numpy as np

from macros.discrimination import discriminate
from macros.reset import qubit_initialization


# ----------------------------------------------------------------------
# Options
# ----------------------------------------------------------------------
class OptionsT1Spectroscopy2D(Options):
    n_avg: int = 200
    echo: bool = False


# ----------------------------------------------------------------------
# Main Experiment
# ----------------------------------------------------------------------
class T1Spectroscopy2DExperiment(BaseExperiment):
    def __init__(
        self,
        qubit: str,
        detunings: np.ndarray,
        amplitudes: np.ndarray,
        options: OptionsT1Spectroscopy2D = OptionsT1Spectroscopy2D(),
        params: QPUConfig = QPUConfig(),
    ):
        super().__init__(qubit, options, params)

        # Sweep parameters
        self.amplitudes = amplitudes

        # Frequency sweep centered around qubit LO
        f0 = self.qubit.parameters.qubit.qubit_ge_freq
        LO = self.qubit.parameters.qubit.qubit_LO
        self.detunings = detunings
        self.frequencies = LO - (f0 + self.detunings)

        self.qubit.xy.operations["lorentzian"] = echo_utils.LorentzianPulse(
            amplitude=0.1,
            length=10 * u.us,
            tau=1 * u.us,
            axis_angle=0,
            subtracted=False,
        )

        self.machine.qubits[self.qubit.name] = self.qubit
        self.config = self.machine.generate_config()

    # ------------------------------------------------------------------
    # Define Program
    # ------------------------------------------------------------------
    def define_program(self):
        qubit = self.qubit
        resonator = qubit.resonator

        with program() as spec_2d:
            n = declare(int)
            a = declare(fixed)
            df = declare(int)

            I = declare(fixed)
            Q = declare(fixed)
            state = declare(fixed)

            state_st = declare_stream()
            n_st = declare_stream()
            I_st = declare_stream()
            Q_st = declare_stream()

            # Main averaging loop
            with for_(n, 0, n < self.options.n_avg, n + 1):
                with for_(*from_array(df, self.frequencies)):
                    update_frequency(qubit.name, df)
                    with for_(*from_array(a, self.amplitudes)):
                        qubit_initialization(qubit, self.options)
                        qubit.xy.play("lorentzian", amplitude_scale=a)
                        qubit.xy.align(resonator.name)
                        resonator.measure("readout", qua_vars=(I, Q))
                        state = discriminate(qubit, I, state)
                        save(state, state_st)
                        save(I, I_st)
                        save(Q, Q_st)

                save(n, n_st)

            # Stream Processing
            with stream_processing():
                state_st.buffer(len(self.amplitudes)).buffer(
                    len(self.detunings)
                ).average().save("state")
                n_st.save("iteration")
                I_st.buffer(len(self.amplitudes)).buffer(
                    len(self.detunings)
                ).average().save("I")
                Q_st.buffer(len(self.amplitudes)).buffer(
                    len(self.detunings)
                ).average().save("Q")

        self.program = spec_2d

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------
    def execute_program(self):
        qm = self.qmm.open_qm(self.config)
        self.job = qm.execute(self.program)

        results = fetching_tool(
            self.job, data_list=["I", "Q", "state", "iteration"], mode="live"
        )

        while results.is_processing():
            I, Q, state, iteration = results.fetch_all()
            progress_counter(
                iteration, self.options.n_avg, start_time=results.get_start_time()
            )

        self.results = results

    # ------------------------------------------------------------------
    # Analyze Results
    # ------------------------------------------------------------------
    def analyze_results(self):

        I, Q, states, iteration = self.results.fetch_all()

        self.data["amplitudes"] = self.amplitudes
        self.data["frequencies"] = self.frequencies
        self.data["detunings"] = self.detunings
        self.data["state"] = states
        self.data["I"] = I
        self.data["Q"] = Q

        # Find maximum contrast → peak transition frequency
        idx = np.argmax(np.mean(states, axis=0))
        self.data["peak_frequency"] = self.frequencies[idx]

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------
    def plot_results(self):
        I = self.data["I"]
        Q = self.data["Q"]
        states = self.data["state"]
        amps = self.data["amplitudes"]
        dets = self.data["detunings"] / 1e6  # MHz

        print(I.shape)

        plt.pcolormesh(dets, amps, I.T)
        plt.xlabel("Detuning (MHz)")
        plt.ylabel("Amplitude")
        plt.title("T1 Spectroscopy 2D")
        plt.colorbar()
        plt.show()

    def plot_1d(self, idx):
        I = self.data["I"]
        Q = self.data["Q"]
        amps = self.data["amplitudes"]
        dets = self.data["detunings"] / 1e6  # MHz

        plt.plot(dets, I.T[idx])
        plt.xlabel("detuning")
        plt.ylabel("state")
        plt.title("T1 Spectroscopy 2D")
        plt.show()

    # ------------------------------------------------------------------
    # Save / Update Params
    # ------------------------------------------------------------------
    def save_results(self):
        pass

    def update_params(self):
        pass


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    qubit = "q10"
    options = OptionsT1Spectroscopy2D()
    options.n_avg = 100
    options.active_reset = False
    options.simulate = False
    options.simulate_duration = 10 * u.us
    span = 200e6
    detunings = np.linspace(-span / 2, span / 2, 101)
    amps = np.linspace(0.1, 1, 10)

    experiment = T1Spectroscopy2DExperiment(
        qubit=qubit,
        options=options,
        amplitudes=amps,
        detunings=detunings,
        params=QPUConfig(),
    )

    experiment.run()

    plt.show()

    # experiment.plot_1d(0)
