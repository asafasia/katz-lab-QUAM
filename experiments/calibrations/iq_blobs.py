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
    def __init__(self, qubit, options=None):
        if options is None:
            options = IQBlobsOptions()
        super().__init__(qubit, options)

    def define_program(self):
        self.program = _program(self.qubit, self.options)

    def execute_program(self):
        pass

    def analyze_results(self):
        pass

    def plot_results(self):
        pass

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
    experiment = IQBlobsExperiment("q10")
    experiment.run()

# # -------------------------------------------------------------------------
# # RUN
# # -------------------------------------------------------------------------
# if __name__ == "__main__":

#     qmm = QuantumMachinesManager(host=qm_host, port=qm_port)
#     qm = qmm.open_qm(qua_config)

#     if simulate:
#         job = qm.simulate(iq_blobs, SimulationConfig(duration=10 * u.us))
#         job.get_simulated_samples().con1.plot()
#         plt.show()
#     else:
#         job = qm.execute(iq_blobs)

#         results = fetching_tool(job, ["Ig", "Qg", "Ie", "Qe"])
#         Ig, Qg, Ie, Qe = results.fetch_all()

#         # ---------------------------------------------------
#         #   PROCESSING
#         #   Ig/Qg: shape = [freq, n_avg, shots]
#         # ---------------------------------------------------
#         Ig = np.array(Ig)
#         Qg = np.array(Qg)
#         Ie = np.array(Ie)
#         Qe = np.array(Qe)

#         # collapse n_avg dimension → all shots in one dimension

#         # choose frequency with biggest separation

#         # select best frequency IQ data

#         # ---------------------------------------------------
#         #       PLOT IQ BLOBS
#         # ---------------------------------------------------

#         angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(
#             Ig, Qg, Ie, Qe, b_print=True, b_plot=True
#         )

#         plt.show()
