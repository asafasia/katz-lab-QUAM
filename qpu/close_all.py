import qm
from qpu.config import qm_host, qm_port
from qm import QuantumMachinesManager, SimulationConfig
from qpu.transmon import create_machine
from params import QPUConfig

config = QPUConfig()
machine = create_machine(config)
config = machine.generate_config()

qmm = QuantumMachinesManager(host=qm_host, port=qm_port)


qmm.close_all_qms()

qmm.open_qm(config)

qmm.close_all_qms()

qmm.close_all_qms()
