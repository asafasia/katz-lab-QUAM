# Refactored Power Rabi Experiment (Updated Script)

import numpy as np
from scipy.optimize import curve_fit
from qm.qua import *
import matplotlib.pyplot as plt


from qualang_tools.results import progress_counter, fetching_tool
from qualang_tools.loops import from_array
from params import QPUConfig
from utils import Options
from experiments.core.base_experiment import BaseExperiment


class OptionsPowerRabi(Options):
    num_pis: int = 4
    n_avg: int = 100


class PowerRabiExperiment(BaseExperiment):
    def __init__(
        self,
        qubit: str,
        options: OptionsPowerRabi = OptionsPowerRabi(),
        amplitudes: np.ndarray = np.linspace(0, 1, 100),
        params: QPUConfig = None,
    ):
        super().__init__(qubit, options, params)

        self.amplitudes = amplitudes
        self.state_discrimination = False
        self.rabi_amp = self.params["q10"].gates

    def define_program(self):
        with program() as power_rabi:
            n = declare(int)
            a = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)
            state = declare(int)
            I_st = declare_stream()
            Q_st = declare_stream()
            n_st = declare_stream()
            state_st = declare_stream()

            with for_(n, 0, n < self.options.n_avg, n + 1):
                with for_(*from_array(a, self.amplitudes)):
                    qubit_initialization(self.options.active_reset)

                    for _ in range(self.options.num_pis):
                        play("X180" * amp(a), "qubit")

                    align("qubit", "resonator")
                    rr.measure("readout", qua_vars=(I, Q))

                    save(I, I_st)
                    save(Q, Q_st)
                    # save(state, state_st)

                save(n, n_st)

            with stream_processing():
                I_st.buffer(len(self.amplitudes)).average().save("I")
                Q_st.buffer(len(self.amplitudes)).average().save("Q")
                # state_st.buffer(len(self.amplitudes)).average().save("state")
                n_st.save("iteration")

        self.program = power_rabi

    def execute_program(self):

        qm = self.qmm.open_qm(self.config)
        self.job = qm.execute(self.program)
        variable_list = ["I", "Q", "iteration"]

        results = fetching_tool(self.job, data_list=variable_list, mode="live")

        while results.is_processing():
            I, Q, iteration = results.fetch_all()

            progress_counter(
                iteration, self.options.n_avg, start_time=results.get_start_time()
            )

        self.results = results

    def analyze_results(self):
        I, Q, iteration = self.results.fetch_all()

        self.data["amplitudes"] = self.amplitudes
        self.data["I"] = I
        self.data["Q"] = Q

        if self.options.state_discrimination:
            self.y = state
        else:
            Ic = np.max(I) - np.min(I)
            Qc = np.max(Q) - np.min(Q)
            self.y = I if Ic > Qc else Q
            self.quad_name = "I" if Ic > Qc else "Q"

        def cos_fit(x, a, b, c, d):
            return a * np.cos(2 * np.pi * 1 / b * x + c) + d

        try:
            self.fit_args = curve_fit(
                cos_fit,
                self.x,
                self.y,
                p0=[
                    max(self.y) / 2 - min(self.y) / 2,
                    self.rabi_amp * 2,
                    np.pi,
                    np.mean(self.y),
                ],
                maxfev=100000,
                xtol=1e-8,
                ftol=1e-8,
            )[0]
        except:
            self.fit_args = None

    def plot_results(self):

        amplitudes = self.data["amplitudes"]
        I = self.data["I"]
        Q = self.data["Q"]
        state = self.data["state"]

        plt.plot(amplitudes * self.rabi_amp * self.options.num_pis * 1e3, state, ".")
        plt.title("Power Rabi g->e transition")
        plt.xlabel("Rabi amplitude (mV)")
        plt.ylabel("state")
        plt.show()

    def save_results(self):
        pass

    def update_params(self):
        pass


if __name__ == "__main__":
    qubit = "q10"
    options = OptionsPowerRabi()
    options.n_avg = 100
    options.n_a = 100
    options.num_pis = 4

    amps = np.linspace(0, 1, 100)
    experiment = PowerRabiExperiment(
        qubit=qubit, options=options, amplitudes=amps, params=QPUConfig()
    )
    experiment.run()
