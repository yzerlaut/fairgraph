"""

###############################################
### Building a dataset object with faigraph ###
###############################################

"""
import os, time
from datetime import datetime

from fairgraph import uniminds, KGClient

token = os.environ['HBP_token']
client = KGClient(token)


# The data are available in a public container at CSCS
container_url = 'https://object.cscs.ch/v1/AUTH_c0a333ecf7c045809321ce9d9ecdfdea/faigraph_demo'

cortex = uniminds.BrainStructure.by_name('cerebral cortex', client, api='nexus')
cell = uniminds.CellularTarget.by_name('L2/3 pyramidal cell', client, api='nexus')

yann = uniminds.Person.by_name('Zerlaut, Yann', client)
glynis = uniminds.Person.by_name('Mattheisen, Glynis', client)
andrew = uniminds.Person.by_name('Davison, Andrew', client)

ccb40 = uniminds.License.list(client, api='query')[0]

## CREATING THE FILE BUNDLE
fb = uniminds.FileBundle(name='filebundle for the demo dataset for fairgraph',
                         url=container_url)

## CREATING THE DATASET
dataset = uniminds.Dataset(
    name='Set of intracellular recordings for fairgraph-demo',
    description="""
    This is the demo dataset for fairgraph
    
    """,
    brain_structure = cortex,
    cellular_target = cell,
    main_file_bundle = fb,
    contributor = (yann, glynis, andrew),
    main_contact = andrew,
    hbp_component = uniminds.HBPComponent.by_name('SGA2', client),
    custodian = yann) # ETC...

# dataset.save(client) # DOESN'T WORK YET
