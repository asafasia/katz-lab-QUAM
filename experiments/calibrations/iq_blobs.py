import numpy as np
import matplotlib.pyplot as plt

from qm.qua import *
from qm import QuantumMachinesManager, SimulationConfig
from qualang_tools.results import fetching_tool

from qpu.transmon import *
from qpu.config import *

from qualang_tools.analysis.discriminator import two_state_discriminator
from experiments.core.base_experiment import BaseExperiment
from utils import Options
from dataclasses import dataclass


# -------------------------------------------------------------------------
# PARAMETERS
# -------------------------------------------------------------------------
@dataclass
class IQBlobsOptions(Options):
    n_avg: int = 5000


class IQBlobsExperiment(BaseExperiment):
    def __init__(
        self,
        qubit,
        options: IQBlobsOptions = IQBlobsOptions(),
        params: QPUConfig = None,
    ):

        super().__init__(qubit=qubit, options=options, params=params)

    def define_program(self):
        self.program = _program(self.qubit, self.options)

    def execute_program(self):
        self.qm = self.qmm.open_qm(self.config)
        job = self.qm.execute(self.program, dry_run=True)
        variable_list = ["Ig", "Qg", "Ie", "Qe"]
        results = fetching_tool(job, data_list=variable_list)

        Ig, Qg, Ie, Qe = results.fetch_all()
        self.data = {
            "Ig": Ig,
            "Qg": Qg,
            "Ie": Ie,
            "Qe": Qe,
        }

    def analyze_results(self):

        angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(
            self.data["Ig"],
            self.data["Qg"],
            self.data["Ie"],
            self.data["Qe"],
            b_print=False,
            b_plot=False,
        )
        self.data["angle"] = angle
        self.data["threshold"] = threshold
        self.data["fidelity"] = fidelity

    def plot_results(self):
        Ig = np.array(self.data["Ig"])
        Qg = np.array(self.data["Qg"])
        Ie = np.array(self.data["Ie"])
        Qe = np.array(self.data["Qe"])

        angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(
            Ig, Qg, Ie, Qe, b_print=self.options.plot, b_plot=self.options.plot
        )

    def save_results(self):
        pass

    def update_params(self):
        pass


def _program(qubit, options):
    rr = qubit.resonator

    with program() as iq_blobs:

        n = declare(int)
        shot = declare(int)
        Ig = declare(fixed)
        Qg = declare(fixed)
        Ie = declare(fixed)
        Qe = declare(fixed)
        Ig_st = declare_stream()
        Qg_st = declare_stream()
        Ie_st = declare_stream()
        Qe_st = declare_stream()

        with for_(n, 0, n < options.n_avg, n + 1):
            # ----------- Ground measurement ---------------
            qubit_initialization(qubit, active_reset=options.active_reset)
            rr.measure("readout", qua_vars=(Ig, Qg))
            save(Ig, Ig_st)
            save(Qg, Qg_st)

            # ----------- Excited measurement ---------------
            qubit_initialization(qubit, active_reset=options.active_reset)
            qubit.xy.play("X180")  # π pulse

            rr.measure("readout", qua_vars=(Ie, Qe))
            save(Ie, Ie_st)
            save(Qe, Qe_st)

        with stream_processing():
            Ig_st.buffer(options.n_avg).save("Ig")
            Qg_st.buffer(options.n_avg).save("Qg")
            Ie_st.buffer(options.n_avg).save("Ie")
            Qe_st.buffer(options.n_avg).save("Qe")

    return iq_blobs


def qubit_initialization(qubit, active_reset=False):
    thermalization = qubit.parameters.qubit.thermalization_time
    threshold = qubit.parameters.resonator.threshold
    I_reset = declare(fixed)
    Q_reset = declare(fixed)
    if active_reset:

        # qubit.xy.align()
        # qubit.resonator.align()
        qubit.resonator.measure("readout", qua_vars=(I_reset, Q_reset))
        # qubit.xy.align()
        # qubit.resonator.align()

        with if_(I_reset > threshold):
            qubit.xy.play("X180")
            wait(16 * u.ns, qubit.name)
        with else_():
            pass

    else:
        wait(thermalization, qubit.name)

    qubit.xy.align()
    qubit.resonator.align()


if __name__ == "__main__":

    from params import QPUConfig

    qubit = "q10"

    options = IQBlobsOptions()
    options.simulate = True
    options.active_reset = True
    options.simulate_duration = 1000 * u.ns
    params = QPUConfig()

    experiment = IQBlobsExperiment(qubit=qubit, options=options, params=params)

    experiment.run()

    plt.show()
