import os, time
from datetime import datetime

from fairgraph import brainsimulation, KGClient, base, uniminds

# needs to have HBP_AUTH_TOKEN set as a bash variable
client = KGClient()


###############################################
### Downloading the (toy) Model of the demo ###
###############################################

# The model source code is available in a public container at CSCS
container_url = 'https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo'
if not os.path.isfile('model_script.py'):
    os.system('wget https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo/model/model_script.py')

###############################################
### Documenting Model Metadata ################
###############################################

## --> starting with script metadata underlying the model
model_script = brainsimulation.ModelScript(name='Script for Toy model#%s of network dynamics for demo purpose' % str(datetime.now),
                                code_format='python',
                                distribution=base.Distribution(container_url+'/simulation_script.py'),
                                license='CC BY-SA')
model_script.save(client) # SAVE IN KG
print('The KG ID is:', model_script.id)

## --> then model metadata
my_model = brainsimulation.ModelInstance(name= 'Toy model#%s of neural network dynamics for demo purpose' % str(datetime.now),
                         description="""
                         This model#%s implements a very simple description of desynchronized 
                         activity in neural assemblies:
                         - Vm fluctuations are sampled from a random process with Gaussian distribution
                         - Single neuron spiking consists of the positive crossing events above a certain threshold 
                         """  % str(datetime.now()),
                         main_script=model_script,
                        version='v0')

my_model.save(client) # SAVE IN KG
print('The KG ID is:', my_model.id)

###############################################
### Documenting Simulation Metadata ###########
###############################################

## script
sc = brainsimulation.SimulationScript(name='script of toy model#%s in demo notebook'  % str(datetime.now),
                                      script_file='simulation.py',
                                      code_format='python')
sc.save(client)
print('The KG ID is:', sc.id)

## --> parameters/configuration
import json
parameters = dict(dt=1e-4, tstop=1., seed=0,
                  freq=10., E_rest=-70., V_thresh=-50., V_peak=-50., N_pops=[80,20],
                  N_recVm=2, N_show=2)

with open('config_file.json', 'w') as fp:
    json.dump(parameters, fp)
sim_config = brainsimulation.SimulationConfiguration(name='config #%s in demo notebook'  % str(datetime.now),
                                                     description='parameter configuration of toy model#%s in demo notebook'  % str(datetime.now),
                                                     config_file='config_file.json')
sim_config.save(client)
print('The KG ID is:', sim_config.id)

## --> result

# for small files, we can store them directly on the knowledge graph
spike_result = brainsimulation.SimulationResult(name='spike results of toy model#%s in demo notebook'  % str(datetime.now),
                                                # generated_by = my_model,
                                                report_file='spike_long_run.npz',
                                                data_type = 'network activity data', 
                                                variable='spike',
                                                target='soma',
                                                description='Spiking results of toy model#%s run in demo notebook'  % str(datetime.now))
spike_result.save(client)
print('The KG ID is:', spike_result.id)


# for big files, need a specific storage (e.g. CSCS) and the url reference uses a Distribution object
# create the distribution:
vm_location = brainsimulation.Distribution('https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo/data/Vm_long_run.npz')
# associate to the SimulationResult object:
Vm_result = brainsimulation.SimulationResult(name='Vm results of toy model#%s in demo notebook' % str(datetime.now),
                                             # generated_by = my_model,
                                             data_type = 'network activity data', 
                                             report_file=vm_location, # Now a Distribution !
                                             variable='spike',
                                             target='soma',
                                             description='Intracelular data of toy model#%s run in demo notebook' % str(datetime.now) )
# now saving will be succesfull
Vm_result.save(client)
print('The KG ID is:', Vm_result.id)

## --> agent
# print(uniminds.list(client, api='query'))
# yann = uniminds.Person.by_name('Zerlaut, Yann', client)
yann = brainsimulation.Person(family_name='Zerlaut',
                              given_name='Yann',
                              email='yann.zerlaut@cnrs.fr')
#yann.save(client)
print('The KG ID is:', yann.id)


## --> activity
sim = brainsimulation.SimulationActivity(name='parameter configuration of toy model#%s in demo notebook'  % str(datetime.now),
                                         description='',
                                         configuration_used=sim_config,
                                         simulation_script=sc,
                                         model_instance=my_model,
                                         timestamp=datetime.now(),
                                         result = spike_result,
                                         # started_by = yann,
                                         ended_at_time=datetime.now())

sim.save(client)
print('The KG ID is:', sim.id)
