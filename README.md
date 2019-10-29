# fairgraph: a Python API for the Human Brain Project Knowledge Graph.

Authors: Andrew Davison and Onur Ates, CNRS

Copyright CNRS 2019

**fairgraph** is an experimental Python library for working with metadata
in the HBP Knowledge Graph, with a particular focus on data reuse,
although it is also useful in metadata registration/curation.
The API is not stable, and is subject to change.

## Installation

```
git clone https://github.com/HumanBrainProject/pyxus.git pyxus_src
pip install -r pyxus_src/pyxus/requirements.txt
pip install pyxus_src/pyxus
git clone https://github.com/HumanBrainProject/fairgraph.git
pip install -U ./fairgraph
```

## Basic setup

The basic idea of the library is to represent data instances from the Knowledge Graph as Python objects.
Communication with the Knowledge Graph service is through a client object,
for which an access token associated with an HBP Identity account is needed.

If you are working in a Collaboratory Jupyter notebook:

```
from jupyter_collab_storage import oauth_token_handler
token = oauth_token_handler.get_token()
```

If working outside the Collaboratory, we recommend you obtain a token from https://nexus-iam.humanbrainproject.org/v0/oauth2/authorize
and save it as an environment variable, e.g. at a shell prompt:

```
export HBP_token=eyJhbGci...nPq
```

and then in Python

```
token = os.environ['HBP_token']
```

Once you have a token:

```
from fairgraph import KGClient

client = KGClient(token)
```

## Retrieving metadata from the Knowledge Graph

The different metadata/data types available in the Knowledge Graph are grouped into modules,
currently `commons`, `core`, `brainsimulation`, `electrophysiology` and `minds`.
For example:

```
from fairgraph.commons import BrainRegion
from fairgraph.electrophysiology import PatchedCell
```

Using these classes, it is possible to list all metadata matching a particular criterion, e.g.

```
cells_in_ca1 = PatchedCell.list(client, brain_region=BrainRegion("hippocampus CA1"))
```

If you know the unique identifier of an object, you can retrieve it directly:

```
cell_of_interest = PatchedCell.from_uuid("153ec151-b1ae-417b-96b5-4ce9950a3c56", client)
```

Links between metadata in the Knowledge Graph are not followed automatically,
to avoid unnecessary network traffic, but can be followed with the `resolve()` method:

```
example_cell = cells_in_ca1[3]
experiment = example_cell.experiments.resolve(client)
trace = experiment.traces.resolve(client)
```

The associated metadata is accessible as attributes of the Python objects, e.g.:

```
print(example_cell.cell_type)
print(example_cell.reversal_potential_cl)
print(trace.time_step)
print(trace.data_unit)
```

You can also access any associated data:

```
import requests
import numpy as np
from io import BytesIO

download_url = trace.data_location['downloadURL']
data = np.genfromtxt(BytesIO(requests.get(download_url).content))
```

## Advanced queries

While certain filters and queries are built in (such as the filter by brain region, above),
more complex queries are possible using the [Nexus query API](https://bbp-nexus.epfl.ch/staging/docs/kg/api-reference/operating-on-resources.html#search-and-filtering)

```
from fairgraph.base import KGQuery
from fairgraph.minds import Dataset

query = {
    "path": "minds:specimen_group / minds:subjects / minds:samples / minds:methods / schema:name",
    "op": "in",
    "value": ["Electrophysiology recording",
              "Voltage clamp recording",
              "Single electrode recording",
              "functional magnetic resonance imaging"]
}
context = {
            "schema": "http://schema.org/",
            "minds": "https://schema.hbp.eu/minds/"
}

activity_datasets = KGQuery(Dataset, query, context).resolve(client)
for dataset in activity_datasets:
    print("* " + dataset.name)
```

## Storing and editing metadata

For those users who have the necessary permissions to store and edit metadata in the Knowledge Graph,
**fairgraph* objects can be created or edited in Python, and then saved back to the Knowledge Graph, e.g.:

```
import os, hashlib
from fairgraph import KGClient
from fairgraph.uniminds import ModelInstance, Organization, Person, License, AbstractionLevel, BrainStructure, CellularTarget, ModelFormat, ModelScope

HBP_token = os.environ["HBP_token"] # pass whatever bash variable stores your 
client = KGClient(HBP_token)

# adding an organization
full_name = 'Human Brain Project Research Centre' 
person1 = Organization(name=full_name,
					   identifier = hashlib.sha1(full_name.encode('utf-8')).hexdigest(),
					   family_name='Dupont', given_name ='Jean') 

# adding people
full_name = 'Dupont, Jean' 
JDupont = Person(name=full_name,
				 identifier = hashlib.sha1(full_name.encode('utf-8')).hexdigest(),
				 email='jean.dupont@hbp.eu',
				 family_name='Dupont', given_name ='Jean') 
full_name = 'Smith, John'
JSmith = Person(name=full_name,
				 identifier = hashlib.sha1(full_name.encode('utf-8')).hexdigest(),
				 email='john.smith@hbp.eu',
				 family_name='Smith', given_name ='John')
for person in [JDupont, JSmith]:
	person.save(client)


# -------------------------------------------------------
# **  Release a new Model entry to the Knowledge Graph **
# -------------------------------------------------------

name, version ='Test by John Smith', 'v1' 

# -- we first fetch a few existing metadata from the Knowledge graph that describe this new entry
CCBY40 = License.from_uuid("8462091d-45a0-4e57-a9cc-869a667d8702", client, api='query')
Population_Modeling = AbstractionLevel.from_uuid("e527c7f2-2cff-4727-826f-7e3cc1dbdde3", client, api='query')
Cerebral_Cortex = BrainStructure.from_uuid("7e397000-243c-4773-9cbe-00167dfc384d", client, api='query')
Interneurons = CellularTarget.from_uuid("c601c757-da45-49f7-bd20-8ceec61a16a1", client, api='query')
PyNN = ModelFormat.from_uuid("25579512-ade4-4ddf-b039-7d10e275da26", client, api='query')
Network = ModelScope.from_uuid("d773866c-e790-45ef-b354-147176b44cdb", client, api='query')

# then we write the new ModelInstance using those metadata
minst = ModelInstance(name=name,
					  description='Test of a Model Release using Faigraph by John Smith ',
					  identifier = hashlib.sha1((name + version).encode('utf-8')).hexdigest(),
					  custodian=JSmith,
					  main_contact = JSmith,
					  author=[JDupont, JSmith],
					  abstraction_level=Population_Modeling,
					  brain_structure=Cerebral_Cortex,
					  cellular_target=Interneurons,
					  modelformat=PyNN,
					  modelscope=Network,
					  license=CCBY40,
					  version=version)
minst.save(client)
```

Other examples of the use of fairgraph to read and write can be found in the documentation of the [model curation](https://github.com/yzerlaut/model-curation) pipeline, at: https://github.com/yzerlaut/model-curation/blob/master/docs/use_of_fairgraph.org

## Getting help

In case of questions about **fairgraph**, please e-mail support@humanbrainproject.eu.
If you find a bug or would like to suggest an enhancement or new feature,
please open a ticket in the [issue tracker](https://github.com/HumanBrainProject/fairgraph/issues).

## Acknowledgements

<div><img src="https://www.braincouncil.eu/wp-content/uploads/2018/11/wsi-imageoptim-EU-Logo.jpg" alt="EU Logo" height="23%" width="15%" align="right" style="margin-left: 10px"></div>

This open source software code was developed in part or in whole in the Human Brain Project, funded from the European Union's Horizon 2020 Framework Programme for Research and Innovation under Specific Grant Agreements No. 720270 and No. 785907 (Human Brain Project SGA1 and SGA2).
