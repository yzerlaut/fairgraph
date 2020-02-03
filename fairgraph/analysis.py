"""
analysis
"""

try:
    basestring
except NameError:
    basestring = str
import os.path
import logging
from datetime import datetime, date
import mimetypes
from itertools import chain
import sys
import inspect
from dateutil import parser as date_parser
import requests
from .base import KGObject, cache, KGProxy, build_kg_object, Distribution, as_list, KGQuery, Field, IRI
from .commons import BrainRegion, CellType, Species, AbstractionLevel, ModelScope, OntologyTerm
from . import core ## What's the way to work with "core" classes ? 
from .utility import compact_uri, standard_context

from . import brainsimulation
from .brainsimulation import ATTACHMENT_SIZE_LIMIT, upload_attachment, HasAliasMixin

logger = logging.getLogger("fairgraph")
mimetypes.init()

DEFAULT_NAMESPACE = "modelvalidation"
## What's the way to work with "core" classes ? Temporary fix:
core.use_namespace(DEFAULT_NAMESPACE)
Person = core.Person
Collection = core.Collection
Organization = core.Organization
Age = core.Age


class AnalysisActivity(KGObject):
    """  Here this is the Analysis *Activity*
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.0.1/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.0.1",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/activity/v0.1.4"
    ],
    "shapes": [
        {
            "@id": "this:AnalysisActivityShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/activity/v0.1.1/ActivityShape"
                },
                {
                    "property": [
                        {
                            "minCount": 2,
                            "path": "prov:used"
                        },
                        {
                            "class": "nsg:AnalysisResult",
                            "description": "Generated simulation result.",
                            "minCount": 1,
                            "name": "Result",
                            "path": "prov:generated",
                            "seeAlso": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1/shapes/AnalysisResultShape"
                        }
                    ]
                }
            ],
            "label": "Simulation report analysis shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisActivity"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisactivity/v0.0.1"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisactivity/v0.0.1"
    type = ["prov:Activity", "nsg:Activity", "nsg:AnalysisActivity"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "schema": "http://schema.org/",
            "name": "schema:name",
            "description": "schema:description",
            "prov": "http://www.w3.org/ns/prov#",
            "generated": "prov:generated",
            "used": "prov:used",
            "dataUsed": "prov:used",
            "scriptUsed": "prov:used",
            "configUsed": "prov:used",
            "startedAtTime": "prov:startedAtTime",
            "endedAtTime": "prov:endedAtTime",
            "wasAssociatedWith": "prov:wasAssociatedWith",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "referenceData": "nsg:referenceData"
        }
    ]
    fields = (
        Field("name", basestring, "name"),
        Field("description", basestring, "description"),
        Field("input_data", KGObject, "dataUsed", required=True),
        Field("analysis_script", "analysis.AnalysisScript", "scriptUsed", required=True),
        Field("configuration_used", "analysis.AnalysisConfiguration", "configUsed", required=True),
        Field("timestamp", datetime,  "startedAtTime", required=True),
        Field("end_timestamp",  datetime, "endedAtTime"),
        Field("result", "analysis.AnalysisResult", "generated", required=True, multiple=True),
        Field("started_by", Person, "wasAssociatedWith")
    )


class AnalysisConfiguration(KGObject):
    """
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.0.1/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.0.1",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:AnalysisConfigurationShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of config",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Analysis Configuration shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisConfiguration"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisconfiguration/v0.0.1"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/analysisconfiguration/v0.0.1"
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisConfiguration"]
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("config", (Distribution, dict, basestring), "distribution")
    )

    def __init__(self,
                 name,
                 config_file='',
                 description='',
                 json_description='',
                 id=None, instance=None):
        
        super(AnalysisConfiguration, self).__init__(
            name=name,
            config_file=config_file,
            description=description,
            json_description=json_description,
            id=id,
            instance=instance)
        self._file_to_upload = None
        if isinstance(config_file, basestring):
            if config_file.startswith("http"):
                self.config_file = Distribution(location=config_file)
            elif os.path.isfile(config_file):
                self._file_to_upload = config_file
                self.config_file = None
        elif config_file is not None:
            for rf in as_list(self.config_file):
                assert isinstance(rf, Distribution)

    def save(self, client):
        super(AnalysisConfiguration, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.config_file):
            rf.download(local_directory, client)
    

class AnalysisResult(KGObject):
    """
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:AnalysisResultShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of the analysis result",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Analysis Result shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:AnalysisResult"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/analysisresult/v0.0.1"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisResult"]
    _path = "/simulation/analysisresult/v0.0.1"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "variable": "nsg:variable",
               "dataType": "nsg:dataType",
               "prov": "http://www.w3.org/ns/prov#",
               "startedAtTime": "prov:startedAtTime",
               "wasGeneratedBy": "prov:wasGeneratedBy"}
    fields = (Field("name", basestring, "name", required=True),
              Field("variable", basestring, "variable"),
              Field("report_file", (Distribution, basestring), "distribution"),
              Field("generated_by", (AnalysisActivity, basestring), "wasGeneratedBy"),
              Field("data_type", basestring, "dataType"),
              Field("description", basestring, "description"),
              Field("timestamp", datetime,  "startedAtTime"))

    def __init__(self,
                 name,
                 generated_by='',
                 report_file=None,
                 data_type = '',
                 variable='',
                 description='',
                 timestamp=None,
                 id=None, instance=None):
        
        super(AnalysisResult, self).__init__(
            name=name,
            generated_by=generated_by,
            report_file=report_file,
            data_type=data_type,
            variable=variable,
            description=description,
            timestamp=timestamp,
            id=id,
            instance=instance)
        self._file_to_upload = None
        if isinstance(report_file, basestring):
            if report_file.startswith("http"):
                self.report_file = Distribution(location=report_file)
            elif os.path.isfile(report_file):
                self._file_to_upload = report_file
                self.report_file = None
        elif report_file is not None:
            for rf in as_list(self.report_file):
                assert isinstance(rf, Distribution)

    @property
    def _existence_query(self):
        return {
            "op": "and",
            "value": [
                {
                    "path": "schema:name",
                    "op": "eq",
                    "value": self.name
                }
            ]
        }

    def save(self, client):
        super(AnalysisResult, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.report_file):
            rf.download(local_directory, client)

            
class AnalysisScript(KGObject):
    """ NEED TO MAKE A DEDICATED shema"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/emodelscript/v0.1.0"
    type = ["prov:Entity", "nsg:EModelScript"]  # generalize to other sub-types of script
    context =  [  # todo: root should be set by client to nexus or nexus-int or whatever as required
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "license": "schema:license"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("code_format", basestring, "code_format"),
        Field("license", basestring, "license"),
        Field("distribution", Distribution,  "distribution")
    )

    def __init__(self, name, code_location=None, code_format=None, license=None,
                 distribution=None, id=None, instance=None):
        super(AnalysisScript, self).__init__(name=name, code_format=code_format, license=license,
                                          distribution=distribution, id=id, instance=instance)
        if code_location and distribution:
            raise ValueError("Cannot provide both code_location and distribution")
        if code_location:
            self.distribution = Distribution(location=code_location)

    @property
    def code_location(self):
        if self.distribution:
            return self.distribution.location
        else:
            return None




class Dataset(KGObject):
    """
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/dataset/v0.0.1/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/dataset/v0.0.1",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:DatasetShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of dataset",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Analysis Configuration shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:Dataset"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/dataset/v0.0.1"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/dataset/v0.0.1"
    type = ["prov:Entity", "nsg:Entity", "nsg:Dataset"]
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "contributor": "https://schema.hbp.eu/minds/contributors",
               "url":"https://schema.hbp.eu/minds/container_url",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("identifier", basestring, "http://schema.org/identifier"),
        Field("contributors", Person, "contributor", multiple=True),
        Field("container_url", basestring, "url", required=False, multiple=False)
    )

    def download(self, local_directory, accept_terms_of_use=False):
        # todo: add support for download as zip
        # todo: check hashes
        if not (accept_terms_of_use or self.accepted_terms_of_use):
            if in_notebook():
                from IPython.display import display, Markdown
                display(Markdown(terms_of_use))
            else:
                print(terms_of_use)
            user_response = raw_input("Do you accept the EBRAINS KG Terms of Service? ")
            if user_response in ('y', 'Y', 'yes', 'YES'):
                self.__class__.accepted_terms_of_use = True
            else:
                raise Exception("Please accept the terms of use before downloading the dataset")
        response = requests.get(self.container_url + "?format=json")
        if response.status_code != 200:
            raise IOError(
                "Unable to download dataset. Response code {}".format(response.status_code))
        contents = response.json()
        total_data_size = sum(item["bytes"] for item in contents) // 1024
        progress_bar = tqdm(total=total_data_size)
        for entry in contents:
            local_path = os.path.join(local_directory, entry["name"])
            print(local_path)
            if entry["name"].endswith("/"):
                os.makedirs(local_path, exist_ok=True)
            else:
                response2 = requests.get(self.container_url + "/" + entry["name"])
                if response2.status_code == 200:
                    with open(local_path, "wb") as fp:
                        fp.write(response2.content)
                    progress_bar.update(entry["bytes"] // 1024)
                else:
                    raise IOError(
                        "Unable to download file '{}'. Response code {}".format(
                            local_path, response2.status_code))
        progress_bar.close()


        
def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
