from experiments import IQBlobsExperiment
from utils import Options


qubit = "10"
options = Options()
experiment = IQBlobsExperiment(qubit, options)
# experiment.run()


print(options)
