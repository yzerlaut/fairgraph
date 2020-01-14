# We use the brainsimulation namespace of the KG

import os

from fairgraph import brainsimulation, KGClient

client = KGClient(os.environ["HBP_token"]) # you need to have loaded you 

# The model source code is available in a public container at CSCS
container_url = 'https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo'
os.system('wget https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo/model/model_script.py')

from fairgraph.base import Distribution

# starting with script metadata underlying the model
model_script = brainsimulation.ModelScript(name='Script for Toy model of network dynamics for demo purpose',
                                           code_format='python',
                                           distribution=Distribution(container_url+'/model/model_script.py'),
                                           license='CC BY-SA')
model_script.save(client) # SAVE IN KG

# then model metadata
my_model = brainsimulation.ModelInstance(name='Toy model of neural network dynamics for demo purpose',
                                         main_script=model_script,
                                         description="""
                                         This model implements a very simple description of desynchronized 
                                         activity in neural assemblies:
                                         - Single neuron spiking consists of independent Poisson processes
                                         - Vm fluctuations are sampled from a random process with Gaussian distribution
                                         """,
                                         version='v0')

my_model.save(client) # SAVE IN KG

from model_script import run_model
from types import SimpleNamespace

args = SimpleNamespace(dt=1e-4,
                       tstop=1.,
                       seed=0,
                       freq=10.,
                       N_recVm=2,
                       E_rest=-70.,
                       V_thresh=-50.,
                       V_peak=-50.,
                       N_pops=[80,20],
                       N_show=2)

data = run_model(args)

spike_result = brainsimulation.SimulationResult(name='spike results of toy model in demo notebook',
                                                generated_by = my_model,
                                                report_file='spike_long_run.npz',
                                                data_type = 'network activity data', 
                                                variable='spike',
                                                target='soma',
                                                parameters = ''.join(['%s=%s ; ' % kv for kv in vars(args).items()]),
                                                description='Spiking results of toy model run in demo notebook')
spike_result.save(client)



print('The KG ID is:', spike_result.id)

# create the distribution
vm_location = brainsimulation.Distribution('https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo/data/Vm_long_run.npz')
# associate to the SimulationResult object
Vm_result = brainsimulation.SimulationResult(name='Vm results of toy model in demo notebook',
                                             generated_by = my_model,
                                             data_type = 'network activity data', 
                                             report_file=vm_location, # Now a Distribution !
                                             variable='spike',
                                             target='soma',
                                             parameters = ''.join(['%s=%s ; ' % kv for kv in vars(args).items()]),
                                             description='Intracelular data of toy model run in demo notebook')
# now saving will be succesfull
Vm_result.save(client)
print('The KG ID is:', Vm_result.id)
