from numpy import int16
from qpu.transmon import *
from config.config import *
from qm import QuantumMachinesManager, SimulationConfig
import numpy as np
from matplotlib import pyplot as plt
from qm.qua import *
from qualang_tools.loops import from_array

freqs = np.arange(-100e6, 100e6, 1e6)

qmm = QuantumMachinesManager(host=qm_host, port=qm_port)
qm = qmm.open_qm(qua_config)  # Open a quantum machine with the configuration
qubit = machine.qubits["q0"]

with program() as prog:
    f = declare(int)
    I_st_1 = declare_stream()
    Q_st_1 = declare_stream()
    I_st_2 = declare_stream()
    Q_st_2 = declare_stream()
    with for_(*from_array(f, freqs)):

        rr = qubit.resonator
        qubit.xy.update_frequency(f)
        qubit.resonator.update_frequency(f)

        qubit.resonator.align()

        I, Q = qubit.resonator.measure("readout")
        save(I, I_st_1)
        save(Q, Q_st_1)

        I, Q = qubit.resonator.measure("readout")
        save(I, I_st_2)
        save(Q, Q_st_2)

    with stream_processing():
        I_st_1.buffer(1).save_all("I1")
        Q_st_1.buffer(1).save_all("Q1")
        I_st_2.buffer(1).save_all("I2")
        Q_st_2.buffer(1).save_all("Q2")


simulate = False
from qualang_tools.results import progress_counter, fetching_tool

if simulate:
    job = qm.simulate(prog, SimulationConfig(duration=10000))
    job.get_simulated_samples().con1.plot()
else:
    job = qm.execute(prog)
    results = fetching_tool(job, data_list=["I", "Q"])

    print(results.fetch_all())
    plt.show()
