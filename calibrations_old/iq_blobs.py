import numpy as np
import matplotlib.pyplot as plt
from qm.qua import *
from qm import QuantumMachinesManager, SimulationConfig
from qualang_tools.results import fetching_tool
from qualang_tools.loops import from_array

from qpu.transmon import *

# -------------------------------------------------------------------------
# PARAMETERS
# -------------------------------------------------------------------------
n_avg = 2000
thermalization = 300 * u.us

qubit = machine.qubits["q0"]
rr = qubit.resonator

resonator_LO = q10_params.resonator.resonator_LO
res_freq = q10_params.resonator.resonator_freq

simulate = False

# -------------------------------------------------------------------------
# QUA PROGRAM
# -------------------------------------------------------------------------
with program() as iq_blobs:

    n = declare(int)
    shot = declare(int)

    # single-shot measurements
    Ig = declare(fixed)
    Qg = declare(fixed)
    Ie = declare(fixed)
    Qe = declare(fixed)

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

        # ----------- Excited measurement ---------------
        qubit.xy.play("X180")  # π pulse
        align()

        rr.measure("readout", qua_vars=(Ie, Qe))
        save(Ie, Ie_st)
        save(Qe, Qe_st)

        wait(thermalization, rr.name)

    with stream_processing():
        Ig_st.buffer(n_avg).save("Ig")
        Qg_st.buffer(n_avg).save("Qg")
        Ie_st.buffer(n_avg).save("Ie")
        Qe_st.buffer(n_avg).save("Qe")


# -------------------------------------------------------------------------
# RUN
# -------------------------------------------------------------------------
if __name__ == "__main__":

    from config.config import *

    qmm = QuantumMachinesManager(host=qm_host, port=qm_port)
    qm = qmm.open_qm(qua_config)

    if simulate:
        job = qm.simulate(iq_blobs, SimulationConfig(duration=10 * u.us))
    else:
        job = qm.execute(iq_blobs)

        results = fetching_tool(job, ["Ig", "Qg", "Ie", "Qe"])
        Ig, Qg, Ie, Qe = results.fetch_all()

        # ---------------------------------------------------
        #   PROCESSING
        #   Ig/Qg: shape = [freq, n_avg, shots]
        # ---------------------------------------------------
        Ig = np.array(Ig)
        Qg = np.array(Qg)
        Ie = np.array(Ie)
        Qe = np.array(Qe)

        # collapse n_avg dimension → all shots in one dimension

        # choose frequency with biggest separation

        # select best frequency IQ data

        # ---------------------------------------------------
        #       PLOT IQ BLOBS
        # ---------------------------------------------------
        plt.figure(figsize=(6, 6))
        plt.scatter(Ig, Qg, s=5, alpha=0.3, label="|g⟩ shots")
        plt.scatter(Ie, Qe, s=5, alpha=0.3, label="|e⟩ shots")

        # centers
        plt.scatter(Ig.mean(), Qg.mean(), s=150, marker="x")
        plt.scatter(Ie.mean(), Qe.mean(), s=150, marker="x")

        from qualang_tools.analysis.discriminator import two_state_discriminator

        angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(
            Ig, Qg, Ie, Qe, b_print=True, b_plot=True
        )

        plt.xlabel("I")
        plt.ylabel("Q")
        plt.title("IQ Blobs (Ground vs Excited)")
        plt.legend()
        plt.axis("equal")
        plt.grid(True)
        plt.show()
