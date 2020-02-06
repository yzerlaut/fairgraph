"""
validation
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


class ValidationTestDefinition(KGObject, HasAliasMixin):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationtestdefinition/v0.1.0"
    #path = DEFAULT_NAMESPACE + "/simulation/validationtestdefinition/v0.1.2"
    type = ["prov:Entity", "nsg:ValidationTestDefinition"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "alias": "nsg:alias",
            "author": "schema:author",
            "brainRegion": "nsg:brainRegion",
            "species": "nsg:species",
            "celltype": "nsg:celltype",
            "abstractionLevel": "nsg:abstractionLevel",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "testType": "nsg:testType",
            "referenceData": "nsg:referenceData",
            "dataType": "nsg:dataType",
            "recordingModality": "nsg:recordingModality",
            "status": "nsg:status",
            "scoreType": "nsg:scoreType",
            "oldUUID": "nsg:providerId"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("authors", Person, "author", multiple=True, required=True),
        Field("description", basestring, "description", required=False),
        Field("date_created", (date, datetime), "dateCreated", required=True),
        Field("alias", basestring, "alias"),
        Field("brain_region", BrainRegion, "brainRegion", multiple=True),
        Field("species", Species, "species"),
        Field("celltype", CellType, "celltype", multiple=True),
        Field("test_type", basestring, "testType"),
        Field("age", Age, "age"),
        Field("reference_data", KGObject, "referenceData"),
        Field("data_type", basestring, "dataType"),
        Field("recording_modality", basestring, "recordingModality"),
        Field("score_type", basestring, "scoreType"),
        Field("status", basestring, "status"),
        Field("old_uuid", basestring, "oldUUID")
    )

    @property
    def scripts(self):
        query = {
            "path": "nsg:implements",
            "op": "eq",
            "value": self.id
        }
        context = {
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"
        }
        return KGQuery(ValidationScript, query, context)


class ValidationScript(KGObject):  # or ValidationImplementation
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationscript/v0.1.0"
    type = ["prov:Entity", "nsg:ModelValidationScript"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "repository": "schema:codeRepository",
            "version": "schema:version",
            "parameters": "nsg:parameters",
            "path": "nsg:path",
            "implements": "nsg:implements",
            "oldUUID": "nsg:providerId"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("date_created", (date, datetime), "dateCreated", required=True),
        Field("repository", IRI, "repository"),
        Field("version", basestring, "version"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("test_definition", ValidationTestDefinition, "implements"),
        Field("old_uuid", basestring, "oldUUID")
    )


class ValidationResult(KGObject):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationresult/v0.1.0"
    #path = DEFAULT_NAMESPACE + "/simulation/validationresult/v0.1.1"
    type = ["prov:Entity", "nsg:ValidationResult"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "score": "nsg:score",
            "normalizedScore": "nsg:normalizedScore",
            "passed": "nsg:passedValidation",
            "wasGeneratedBy": "prov:wasGeneratedBy",
            "hadMember": "prov:hadMember",
            "collabID": "nsg:collabID",
            "oldUUID": "nsg:providerId",
            "hash": "nsg:digest"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("generated_by", "brainsimulation.ValidationActivity", "wasGeneratedBy"),
        Field("description", basestring, "description"),
        Field("score", (float, int), "score"),
        Field("normalized_score", (float, int), "normalizedScore"),
        Field("passed", bool, "passedValidation"),
        Field("timestamp", (date, datetime), "dateCreated"),
        Field("additional_data", KGObject, "hadMember", multiple=True),
        Field("old_uuid", basestring, "oldUUID"),
        Field("collab_id", (int, basestring), "collabID"),
        Field("hash", basestring, "hash")
    )


class ValidationActivity(KGObject):
    """
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/modelvalidation/v0.2.0"  # only present in nexus-int
    type = ["prov:Activity", "nsg:ModelValidation"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "generated": "prov:generated",
            "used": "prov:used",
            "modelUsed": "prov:used",
            "testUsed": "prov:used",
            "dataUsed": "prov:used",
            "startedAtTime": "prov:startedAtTime",
            "endedAtTime": "prov:endedAtTime",
            "wasAssociatedWith": "prov:wasAssociatedWith",
            "referenceData": "nsg:referenceData"
        }
    ]
    fields = (
        Field("name", basestring, "name"),
        Field("model_instance", (ModelInstance, MEModel), "modelUsed", required=True),
        Field("test_script", ValidationScript, "testUsed", required=True),
        Field("reference_data", Collection, "dataUsed", required=True),
        Field("timestamp", datetime,  "startedAtTime", required=True),
        Field("result", ValidationResult, "generated", required=True),
        Field("started_by", Person, "wasAssociatedWith"),
        Field("end_timestamp",  datetime, "endedAtTime")
    )

    @property
    def _existence_query(self):
        # to fix: need an _and_ on model_instance, test_script, reference_data and timestamp
        return {
            "path": "prov:startedAtTime",
            "op": "eq",
            "value": self.timestamp.isoformat()
        }

    @property
    def duration(self):
        if self.end_timestamp:
            return self.end_timestamp - self.start_timestamp
        else:
            return 0.0

    @classmethod
    @cache
    def from_kg_instance(cls, instance, client, resolved=False):
        D = instance.data
        if resolved:
            D = cls._fix_keys(D)
        for otype in cls.type:
            if otype not in D["@type"]:
                # todo: profile - move compaction outside loop?
                compacted_types = compact_uri(D["@type"], standard_context)
                if otype not in compacted_types:
                    print("Warning: type mismatch {} - {}".format(otype, compacted_types))
        def filter_by_kg_type(items, type_name):
            filtered_items = []
            for item in as_list(items):
                if type_name in item["@type"] or type_name in compact_uri(item["@type"], standard_context):
                    filtered_items.append(item)
            return filtered_items
        try:
            model_instance = filter_by_kg_type(D["modelUsed"], "nsg:ModelInstance")[0]
        except KeyError:
            model_instance = filter_by_kg_type(D["used"], "nsg:ModelInstance")[0]
        try:
            reference_data = filter_by_kg_type(D["dataUsed"], "nsg:Collection")[0]
        except KeyError:
            reference_data = filter_by_kg_type(D["used"], "nsg:Collection")[0]
        try:
            test_script = filter_by_kg_type(D["testUsed"], "nsg:ModelValidationScript")[0]
        except KeyError:
            test_script = filter_by_kg_type(D["used"], "nsg:ModelValidationScript")[0]
        end_timestamp = D.get("endedAtTime")
        if end_timestamp:
            end_timestamp = date_parser.parse(end_timestamp)
        obj = cls(model_instance=build_kg_object(None, model_instance),
                  test_script=build_kg_object(ValidationScript, test_script),
                  reference_data=build_kg_object(None, reference_data),
                  timestamp=date_parser.parse(D.get("startedAtTime")),
                  result=build_kg_object(ValidationResult, D.get("generated")),
                  started_by=build_kg_object(Person, D.get("wasAssociatedWith")),
                  end_timestamp=end_timestamp,
                  id=D["@id"],
                  instance=instance)
        return obj


class VariableReport(KGObject):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:VariableReportShape"]
    _path = "/simulation/variablereport/v0.1.0"
    context = {"name": "schema:name",
               "description": "schema:description",
               "variable": "nsg:variable",
               "target": "nsg:target",
               "schema": "http://schema.org/",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "prov": "http://www.w3.org/ns/prov#"}
    fields = (Field("name", str, "name", required=True),
              Field("description", str, "description", required=False),
              Field("variable", str,"variable", required=True),
              Field("target", str, "target", required=True),
              Field("report_file", (Distribution, basestring), "distribution"))

    def __init__(self, name,
                 variable='',
                 target='soma',
                 description='',
                 report_file=None,
                 id=None,
                 instance=None):
        super(VariableReport, self).__init__(
            name=name,
            variable=variable, target=target, description=description,
            report_file=report_file,
            id=id, instance=instance
        )
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
        super(VariableReport, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        assert os.path.isfile(file_path)
        statinfo = os.stat(file_path)
        if statinfo.st_size > ATTACHMENT_SIZE_LIMIT:
            raise Exception("File is too large to store directly in the KnowledgeGraph, please upload it to a Swift container")
        # todo, use the Nexus HTTP client directly for the following
        headers = client._nexus_client._http_client.auth_client.get_headers()
        content_type, encoding = mimetypes.guess_type(file_path, strict=False)
        response = requests.put("{}/attachment?rev={}".format(self.id, self.rev or 1),
                                headers=headers,
                                files={
                                    "file": (os.path.basename(file_path),
                                             open(file_path, "rb"),
                                             content_type)
                                })
        if response.status_code < 300:
            logger.info("Added attachment {} to {}".format(file_path, self.id))
            self._file_to_upload = None
            self.report_file = Distribution.from_jsonld(response.json()["distribution"][0])
        else:
            raise Exception(str(response.content))

    def download(self, local_directory, client):
        for rf in as_list(self.report_file):
            rf.download(local_directory, client)


class SimulationActivity(KGObject):
    """
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/simulationactivity/v0.0.4"
    type = ["prov:Activity", "nsg:SimulationActivity"]
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
            "modelUsed": "prov:used",
            "simUsed": "prov:used",
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
        Field("model_instance", (ModelInstance, MEModel), "modelUsed", multiple=True),
        Field("simulation_script", "brainsimulation.SimulationScript", "simUsed", multiple=True),
        Field("configuration_used", "brainsimulation.SimulationConfiguration", "configUsed", multiple=True),
        Field("timestamp", datetime,  "startedAtTime", required=True),
        Field("result", "brainsimulation.SimulationResult", "generated", multiple=True),
        Field("started_by", Person, "wasAssociatedWith"),
        Field("end_timestamp",  datetime, "endedAtTime")
    )
    


class SimulationConfiguration(KGObject):
    """
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/simulationconfiguration/v0.0.2/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/simulationconfiguration/v0.0.2",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:SimulationConfigurationShape",
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
            "label": "Simulation Configuration shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:SimulationConfiguration"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/simulationconfiguration/v0.0.2"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:SimulationConfiguration"]
    _path = "/simulation/simulationconfiguration/v0.0.2"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("description", basestring, "description"),
        Field("config_file", (Distribution, basestring), "distribution"),
        Field("json_description", basestring, "json_description") 
    )

    def __init__(self,
                 name,
                 config_file='',
                 description='',
                 json_description='',
                 id=None, instance=None):
        
        super(SimulationConfiguration, self).__init__(
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
        super(SimulationConfiguration, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.config_file):
            rf.download(local_directory, client)
    
            
class SimulationResult(KGObject):
    """
    Schema (use the environment setting in Postman to replace {{base}} with the desired nexus endpoint) :
{
    "@context": [
        "{{base}}/contexts/neurosciencegraph/core/schema/v0.1.0",
        {
            "this": "{{base}}/schemas/modelvalidation/simulation/simulationresult/v0.0.4/shapes/"
        },
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ],
    "@id": "{{base}}/schemas/modelvalidation/simulation/simulationresult/v0.0.4",
    "@type": "nxv:Schema",
    "imports": [
        "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0"
    ],
    "shapes": [
        {
            "@id": "this:SimulationResultShape",
            "@type": "sh:NodeShape",
            "and": [
                {
                    "node": "{{base}}/schemas/neurosciencegraph/commons/entity/v0.1.0/shapes/EntityShape"
                },
                {
                    "property": [
                        {
                            "datatype": "xsd:string",
                            "description": "name of the simulation result",
                            "minCount": 1,
                            "name": "name",
                            "path": "schema:name"
                        }
                    ]
                }
            ],
            "label": "Simulation Result shape",
            "nodekind": "sh:BlankNodeOrIRI",
            "targetClass": "nsg:SimulationResult"
        }
    ],
    "links": {
        "@context": "{{base}}/contexts/nexus/core/links/v0.2.0",
        "self": "{{base}}/schemas/modelvalidation/simulation/simulationresult/v0.0.4"
    }
}
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:SimulationResult"]
    _path = "/simulation/simulationresult/v0.0.4"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "variable": "nsg:variable",
               "target": "nsg:target",
               "brainRegion": "nsg:brainRegion",
               "species": "nsg:species",
               "celltype": "nsg:celltype",
               "dataType": "nsg:dataType",
               "prov": "http://www.w3.org/ns/prov#",
               "startedAtTime": "prov:startedAtTime",
               "wasGeneratedBy": "prov:wasGeneratedBy"}
    fields = (Field("name", basestring, "name", required=True),
              Field("variable", basestring, "variable"),
              Field("target", basestring, "target"),
              Field("report_file", (Distribution, basestring), "distribution"),
              Field("generated_by", (ModelInstance, basestring), "wasGeneratedBy"),
              Field("data_type", basestring, "dataType"),
              Field("description", basestring, "description"),
              Field("parameters", basestring, "parameters"),
              Field("timestamp", datetime,  "startedAtTime"),
              Field("brain_region", BrainRegion, "brainRegion"),
              Field("species", Species, "species"),
              Field("celltype", CellType, "celltype"))

    def __init__(self,
                 name,
                 generated_by='',
                 report_file=None,
                 data_type = '',
                 variable='',
                 target='',
                 description='',
                 timestamp=None,
                 brain_region=None, species=None, celltype=None,
                 parameters=None,
                 id=None, instance=None):
        
        super(SimulationResult, self).__init__(
            name=name,
            generated_by=generated_by,
            report_file=report_file,
            data_type=data_type,
            variable=variable,
            target=target,
            description=description,
            parameters=parameters,
            timestamp=timestamp,
            brain_region=brain_region,
            species=species,
            celltype=celltype,
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
        super(SimulationResult, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.report_file):
            rf.download(local_directory, client)

class AnalysisScript(KGObject):
    """
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:AnalysisScript"]
    _path = "/simulation/analysisscript/v0.1.0"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "license": "schema:license",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "distribution": "nsg:distribution",
               "code_format": "nsg:code_format"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("script_file", (Distribution, basestring), "distribution"),
        Field("code_format", basestring, "code_format", multiple=True),
        Field("license", basestring, "license"),
        Field("distribution", Distribution,  "distribution")
    )

    def __init__(self, name,
                 script_file=None,
                 code_format=None,
                 license=None,
                 id=None,
                 instance=None):
        super(AnalysisScript, self).__init__(name=name,
                                             script_file=script_file,
                                             code_format=code_format,
                                             license=license,
                                             id=id,
                                             instance=instance)
        self._file_to_upload = None
        if isinstance(script_file, basestring):
            if script_file.startswith("http"):
                self.script_file = Distribution(location=script_file)
            elif os.path.isfile(script_file):
                self._file_to_upload = script_file
                self.script_file = None
        elif script_file is not None:
            for rf in as_list(self.script_file):
                assert isinstance(rf, Distribution)
        else:
            print('/!\ Need to provide a "script_file" argument, either a string path to a file (local or public on the web) or a Distribution object')

    def save(self, client):
        super(AnalysisScript, self).save(client)
        if self._file_to_upload:
            self.upload_attachment(self._file_to_upload, client)
            
    @property
    def script_location(self):
        if self.distribution:
            return self.distribution.location
        else:
            print('script attached to the KG entry, use the "download" method to fetch it')
            return None

    def upload_attachment(self, file_path, client):
        upload_attachment(self, file_path, client)
        
    def download(self, local_directory, client):
        for rf in as_list(self.script_file):
            rf.download(local_directory, client)


class ValidationScript(KGObject):  # or ValidationImplementation
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/validationscript/v0.1.0"
    type = ["prov:Entity", "nsg:ModelValidationScript"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "name": "schema:name",
            "description": "schema:description",
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
            "prov": "http://www.w3.org/ns/prov#",
            "schema": "http://schema.org/",
            "dateCreated": "schema:dateCreated",
            "repository": "schema:codeRepository",
            "version": "schema:version",
            "parameters": "nsg:parameters",
            "path": "nsg:path",
            "implements": "nsg:implements",
            "oldUUID": "nsg:providerId"
        }
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("date_created", (date, datetime), "dateCreated", required=True),
        Field("repository", IRI, "repository"),
        Field("version", basestring, "version"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("test_definition", ValidationTestDefinition, "implements"),
        Field("old_uuid", basestring, "oldUUID")
    )
            
            
def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
