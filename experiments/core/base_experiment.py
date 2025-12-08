from abc import ABC, abstractmethod
from qm import QuantumMachinesManager, SimulationConfig
from utils.options import Options
from qm.qua import *

from qpu.transmon import create_machine
from params import QPUConfig
from qpu.config import *


class BaseExperiment(ABC):
    def __init__(
        self,
        qubit: str,
        options: Options,
        params: QPUConfig = None,
    ):

        self.data = dict()
        self.program = None
        self.options = options
        self.params = params

        self.qmm = QuantumMachinesManager(host=qm_host, port=qm_port)

        if params is None:
            params = QPUConfig()

        self.machine = create_machine(params)
        self.config = self.machine.generate_config()

        self.qubit = self.machine.qubits[qubit]

    @abstractmethod
    def define_program(self):
        pass

    @abstractmethod
    def execute_program(self):
        pass

    @abstractmethod
    def analyze_results(self):
        pass

    @abstractmethod
    def plot_results(self):
        pass

    @abstractmethod
    def save_results(self):
        pass

    @abstractmethod
    def update_params(self):
        pass

    def run(self):
        self.define_program()

        if self.options.simulate:
            import matplotlib.pyplot as plt

            simulation_config = SimulationConfig(
                duration=10_000
            )  # In clock cycles = 4ns
            job = self.qmm.simulate(self.config, self.program, simulation_config)
            job.get_simulated_samples().con1.plot()

            plt.show()
        else:

            if self.options.dc_set_voltage:
                # DC.set_voltage(qubit_flux_bias_channel, flux_bias)
                pass

            self.execute_program()

            if self.options.dc_set_voltage:
                # DC.set_voltage(qubit_flux_bias_channel, 0)
                pass

            self.analyze_results()
            if self.options.plot:
                self.plot_results()
            if self.options.save:
                self.save_results()

            if self.options.update_args:
                self.update_params()
