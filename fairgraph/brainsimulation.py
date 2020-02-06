"""
brain simulation
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
# from .core import Organization, Person, Age, Collection
from .utility import compact_uri, standard_context


logger = logging.getLogger("fairgraph")
mimetypes.init()

DEFAULT_NAMESPACE = "modelvalidation"

## What's the way to work with "core" classes ? Temporary fix:
core.use_namespace(DEFAULT_NAMESPACE)
Person = core.Person
Collection = core.Collection
Organization = core.Organization
Age = core.Age

ATTACHMENT_SIZE_LIMIT = 1024 * 1024  # 1 MB

# An upload function used by all Results entity classes
def upload_attachment(cls, file_path, client):
    assert os.path.isfile(file_path)
    statinfo = os.stat(file_path)
    if statinfo.st_size > ATTACHMENT_SIZE_LIMIT:
        raise Exception("File is too large to store directly in the KnowledgeGraph, please upload it to a Swift container")
    # todo, use the Nexus HTTP client directly for the following
    headers = client._nexus_client._http_client.auth_client.get_headers()
    content_type, encoding = mimetypes.guess_type(file_path, strict=False)
    response = requests.put("{}/attachment?rev={}".format(cls.id, cls.rev or 1),
                            headers=headers,
                            files={
                                "file": (os.path.basename(file_path),
                                         open(file_path, "rb"),
                                         content_type)
                            })
    if response.status_code < 300:
        logger.info("Added attachment {} to {}".format(file_path, cls.id))
        cls._file_to_upload = None
        cls.report_file = Distribution.from_jsonld(response.json()["distribution"][0])
    else:
        raise Exception(str(response.content))

class HasAliasMixin(object):

    @classmethod
    def from_alias(cls, alias, client):
        context = {
            "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"
        }
        query = {
            "path": "nsg:alias",
            "op": "eq",
            "value": alias
        }
        return KGQuery(cls, query, context).resolve(client)


class ModelProject(KGObject, HasAliasMixin):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/modelproject/v0.1.0"
    #path = DEFAULT_NAMESPACE + "/simulation/modelproject/v0.1.1"
    type = ["prov:Entity", "nsg:ModelProject"]
    context = {
        "name": "schema:name",
        "label": "rdfs:label",
        "alias": "nsg:alias",
        "author": "schema:author",
        "owner": "nsg:owner",
        "organization": "nsg:organization",
        "PLAComponents": "nsg:PLAComponents",
        "private": "nsg:private",
        "collabID": "nsg:collabID",
        "brainRegion": "nsg:brainRegion",
        "species": "nsg:species",
        "celltype": "nsg:celltype",
        "abstractionLevel": "nsg:abstractionLevel",
        "modelOf": "nsg:modelOf",
        "description": "schema:description",
        "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
        "prov": "http://www.w3.org/ns/prov#",
        "schema": "http://schema.org/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "dateCreated": "schema:dateCreated",
        "dcterms": "http://purl.org/dc/terms/",
        "instances": "dcterms:hasPart",
        "oldUUID": "nsg:providerId",
        "partOf": "nsg:partOf",
        "hasPart": "dcterms:hasPart"
    }
    attribute_map = {
        "model_of": (ModelScope, context["modelOf"]),
        "brain_region": (BrainRegion, context["brainRegion"]),
        "species": (Species, context["species"]),
        "celltype": (CellType, context["celltype"]),
        "abstraction_level": (AbstractionLevel, context["abstractionLevel"]),
    }
    # should be able to replace `attribute_map` by extending `fields`
    fields = (
        Field("name", basestring, "name", required=True),
        Field("owners", Person, "owner", required=True, multiple=True),
        Field("authors", Person, "author", required=True, multiple=True),
        Field("description", basestring, "description", required=True),
        Field("date_created", datetime, "dateCreated", required=True),
        Field("private", bool, "private", required=True),
        Field("collab_id", int, "collabID"),
        Field("alias", basestring, "alias"),
        Field("organization", Organization, "organization", multiple=True),
        Field("pla_components", basestring, "PLAComponents", multiple=True),
        Field("brain_region", BrainRegion, "brainRegion", multiple=True),
        Field("species", Species, "species"),
        Field("celltype", CellType, "celltype"),
        Field("abstraction_level", AbstractionLevel, "abstractionLevel"),
        Field("model_of", ModelScope, "modelOf"),
        Field("old_uuid", basestring, "oldUUID"),
        Field("parents", "ModelProject", "partOf", multiple=True),
        #Field("instances", ("ModelInstance", "brainsimulation.MEModel"),
        #      "dcterms:hasPart", multiple=True),
        # todo: kg query returns "hasPart", while nexus instances mostly use "dcterms:hasPart"
        #       suggest changing all instances to store "hasPart", with corrected context if needed
        Field("instances", ("brainsimulation.ModelInstance", "brainsimulation.MEModel"),
              "hasPart", multiple=True),
        Field("images", dict, "images", multiple=True)  # type should be Distribution?
    )

    def __init__(self, name, owners, authors, description, date_created, private, collab_id=None,
                 alias=None, organization=None, pla_components=None, brain_region=None,
                 species=None, celltype=None, abstraction_level=None, model_of=None,
                 old_uuid=None, parents=None, instances=None, images=None,
                 id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)

    @property
    def _existence_query(self):
        # allow multiple projects with the same name
        return {
            "op": "and",
            "value": [
                {
                    "path": "schema:name",
                    "op": "eq",
                    "value": self.name
                },
                {
                    "path": "schema:dateCreated",
                    "op": "eq",
                    "value": self.date_created.isoformat()
                }
            ]
        }

    @classmethod
    def list(cls, client, size=100, api='nexus', scope="released", resolved=False, **filters):
        """List all objects of this type in the Knowledge Graph"""
        if api == 'nexus':
            context = {
            'nsg': 'https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/'
            }
            filter_queries = []
            for name, value in filters.items():
                if name in cls.attribute_map:
                    concept_class, concept_uri = cls.attribute_map[name]
                    filter_queries.append({
                        'path': concept_uri,
                        'op': 'eq',
                        'value': concept_class(value).iri
                    })
                elif name in ("author", "owner"):
                    if not isinstance(value, Person):
                        raise TypeError("{} must be a Person object".format(name))
                    filter_queries.append({
                        "path": cls.context[name],
                        "op": "eq",
                        "value": value.id
                    })
                else:
                    raise Exception("The only supported filters are by '{supported_filters}'. "
                                    "You specified '{name}'".format(
                                        supported_filters="', '".join(chain(cls.attribute_map, ["author", "owner"])),
                                        name=name))
            if len(filter_queries) == 0:
                return client.list(cls, size=size)
            elif len(filter_queries) == 1:
                filter_query = filter_queries[0]
            else:
                filter_query = {
                    "op": "and",
                    "value": filter_queries
                }
            return KGQuery(cls, filter_query, context).resolve(client, size=size)
            # todo: handle resolved=True for nexus queries (i.e. do all the downstream resolutions  )
        else:
            # todo: handle author, owner
            filter_queries = {}
            for name, value in filters.items():
                if name in cls.attribute_map:
                    concept_class, concept_uri = cls.attribute_map[name]
                    filter_queries[name] = concept_class.iri_map[value]
                else:
                    filter_queries[name] = value
            return client.list(cls, size=size, api=api, scope=scope, filter=filter_queries, resolved=resolved)


    def authors_str(self, client):
        return ", ".join("{obj.given_name} {obj.family_name}".format(obj=obj.resolve(client))
                         for obj in self.authors)

    #def sub_projects(self):


class ModelInstance(KGObject):
    """docstring"""
    #path = DEFAULT_NAMESPACE + "/simulation/modelinstance/v0.1.2"
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/modelinstance/v0.1.1"
    type = ["prov:Entity", "nsg:ModelInstance"]
    # ScientificModelInstance
    #   - model -> linked ModelProject using partOf
    #   - version -> add field to ModelInstance.
    #   - description -> part of Entity
    #   - parameters -> linked ModelParameters
    #   - source -> (e.g. git repository) -> linked ModelScript
    #   - timestamp -> prov:generatedAtTime
    #   - code_format -> linked ModelScript
    #   - hash - general feature, don't put in schema
    #   - morphology - not needed for all models, use MEModel where we have a morphology
    # modelinstance/v0.1.2
    #   - fields of Entity + modelOf, brainRegion, species
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {"oldUUID": "nsg:providerId"}
    ]
    # fields:
    #  - fields of ModelInstance + eModel, morphology, mainModelScript, isPartOf (an MEModelRelease)
    fields = (
        Field("name", basestring, "name", required=True),
        # Field("author", Person, "person", required=False),
        Field("brain_region", BrainRegion, "brainRegion", required=False),
        Field("species", Species, "species", required=False),
        Field("model_of", (CellType, BrainRegion), "modelOf", required=False),  # should be True, but causes problems for a couple of cases at the moment
        Field("main_script", "brainsimulation.ModelScript", "mainModelScript"),
        Field("release", basestring, "release", required=False),
        Field("version",  basestring, "version", required=True),
        Field("timestamp", datetime, "generatedAtTime", required=False),
        Field("part_of", KGObject, "isPartOf"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("old_uuid", basestring, "oldUUID")
    )

    def __init__(self, name, main_script=None, version='', timestamp=None,
                 brain_region=None, species=None, model_of=None, release=None,
                 part_of=None, description=None, parameters=None,
                 old_uuid=None, id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)

    @property
    def project(self):
        query = {
            "path": "dcterms:hasPart",
            "op": "eq",
            "value": self.id
        }
        context = {
            "dcterms": "http://purl.org/dc/terms/"
        }
        return KGQuery(ModelProject, query, context)


class MEModel(ModelInstance):
    """docstring"""
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/memodel/v0.1.2"  # latest is 0.1.4, but all the data is currently under 0.1.2
    type = ["prov:Entity", "nsg:MEModel", "nsg:ModelInstance"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {"oldUUID": "nsg:providerId"}
    ]
    # fields:
    #  - fields of ModelInstance + eModel, morphology, mainModelScript, isPartOf (an MEModelRelease)
    fields = list(ModelInstance.fields) + [
        Field("morphology", "brainsimulation.Morphology", "morphology", required=True),
        Field("e_model",  "brainsimulation.EModel", "eModel", required=True),
        #Field("project", ModelProject, "isPartOf", required=True)  # conflicts with project property in parent class. To fix.
    ]

    def __init__(self, name, e_model, morphology, main_script, version, timestamp=None, #project,
                 brain_region=None, species=None, model_of=None,
                 release=None, part_of=None, description=None, parameters=None,
                 old_uuid=None, id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)


class Morphology(KGObject):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/morphology/v0.1.1"
    type = ["prov:Entity", "nsg:Morphology"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("cell_type", CellType, "modelOf"),
        Field("distribution", Distribution, "distribution")
    )

    def __init__(self, name, cell_type=None, morphology_file=None, distribution=None,
                 id=None, instance=None):
        super(Morphology, self).__init__(name=name, cell_type=cell_type,
                                         distribution=distribution, id=id, instance=instance)
        if morphology_file:
            if distribution:
                raise ValueError("Cannot provide both morphology_file and distribution")
            self.morphology_file = morphology_file

    @property
    def morphology_file(self):
        if isinstance(self.distribution, list):
            return [d.location for d in self.distribution]
        elif self.distribution is None:
            return None
        else:
            return self.distribution.location

    @morphology_file.setter
    def morphology_file(self, value):
        if isinstance(value, list):
            self.distribution = [Distribution(location=mf) for mf in value]
        else:
            self.distribution = Distribution(location=value)


class ModelScript(KGObject):
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
        super(ModelScript, self).__init__(name=name, code_format=code_format, license=license,
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


class EModel(ModelInstance):
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/emodel/v0.1.1"
    type = ["prov:Entity", "nsg:EModel"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0"
    ]
    fields = (
        Field("name", basestring, "name", required=True),
        Field("brain_region", BrainRegion, "brainRegion", required=False),
        Field("species", Species, "species", required=False),
        Field("model_of", (CellType, BrainRegion), "modelOf", required=False),
        Field("main_script", "brainsimulation.ModelScript", "mainModelScript", required=False),
        Field("release", basestring, "release", required=False),
        Field("version",  basestring, "version", required=False),
        Field("timestamp", datetime, "generatedAtTime", required=False),
        Field("part_of", KGObject, "isPartOf"),
        Field("description", basestring, "description"),
        Field("parameters", basestring, "parameters"),
        Field("old_uuid", basestring, "oldUUID")
    )

    def __init__(self, name, main_script=None, version=None, timestamp=None, #project,
                 brain_region=None, species=None, model_of=None,
                 release=None, part_of=None, description=None, parameters=None,
                 old_uuid=None, id=None, instance=None):
        args = locals()
        args.pop("self")
        KGObject.__init__(self, **args)

    

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
    _path = "/simulation/simulationactivity/v0.1.0"
    type = ["prov:Activity", "nsg:SimulationActivity"]
    context = [
        "{{base}}/contexts/neurosciencegraph/core/data/v0.3.1",
        "{{base}}/contexts/nexus/core/resource/v0.3.0",
        {
            "schema": "http://schema.org/",
            "name": "schema:name",
            "identifier": "schema:identifier",
            "description": "schema:description",
            "prov": "http://www.w3.org/ns/prov#",
            "generated": "prov:generated",
            "used": "prov:used",
            "dataUsed": "prov:used",
            "modelUsed": "prov:used",
            "simUsed": "prov:used",
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
        Field("identifier", basestring, "identifier"),
        Field("model_instance", (ModelInstance, MEModel), "modelUsed"),
        # Field("input_data", KGObject, "dataUsed", multiple=True), # A KIND OF INPUT DATA OBJECT, TO BE ADDED
        Field("script", "brainsimulation.SimulationScript", "scriptUsed", multiple=True),
        Field("config", "brainsimulation.SimulationConfiguration", "configUsed", multiple=True),
        Field("timestamp", datetime,  "startedAtTime"),
        Field("result", "brainsimulation.SimulationResult", "generated", multiple=True),
        Field("started_by", Person, "wasAssociatedWith"),
        Field("end_timestamp",  datetime, "endedAtTime")
    )
    

class SimulationConfiguration(KGObject):
    """
    """
    namespace = DEFAULT_NAMESPACE
    _path = "/simulation/simulationconfiguration/v0.1.0"
    type = ["prov:Entity", "nsg:Entity", "nsg:SimulationConfiguration"]
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "description": "schema:description",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("identifier", basestring, "identifier"),
        Field("description", basestring, "description"),
        Field("config_file", (Distribution, basestring), "distribution")
    )

    def __init__(self,
                 name,
                 config_file='',
                 description='',
                 id=None, instance=None):
        
        super(SimulationConfiguration, self).__init__(
            name=name,
            config_file=config_file,
            description=description,
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
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:SimulationResult"]
    _path = "/simulation/simulationresult/v0.1.0"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "identifier": "schema:identifier",
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
              Field("description", basestring, "description"),
              Field("identifier", basestring, "identifier"),
              Field("report_file", (Distribution, basestring), "distribution"),
              Field("generated_by", SimulationActivity, "wasGeneratedBy"),
              Field("derived_from", KGObject, "wasDerivedFrom", multiple=True),  # SHOULD BE SET UP  BY THE ACTIVITY
              Field("target", basestring, "target"),
              Field("data_type", basestring, "dataType"),
              Field("timestamp", datetime,  "startedAtTime"),
              Field("brain_region", BrainRegion, "brainRegion"),
              Field("species", Species, "species"),
              Field("celltype", CellType, "celltype"))

    def __init__(self,
                 name,
                 identifier=None,
                 report_file=None,
                 generated_by=None,
                 derived_from=None,
                 data_type = '',
                 variable='',
                 target='',
                 description='',
                 timestamp=None,
                 brain_region=None, species=None, celltype=None,
                 id=None, instance=None):
        
        super(SimulationResult, self).__init__(
            name=name,
            identifier=identifier,
            report_file=report_file,
            generated_by=generated_by,
            derived_from=derived_from,
            data_type=data_type,
            variable=variable,
            target=target,
            description=description,
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

class SimulationScript(KGObject):
    """
    """
    namespace = DEFAULT_NAMESPACE
    type = ["prov:Entity", "nsg:Entity", "nsg:SimulationScript"]
    _path = "/simulation/simulationscript/v0.1.0"
    context = {"schema": "http://schema.org/",
               "name": "schema:name",
               "identifier": "schema:identifier",
               "description": "schema:description",
               "license": "schema:license",
               "nsg": "https://bbp-nexus.epfl.ch/vocabs/bbp/neurosciencegraph/core/v0.1.0/",
               "distribution": "nsg:distribution",
               "code_format": "nsg:code_format"}
    fields = (
        Field("name", basestring, "name", required=True),
        Field("identifier", basestring, "identifier"),
        Field("script_file", (Distribution, basestring), "distribution", multiple=True),
        Field("code_format", basestring, "code_format", multiple=True),
        Field("license", basestring, "license")
    )

    def __init__(self, name,
                 script_file=None,
                 code_format=None,
                 license=None,
                 id=None,
                 instance=None):
        super(SimulationScript, self).__init__(name=name,
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
        super(SimulationScript, self).save(client)
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

def list_kg_classes():
    """List all KG classes defined in this module"""
    return [obj for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and issubclass(obj, KGObject) and obj.__module__ == __name__]


def use_namespace(namespace):
    """Set the namespace for all classes in this module."""
    for cls in list_kg_classes():
        cls.namespace = namespace
