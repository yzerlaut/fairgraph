import os, time
from datetime import datetime

from fairgraph import brainsimulation, KGClient, minds

dev = True
if dev:
    client = KGClient(os.environ["HBP_token"],
                      nexus_endpoint='https://nexus-int.humanbrainproject.org/v0')
else:
    client = KGClient(os.environ["HBP_token"])
    
####################################################
### Downloading the (toy) Validation of the demo ###
####################################################

# The validation source code is available in a public container at CSCS
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


####################################################
### Documenting Validation Metadata ################
####################################################

## --> starting with script metadata underlying the validation
validation_script = brainsimulation.ValidationScript(name='Script for Toy model#%s of network dynamics for demo purpose' % str(datetime.now()),
                                                     code_format='python',
                                                     distribution=Distribution(container_url+'/model/model_script.py'),
                                                     date_created=datetime.now(),
                                                     license='CC BY-SA')
validation_script.save(client) # SAVE IN KG


validation_result = brainsimulation.ValidationResult(name='Result of Toy validation#%s' % str(datetime.now()),
                                                     score=1.,
                                                     normalized_score=0.5)
validation_result.save(client) # SAVE IN KG
print('The KG ID is:', validation_result.id)

####################################################
### Validating against an existing Dataset #########
####################################################

datasets = brainsimulation.Collection(name='Experimental dataset for validation',
                                      members=[minds.Dataset.list(client, size=1)[0]])
datasets.save(client)
print('The KG ID is:', datasets.id)



my_validation = brainsimulation.ValidationActivity(name= 'Toy validation#%s of neural network dynamics for demo purpose' % str(datetime.now()),
                                                   model_instance=my_model,
                                                   reference_data=datasets,
                                                   test_script=validation_script,
                                                   result=validation_result,
                                                   timestamp=datetime.now())
my_validation.save(client) # SAVE IN KG
print('The KG ID is:', my_validation.id)


