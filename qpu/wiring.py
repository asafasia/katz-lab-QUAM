from quam.components import *
from quam.core import quam_dataclass

from quam_builder.architecture.superconducting.qpu import (
    FixedFrequencyQuam,
    FluxTunableQuam,
)

from quam.examples.superconducting_qubits import Transmon, Quam
from quam.components.pulses import SquarePulse
from quam.components.pulses import SquareReadoutPulse
from qm.qua import program

from qualang_tools.wirer import Instruments, Connectivity, allocate_wiring, visualize


from params.params_class import QPUConfig
from qualang_tools.units import unit

import matplotlib.pyplot as plt
from qualang_tools.wirer.wirer.channel_specs import *
from qualang_tools.wirer import Instruments, Connectivity, allocate_wiring, visualize
from quam_builder.builder.qop_connectivity import build_quam_wiring
from quam_builder.builder.superconducting import build_quam
from transmon import Quam

u = unit(coerce_to_integer=True)

sa_address = "TCPIP0::192.168.43.100::inst0::INSTR"
host_ip = "192.168.43.253"
qm_port = 9510
cluster_name = "Cluster_1"  # Name of the cluster


qpu_config = QPUConfig.from_dict()
q10_params = qpu_config.nodes["q10"]

#########################################

instruments = Instruments()

instruments.add_opx_plus(controllers=[1])
instruments.add_external_mixer(indices=[1, 2])

#########################################
qubits = [10]
qubit_pairs = [(qubits[i], qubits[i + 1]) for i in range(len(qubits) - 1)]


#########################################

q1_res_ch = opx_iq_ext_mixer_spec(in_port_i=1, in_port_q=2, out_port_i=1, out_port_q=2)
q1_drive_ch = opx_iq_ext_mixer_spec(out_port_i=1, out_port_q=2)

#########################################


connectivity = Connectivity()
connectivity.add_resonator_line(qubits=qubits, constraints=q1_res_ch)
connectivity.add_qubit_drive_lines(qubits=qubits)
allocate_wiring(connectivity, instruments)

# visualize(connectivity.elements, available_channels=instruments.available_channels)
plt.show(block=True)

machine = Quam()
# Build the wiring (wiring.json) and initiate the QUAM
build_quam_wiring(connectivity, host_ip, cluster_name, machine)

# Reload QUAM, build the QUAM object and save the state as state.json
machine = Quam.load()
build_quam(machine)
