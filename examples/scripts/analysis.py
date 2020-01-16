import os, time
from datetime import datetime

from fairgraph import brainsimulation, KGClient, base, uniminds
from fairgraph.analysis import AnalysisActivity, AnalysisScript, AnalysisConfiguration, AnalysisResult, Person
# needs to have HBP_AUTH_TOKEN set as a bash variable
dev = True
if dev:
    client = KGClient(os.environ["HBP_AUTH_TOKEN"],
                      nexus_endpoint='https://nexus-int.humanbrainproject.org/v0')
else:
    client = KGClient(os.environ["HBP_AUTH_TOKEN"])


###############################################
### Downloading the (toy) Model of the demo ###
###############################################

# The model source code is available in a public container at CSCS
container_url = 'https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo'
if not os.path.isfile('model_script.py'):
    os.system('wget https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/simulation_result_demo/model/model_script.py')

###############################################
### Documenting Analysis Metadata ################
###############################################

## --> starting with script metadata underlying the model
analysis_script = AnalysisScript(name='Script for Toy analysis#%s of network dynamics for demo purpose' % str(datetime.now),
                                 code_format='python',
                                 distribution=base.Distribution(container_url+'/model/model_script.py'),
                                 date_created=datetime.now(),
                                 license='CC BY-SA')
analysis_script.save(client) # SAVE IN KG
print('The KG ID is:', analysis_script.id)


## --> parameters/configuration
from types import SimpleNamespace
args = SimpleNamespace(dt=1e-4, tstop=1., seed=0,
                       freq=10., E_rest=-70., V_thresh=-50., V_peak=-50., N_pops=[80,20],
                       N_recVm=2, N_show=2)

analysis_config = AnalysisConfiguration(name='parameter configuration of toy analysis#%s in demo notebook'  % str(datetime.now))
analysis_config.save(client)
print('The KG ID is:', analysis_config.id)

## --> result

# for small files, we can store them directly on the knowledge graph
analysis_result = AnalysisResult(name='spike results of toy analysis#%s in demo notebook'  % str(datetime.now),
                                                report_file='spike_long_run.npz',
                                                data_type = 'network activity data', 
                                                variable='spike',
                                                description='Spiking results of toy analysis#%s run in demo notebook'  % str(datetime.now))
analysis_result.save(client)
print('The KG ID is:', analysis_result.id)


## --> agent
yann = Person(family_name='Zerlaut',
              given_name='Yann',
              email='yann.zerlaut@cnrs.fr')
yann.save(client)
print('The KG ID is:', yann.id)


## --> activity
sim = AnalysisActivity(name='parameter configuration of toy analysis#%s in demo notebook'  % str(datetime.now),
                                         description='',
                                         configuration_used=analysis_config,
                                         analysis_script=analysis_script,
                                         timestamp=datetime.now(),
                                         result = analysis_result,
                                         started_by = yann,
                                         ended_at_time=datetime.now())

#sim.save(client)
print('The KG ID is:', sim.id)

