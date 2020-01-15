# We use the brainsimulation namespace of the KG
import os, time
from datetime import datetime

import sys
sys.path.append('../../')
from fairgraph import brainsimulation, KGClient

dev = True
if dev:
    client = KGClient(os.environ["HBP_token"],
                      nexus_endpoint='https://nexus-int.humanbrainproject.org/v0')
else:
    client = KGClient(os.environ["HBP_token"])
    
###############################################
### Downloading the (toy) Model of the demo ###
###############################################

# The model source code is available in a public container at CSCS
container_url = 'https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo'
if not os.path.isfile('model_script.py'):
    os.system('wget https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo/model/model_script.py')

from fairgraph.base import Distribution

###############################################
### Documenting Model Metadata ################
###############################################

## --> starting with script metadata underlying the model
model_script = brainsimulation.ModelScript(name='Script for Toy model#%s of network dynamics for demo purpose' % str(datetime.now),
                                           code_format='python',
                                           distribution=Distribution(container_url+'/model/model_script.py'),
                                           license='CC BY-SA')
model_script.save(client) # SAVE IN KG
print('The KG ID is:', model_script.id)
## --> building a model instance (version) from those metadata
my_model = brainsimulation.ModelInstance(name= 'Toy model#%s of neural network dynamics for demo purpose' % str(datetime.now),
                                         main_script=model_script,
                                         description="""
                                         This model#%s implements a very simple description of desynchronized 
                                         activity in neural assemblies:
                                         - Single neuron spiking consists of independent Poisson processes
                                         - Vm fluctuations are sampled from a random process with Gaussian distribution
                                         """  % str(datetime.now) ,
                                         version='v0')

my_model.save(client) # SAVE IN KG
print('The KG ID is:', my_model.id)

###############################################
### Documenting Simulation Metadata ###########
###############################################

## parameters
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

spike_result = brainsimulation.SimulationResult(name='spike results of toy model#%s in demo notebook'  % str(datetime.now),
                                                generated_by = my_model,
                                                report_file='spike_long_run.npz',
                                                data_type = 'network activity data', 
                                                variable='spike',
                                                target='soma',
                                                parameters = ''.join(['%s=%s ; ' % kv for kv in vars(args).items()]),
                                                description='Spiking results of toy model#%s run in demo notebook'  % str(datetime.now))
spike_result.save(client)
print('The KG ID is:', spike_result.id)


spike_config = brainsimulation.SimulationConfiguration(name='parameter configuration of toy model#%s in demo notebook'  % str(datetime.now))
spike_config.save(client)
print('The KG ID is:', spike_config.id)

sc = brainsimulation.ValidationScript(name='script of toy model#%s in demo notebook'  % str(datetime.now), date_created=datetime.now())
sim = brainsimulation.ValidationActivity(model_instance=my_model, test_script=sc)
# sim = brainsimulation.Simulation(name='parameter configuration of toy model#%s in demo notebook'  % str(datetime.now))
                                 # description='',
                                 # # configuration_used=spike_config,
                                 # # model_used=my_model,
                                 # ended_at_time=datetime.now())

sim.save(client)
print('The KG ID is:', sim.id)

# from types import SimpleNamespace

# args = SimpleNamespace(dt=1e-4,
#                        tstop=1.,
#                        seed=0,
#                        freq=10.,
#                        N_recVm=2,
#                        E_rest=-70.,
#                        V_thresh=-50.,
#                        V_peak=-50.,
#                        N_pops=[80,20],
#                        N_show=2)

# data = run_model(args)

# spike_config = brainsimulation.SimulationConfiguration(name='parameter configuration of toy model#%s in demo notebook'  % str(datetime.now))
# spike_config.save(client)

# spike_result = brainsimulation.SimulationResult(name='spike results of toy model#%s in demo notebook'  % str(datetime.now))
# # spike_result = brainsimulation.SimulationResult(name='spike results of toy model#%s in demo notebook'  % str(datetime.now),
# #                                                 generated_by = my_model,
# #                                                 report_file='spike_long_run.npz',
# #                                                 data_type = 'network activity data', 
# #                                                 variable='spike',
# #                                                 target='soma',
# #                                                 parameters = ''.join(['%s=%s ; ' % kv for kv in vars(args).items()]),
# #                                                 description='Spiking results of toy model#%s run in demo notebook'  % str(datetime.now),
# #                                                 timestamp=datetime.now())
# print(spike_result)
# spike_result.save(client)

# print('The KG ID is:', spike_result.id)

# # create the distribution
# vm_location = brainsimulation.Distribution('https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo/data/Vm_long_run.npz')
# # associate to the SimulationResult object
# Vm_result = brainsimulation.SimulationResult(name='Vm results of toy model#%s in demo notebook' % str(datetime.now),
#                                              generated_by = my_model,
#                                              data_type = 'network activity data', 
#                                              report_file=vm_location, # Now a Distribution !
#                                              variable='spike',
#                                              target='soma',
#                                              parameters = ''.join(['%s=%s ; ' % kv for kv in vars(args).items()]),
#                                              description='Intracelular data of toy model#%s run in demo notebook' % str(datetime.now) )
# # now saving will be succesfull
# #Vm_result.save(client)
# print('The KG ID is:', Vm_result.id)
