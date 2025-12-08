import numpy as np

from utils import Options
from params import QPUConfig

from experiments.calibrations.iq_blobs import IQBlobsExperiment, IQBlobsOptions
from qpu.transmon import u


class ScanAmplitude:
    def __init__(
        self,
        qubit: str,
        options: Options,
        amplitudes: np.ndarray,
        params: QPUConfig = QPUConfig(),
    ):
        self.qubit = qubit
        self.options = options
        self.params = params
        self.data = dict()
        self.amplitudes = amplitudes

    def run(self):
        self.data["amplitudes"] = self.amplitudes
        self.data["fidelities"] = []

        options = IQBlobsOptions()
        options.simulate = False
        options.n_avg = 2000
        options.plot = False

        for amplitude in self.amplitudes:
            print(f"Amplitude: {amplitude}")
            self._update_amplitude(amplitude)
            iqblobs_experiment = IQBlobsExperiment(self.qubit, options, self.params)
            iqblobs_experiment.run()
            data = iqblobs_experiment.data
            self.data["fidelities"].append(data["fidelity"])

        return self.data

    def _update_amplitude(self, amplitude: float):
        self.params.qubits[self.qubit].gates.readout_pulse.amplitude = amplitude

    def plot_results(self):
        import matplotlib.pyplot as plt

        amplitudes = self.data["amplitudes"]
        fidelities = self.data["fidelities"]

        plt.figure(figsize=(10, 5))
        plt.title("Scan Amplitude")
        plt.grid()

        from scipy.ndimage import gaussian_filter
        fidelities_smooth = gaussian_filter(fidelities, sigma=1)


        plt.plot(amplitudes, fidelities)
        plt.plot(amplitudes, fidelities_smooth)
        
        plt.plot(amplitudes[np.argmax(fidelities_smooth)], fidelities_smooth[np.argmax(fidelities_smooth)], "ro")

        plt.xlabel("Amplitude")
        plt.ylabel("Fidelity")
        plt.show()


if __name__ == "__main__":

    amplitudes = np.linspace(0, 0.15, 100)
    scan_amplitude = ScanAmplitude(
        qubit="q10", options=Options(), amplitudes=amplitudes
    )
    scan_amplitude.run()
    scan_amplitude.plot_results()
