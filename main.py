from numpy import int16
from qpu.transmon import *
from config.config import *
from qm import QuantumMachinesManager, SimulationConfig
import numpy as np
from matplotlib import pyplot as plt
from qm.qua import *
from qualang_tools.loops import from_array

freqs = np.arange(100e6, 110e6, 1e6)


qmm = QuantumMachinesManager(host=qm_host, port=qm_port)
qm = qmm.open_qm(qua_config)  # Open a quantum machine with the configuration
qubit = machine.qubits["q0"]

with program() as prog:

    f = declare(int)
    with for_(*from_array(f, freqs)):

        qubit.xy.update_frequency(f)
        qubit.resonator.update_frequency(f)

        # Apply the Gaussian pulse to the qubit
        qubit.xy.play("X90")
        qubit.xy.play("X90")
        qubit.xy.play("X90")
        qubit.xy.play("X90")

        qubit.resonator.align()

        # Perform readout on the qubit
        I, Q = qubit.resonator.measure("readout")

job = qm.simulate(prog, SimulationConfig(duration=10000))
job.get_simulated_samples().con1.plot()


plt.show()
