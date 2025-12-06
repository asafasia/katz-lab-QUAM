from transmon import *
from config import *
from qm import QuantumMachinesManager, SimulationConfig
from qm_saas import QmSaas


client = QmSaas(
    email="asaf.solonnikov@mail.huji.ac.il", password="CYbv+v3xVyVvyUhi6o+iEQ=="
)

with client.simulator() as instance:

    qmm = QuantumMachinesManager()
    qm = qmm.open_qm(qua_config)  # Open a quantum machine with the configuration

    with program() as prog:
        qubit = machine.qubits["q0"]

        # Apply the Gaussian pulse to the qubit
        qubit.xy.play("X90")

        # Perform readout on the qubit
        I, Q = qubit.resonator.measure("readout")

    job = qm.simulate(prog, SimulationConfig(duration=10_000))
    job.get_simulated_samples().con1.plot()
