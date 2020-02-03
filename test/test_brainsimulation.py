# encoding: utf-8
"""
Tests of fairgraph.brainsimulation module, using a mock Http client
which returns data loaded from the files in the test_data directory.
"""

from pyxus.resources.entity import Instance

from fairgraph.base import KGQuery, KGProxy, as_list, Distribution, KGObject
from fairgraph.commons import BrainRegion, CellType, QuantitativeValue
from fairgraph.brainsimulation import (
    ModelScript, ModelProject, ModelInstance, MEModel, Morphology, EModel, AnalysisResult,
    ValidationTestDefinition, ValidationScript, ValidationResult, ValidationActivity
)
from fairgraph.core import use_namespace as use_core_namespace

from .utils import (kg_client, MockKGObject, test_data_lookup, generate_random_object,
                    BaseTestKG, random_uuid)

use_core_namespace("modelvalidation")


test_data_lookup.update({
    "/v0/data/modelvalidation/simulation/modelproject/v0.1.0/": "test/test_data/nexus/brainsimulation/modelproject_list_0_10.json",
    "/query/modelvalidation/simulation/modelproject/v0.1.0/fgResolved/instances": "test/test_data/kgquery/brainsimulation/modelproject_list_resolved_0_10.json",
})


class TestModelScript(BaseTestKG):
    class_under_test = ModelScript

    def test_get_context(self, kg_client):
        obj = ModelScript("test_code",
                          code_location="https://github.com/SomeOrg/ProjName",
                          code_format="Python", license="BSD",
                          id="http://fake_uuid_381aa74bc9")
        context = sorted(obj.get_context(kg_client),
                         key=lambda obj: str(obj))
        expected_context = sorted([
            'https://nexus.humanbrainproject.org/v0/contexts/nexus/core/resource/v0.3.0',
            'https://nexus.humanbrainproject.org/v0/contexts/neurosciencegraph/core/data/v0.3.1',
            {'license': 'schema:license'}
        ], key=lambda obj: str(obj))
        assert context == expected_context


class TestModelProject(BaseTestKG):
    class_under_test = ModelProject

    def test_list(self, kg_client):
        models = ModelProject.list(kg_client, size=10)
        assert len(models) == 10

    def test_list_kgquery(self, kg_client):
        models = ModelProject.list(kg_client, api="query", scope="inferred", size=10, resolved=True)
        assert len(models) == 10

    def test_list_with_filter(self, kg_client):
        models = ModelProject.list(kg_client, size=10, species="Rattus norvegicus")
        assert len(models) == 5

    def test_list_kgquery_with_filter(self, kg_client):
        models = ModelProject.list(kg_client, api="query", scope="inferred", size=10, resolved=True, species="Rattus norvegicus")
        assert len(models) == 2


class TestModelInstance(BaseTestKG):
    class_under_test = ModelInstance


class TestMEModel(BaseTestKG):
    class_under_test = MEModel


class TestMorphology(BaseTestKG):
    class_under_test = Morphology

    def test_round_trip_with_morphology_file(self, kg_client):
        cls = self.class_under_test
        obj1 = cls("test_morph", morphology_file="http://example.com/test.asc")
        instance = Instance(cls.path, obj1._build_data(kg_client), Instance.path)
        instance.data["@id"] = random_uuid()
        instance.data["@type"] = cls.type
        obj2 = cls.from_kg_instance(instance, kg_client)
        for field in cls.fields:
            if field.intrinsic:
                val1 = getattr(obj1, field.name)
                val2 = getattr(obj2, field.name)
                if issubclass(field.types[0], KGObject):
                    assert isinstance(val1, MockKGObject)
                    assert isinstance(val2, KGProxy)
                    assert val1.type == val2.cls.type
                else:
                    assert val1 == val2
        assert obj1.morphology_file == obj2.morphology_file


class TestEModel(BaseTestKG):
    class_under_test = EModel


class TestAnalysisResult(BaseTestKG):
    class_under_test = AnalysisResult


class TestValidationTestDefinition(BaseTestKG):
    class_under_test = ValidationTestDefinition


class TestValidationScript(BaseTestKG):
    class_under_test = ValidationScript


class TestValidationResult(BaseTestKG):
    class_under_test = ValidationResult


class TestValidationActivity(BaseTestKG):
    class_under_test = ValidationActivity