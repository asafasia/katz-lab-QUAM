import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from qm import QuantumMachinesManager, SimulationConfig

from qm.qua import *
from qm import QuantumMachinesManager
from qualang_tools.results import fetching_tool
from qualang_tools.loops import from_array
from qpu.config import *
from qpu.transmon import *


n_avg = 200
long_pulse = True

qubit = machine.qubits["q10"]


resonator_LO = qubit.resonator.frequency_converter_up.LO_frequency
resonator_freq = qubit.resonator.RF_frequency
span = 200e6
df = 1e6

f_min = resonator_freq - span / 2
f_max = resonator_freq + span / 2
frequencies = np.arange(f_min, f_max, df)
frequencies_IF = resonator_LO - frequencies
thermalization = 300 * u.us
simulate = False

with program() as resonator_spec:
    n = declare(int)  # QUA variable for the averaging loop
    f = declare(int)  # QUA variable for the readout frequency
    I1 = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q1 = declare(fixed)  # QUA variable for the measured 'Q' quadrature\
    I2 = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q2 = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st1 = declare_stream()  # Stream for the 'I' quadrature
    Q_st1 = declare_stream()  # Stream for the 'Q' quadrature
    I_st2 = declare_stream()  # Stream for the 'I' quadrature
    Q_st2 = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'

    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(f, frequencies_IF)):
            rr = qubit.resonator
            rr.update_frequency(f)
            rr.measure("readout", qua_vars=(I1, Q1), stream=None)
            rr.wait(thermalization)
            rr.align()

            save(I1, I_st1)
            save(Q1, Q_st1)

            # qubit.xy.play("X180")
            # rr.align()

            # rr.measure("readout", qua_vars=(I2, Q2), stream=None)
            # wait(thermalization, rr.name)
            # save(I2, I_st2)
            # save(Q2, Q_st2)

    with stream_processing():
        I_st1.buffer(len(frequencies)).buffer(n_avg).save("I1")
        Q_st1.buffer(len(frequencies)).buffer(n_avg).save("Q1")
        # I_st2.buffer(len(frequencies)).buffer(n_avg).save("I2")
        # Q_st2.buffer(len(frequencies)).buffer(n_avg).save("Q2")
        # n_st.save("iteration")
        pass


if __name__ == "__main__":

    qmm = QuantumMachinesManager(host=qm_host, port=qm_port)
    qm = qmm.open_qm(qua_config)  # Open a quantum machine with the configuration

    if simulate:
        job = qm.simulate(resonator_spec, SimulationConfig(duration=100 * u.us))
        job.get_simulated_samples().con1.plot()
        plt.show()
    else:
        job = qm.execute(resonator_spec)
        results = fetching_tool(job, data_list=["I1", "Q1", "I2", "Q2"])

        I1, Q1, I2, Q2 = results.fetch_all()

        I1 = np.mean(I1, axis=0)
        Q1 = np.mean(Q1, axis=0)
        # I2 = np.mean(I2, axis=0)
        # Q2 = np.mean(Q2, axis=0)

        state1 = I1 + 1j * Q1
        # state2 = I2 + 1j * Q2

        # diff = state1 - state2

        # state1 = np.abs(state1)
        # state2 = np.abs(state2)

        # diff = np.abs(diff)

        # # find max freq of diff
        # max_freq = frequencies[np.argmax(diff)]
        # print(max_freq)

        # plt.plot(frequencies, state1)
        # plt.plot(frequencies, state2)
        # plt.plot(frequencies, diff)
        # plt.axvline(max_freq, color="r", label="max diff")
        # plt.axvline(resonator_freq, color="g", label="current freq")
        # plt.legend()
        # plt.show()
