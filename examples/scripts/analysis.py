import os, time, sys, hashlib
from datetime import datetime

from fairgraph import brainsimulation, KGClient, base, uniminds
from fairgraph.analysis import AnalysisActivity, AnalysisScript, AnalysisConfiguration, AnalysisResult, Person
# needs to have HBP_AUTH_TOKEN set as a bash variable
client = KGClient()

        
###############################################
### Downloading the dataset metadata ##########
###############################################
#data = uniminds.Dataset.by_name('Set of intracellular recordings for fairgraph-demo', client, api='query', scope='latest') # not working
data = uniminds.Dataset.list(client, api='nexus', resolve=True, scope='released', size=1)[0] # so picking an existing one


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
                                 script_file=base.Distribution(container_url+'/model/model_script.py'),
                                 license='CC BY-SA')

## --> parameters/configuration
import json
parameters = dict(dt=1e-4, tstop=1., seed=0,
                  freq=10., E_rest=-70., V_thresh=-50., V_peak=-50., N_pops=[80,20],
                  N_recVm=2, N_show=2)

with open('config_file.json', 'w') as fp:
    json.dump(parameters, fp)
# analysis_config = AnalysisConfiguration(name='parameter configuration of toy analysis#%s in demo notebook'  % str(datetime.now),
analysis_config = AnalysisConfiguration(name='parameter configuration of toy analysis in demo notebook',
                                        config_file='config_file.json')

## --> agentb
yann = Person(family_name='Zerlaut',
              given_name='Yann',
              email='yann.zerlaut@cnrs.fr')
yann.save(client)
print('The KG ID is:', yann.id)

## --> activity
name='parameter configuration of toy analysis#%s in demo notebook'  % str(datetime.now)
analysis = AnalysisActivity(name=name, identifier=hashlib.sha1("{}".format(name).encode('utf-8')).hexdigest(),
                            description='',
                            input_data=data,
                            configuration_used=analysis_config,
                            analysis_script=analysis_script,
                            timestamp=datetime.now(),
                            # result = analysis_result, # DOESN'T WORK
                            started_by = yann,
                            end_timestamp=datetime.now())

# for small files, we can store them directly on the knowledge graph
name = 'spike results of toy analysis#%s in demo notebook'  % str(datetime.now)
analysis_result = AnalysisResult(name=name, identifier=hashlib.sha1("{}".format(name).encode('utf-8')).hexdigest(),
                                 # generated_by=analysis,
                                 derived_from = data,
                                 report_file='spike_long_run.npz',
                                 data_type = 'network activity data', 
                                 variable='spike',
                                 description='Spiking results of toy analysis#%s run in demo notebook'  % str(datetime.now))

## --> result
for obj in [analysis_script, analysis_config, analysis_result, analysis]:
    obj.save(client) # need to save after the activity is built to have the procedure executed (setting provenance of results)
    print('The KG ID is:', obj.id)


# YOU CAN ADD PROVENANCE ONFO ONLY AFTER HAVING SAVED THE INSTANCES FIRST
analysis.result = analysis_result
# analysis_result.generated_by = analysis # DOESN'T WORK
#
analysis.save(client)

