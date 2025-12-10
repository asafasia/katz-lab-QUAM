from quam.components import pulses
from quam.core import QuamComponent, quam_dataclass
from quam.components.pulses import Pulse
import numpy as np


@quam_dataclass
class LorentzianPulse(Pulse):
    """Lorentzian pulse QUAM component.

    Args:
        amplitude (float): The amplitude of the pulse in volts.
        length (int): The length of the pulse in samples.
        tau (float): The standard deviation of the gaussian pulse.
            Should generally be less than half the length of the pulse.
        axis_angle (float, optional): IQ axis angle of the output pulse in radians.
            If None (default), the pulse is meant for a single channel or the I port
                of an IQ channel
            If not None, the pulse is meant for an IQ channel (0 is X, pi/2 is Y).
        subtracted (bool): If true, returns a subtracted Gaussian, such that the first
            and last points will be at 0 volts. This reduces high-frequency components
            due to the initial and final points offset. Default is true.
    """

    amplitude: float
    length: int
    tau: float
    order: float = 1 / 2
    axis_angle: float = None
    subtracted: bool = True

    def waveform_function(self):
        t = np.arange(-self.length / 2, self.length / 2, dtype=int)
        waveform = self.amplitude * (1 + (t / self.tau) ** 2) ** (-self.order)

        if self.axis_angle is not None:
            waveform = waveform * np.exp(1j * self.axis_angle)
        return waveform

    # def waveform_function(self):
    #     t = np.arange(-self.length / 2, self.length / 2, dtype=int)
    #     waveform = (
    #         self.amplitude * (1 + (t / self.tau) ** 2) ** (-self.order) * 0
    #         + self.amplitude
    #     )

    #     if self.subtracted:
    #         waveform = waveform - waveform[-1]

    #     if self.axis_angle is not None:
    #         waveform = waveform * np.exp(1j * self.axis_angle)

    #     return waveform
