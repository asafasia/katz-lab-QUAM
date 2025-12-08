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


# -------------------------------------------------------------------------
# PARAMETERS
# -------------------------------------------------------------------------
class IQBlobsOptions(Options):
    pass


class IQBlobsExperiment(BaseExperiment):
    def __init__(self, qubit, options=None, params=None):

        if options is None:
            options = IQBlobsOptions()
        super().__init__(qubit, options, params)

    def define_program(self):
        self.program = _program(self.qubit, self.options)

    def execute_program(self):
        job = self.qm.execute(self.program)
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


def _program(qubit, n_avg, thermalization):
    rr = qubit.resonator

    with program() as iq_blobs:

        n = declare(int)
        shot = declare(int)
        # Ig = declare(fixed)
        # Qg = declare(fixed)
        # Ie = declare(fixed)
        # Qe = declare(fixed)
        Ig_st = declare_stream()
        Qg_st = declare_stream()
        Ie_st = declare_stream()
        Qe_st = declare_stream()

        with for_(n, 0, n < n_avg, n + 1):
            # ----------- Ground measurement ---------------
            rr.measure("readout", qua_vars=(Ig, Qg))
            save(Ig, Ig_st)
            save(Qg, Qg_st)
            wait(thermalization, rr.name)
            qubit.xy.align()

            # ----------- Excited measurement ---------------
            qubit.xy.play("X180")  # π pulse
            qubit.xy.align()

            rr.measure("readout", qua_vars=(Ie, Qe))
            save(Ie, Ie_st)
            save(Qe, Qe_st)

            wait(thermalization, rr.name)

        with stream_processing():
            Ig_st.buffer(n_avg).save("Ig")
            Qg_st.buffer(n_avg).save("Qg")
            Ie_st.buffer(n_avg).save("Ie")
            Qe_st.buffer(n_avg).save("Qe")

    return iq_blobs


if __name__ == "__main__":

    from params import QPUConfig

    qubit = "q10"

    params = QPUConfig()
    params.qubits[qubit].gates.readout_pulse.amplitude = 0.01
    params.qubits[qubit].gates.readout_pulse.length = 1000 * u.ns

    experiment = IQBlobsExperiment(qubit, params)
    experiment.run()
