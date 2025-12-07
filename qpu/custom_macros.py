@quam_dataclass
class MeasureMacro(QubitMacro):
    def apply(self):
        # integrating the PMT signal
        I,Q = self.qubit.resonator.measure("readout",outputs = None)

        return I,Q