import numpy as np

from utils import Options
from params import QPUConfig

from experiments.calibrations.iq_blobs import IQBlobsExperiment, IQBlobsOptions


class ScanAmplitude:
    def __init__(self, qubit: str, options: Options, params: QPUConfig = QPUConfig()):
        self.qubit = qubit
        self.options = options
        self.params = params
        self.data

    def run(self):
        self.data["amplitudes"] = self.amplitudes
        self.data["fidelities"] = []
        for amplitude in np.linspace(0, 0.1, 10):
            self._update_amplitude(amplitude)
            iqblobs_experiment = IQBlobsExperiment(
                self.qubit, self.options, self.params
            )
            iqblobs_experiment.run()
            data = iqblobs_experiment.data
            self.data["fidelities"].append(data["fidelity"])

        return self.data

    def _update_amplitude(self, amplitude: float):
        self.params.qubits[self.qubit].gates.readout_pulse.amplitude = amplitude

    def plot_results(self):
        import matplotlib.pyplot as plt

        plt.plot(self.data["amplitudes"], self.data["fidelities"])
        plt.xlabel("Amplitude")
        plt.ylabel("Fidelity")
        plt.show()


if __name__ == "__main__":

    amplitudes = np.linspace(0, 0.1, 10)
    scan_amplitude = ScanAmplitude("q10", Options())
    scan_amplitude.run()
