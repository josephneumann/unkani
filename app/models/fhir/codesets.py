from datetime import datetime
import json, hashlib
from app.utils.general import json_serial
from requests import request
from requests.exceptions import RequestException
from app import db
from app.models.extensions import BaseExtension
from app.models.source_data import SourceData
from sqlalchemy.dialects import postgresql
from app.main.errors import ValidationError
from fhirclient.models import valueset, codesystem
from fhirclient.models.fhirabstractbase import FHIRValidationError

##################################################################################################
# SOURCE_DATA -> CODESYSTEM ASSOCIATION TABLE
##################################################################################################

source_data_codesystem = db.Table('source_data_codesystem',
                                  db.Column('source_data_id', db.Integer, db.ForeignKey('source_data.id'),
                                            primary_key=True),
                                  db.Column('codesystem_id', db.Integer, db.ForeignKey('codesystem.id'),
                                            primary_key=True))


class CodeSystem(db.Model):
    """Code systems define which codes (symbols and/or expressions) exist, and how they are understood.
    The CodeSystem resource is used to declare the existence of a code system, and its key properties:

    1) Identifying URL and version
    2) Description, Copyright, publication date, and other metadata
    3) Some key properties of the code system itself - whether it's case sensitive, version safe, and whether it defines a
        compositional grammar
    4) What filters can be used in value sets that use the code system in a ValueSet.compose element
    5) What properties the concepts defined by the code system

    In addition, the CodeSystem resource may list some or all of the concepts in the code system, along with their
    basic properties (code, display, definition), designations, and additional properties."""
    __tablename__ = 'codesystem'
    __mapper_args__ = {
        'extension': BaseExtension(),
    }

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Text, nullable=False, unique=True)
    version = db.Column(db.Text)
    url = db.Column(db.Text)
    data = db.Column(postgresql.JSONB)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)
    data_hash = db.Column(db.Text, index=True)

    source_data = db.relationship('SourceData', secondary=source_data_codesystem)

    def __repr__(self):  # pragma: no cover
        return '<CodeSystem {}:{}>'.format(self.id, self.resource_id)

    def __init__(self, data=None, data_hash=None):
        if data:
            self.data = data
            self.data_hash = data_hash
            self.set_attributes_from_fhir()

    def set_attributes_from_fhir(self):
        """Method used to set pre-defined table attrbutes with the corresponding data from the FHIR resource
        contained within self.data and self.fhir.  Used to initialize new objects, or update existing objects."""
        self.resource_id = self.fhir.id
        self.version = self.fhir.version
        self.url = self.fhir.url

    def update_from_fhir(self, data):
        """

        :param data:
            type: JSONB
            A JSON CodeSystem resource to be used when updating the CodeSystem SQLAlchemy object
        :return:
            None - sets object attributes only
        """
        self._fhir = self.get_fhir_obj(data=data)
        self.set_attributes_from_fhir()

    def get_fhir_obj(self, data=None):
        """
        Method to initialize a fhirclient derived FHIR data model from the SQLAlchemy CodeSet model's self.data
        attribute, which contains a valid JSON FHIR CodeSystem resource.
        :param data:
            A JSON FHIR CodeSystem resource
            Defaults to self.data if not defined, which is the most common use-case

        :return:
            If a fhirclient FHIR data model can be constructed, it is returned (fhirclient.models.codesystem.Codesystem
            If a fhirclient FHIR data model cannot be constructed, returns None
        """
        if not data:
            data = self.data
        try:
            return codesystem.CodeSystem(data)
        except FHIRValidationError:
            return None

    @property
    def fhir(self):
        """
        Accesses existing fhir model object, or initializes new fhir object and returns it
        :return:
            The fhirclient.model.codesystem.CodeSystem object associated with the object
        """
        if not hasattr(self, '_fhir'):
            self._fhir = self.get_fhir_obj()
        return self._fhir

    @fhir.setter
    def fhir(self, value):
        raise AttributeError('Property fhir is read-only.')

    @property
    def resource_type(self):
        return self.fhir.resource_type

    @property
    def description(self):
        return self.fhir.description

    @property
    def publisher(self):
        return self.fhir.publisher

    @property
    def status(self):
        return self.fhir.status

    @property
    def date(self):
        return self.fhir.date.date

    @property
    def experimental(self):
        return self.fhir.experimental

    @staticmethod
    def unpack_concept(concept):
        if not isinstance(concept, codesystem.CodeSystemConcept):
            raise TypeError('Did not supply a FHIR CodeSystemConcept object.')
        code = concept.code
        nested_concepts = []
        try:
            if concept.concept:
                nested_concepts = concept.concept
        except AttributeError:
            pass

        return code, nested_concepts

    @property
    def code_set(self):
        codes = set()
        concepts = self.fhir.concept

        while concepts:
            additional_concepts = []
            for concept in concepts:
                code, nested_concepts = self.unpack_concept(concept)
                codes.add(code)
                if nested_concepts:
                    additional_concepts.extend(nested_concepts)
            concepts = additional_concepts

        return codes

    def get_concept(self, code):
        concepts = self.fhir.concept
        found_concept = None

        while not found_concept and concepts:
            nested_concepts = []
            for concept in concepts:
                if concept.code == code:
                    found_concept = concept
                else:
                    try:
                        if concept.concept:
                            nested_concepts.extend(concept.concept)
                    except AttributeError:
                        pass
            concepts = nested_concepts

        return found_concept

    def dump_fhir_json(self):
        return self.data  # same as self.fhir.as_json()

    def before_insert(self):
        json_data = json.dumps(self.data, default=json_serial, sort_keys=True)
        self.data_hash = hashlib.sha1(json_data.encode('utf-8')).hexdigest()

    def before_update(self):
        json_data = json.dumps(self.data, default=json_serial, sort_keys=True)
        self.data_hash = hashlib.sha1(json_data.encode('utf-8')).hexdigest()


##################################################################################################
# SOURCE_DATA -> VALUESET ASSOCIATION TABLE
##################################################################################################

source_data_valueset = db.Table('source_data_valueset',
                                db.Column('source_data_id', db.Integer, db.ForeignKey('source_data.id'),
                                          primary_key=True),
                                db.Column('valueset_id', db.Integer, db.ForeignKey('valueset.id'),
                                          primary_key=True))


##################################################################################################
# VALUESET MODEL
##################################################################################################

class ValueSet(db.Model):
    """ValueSet data"""
    __tablename__ = 'valueset'
    __mapper_args__ = {
        'extension': BaseExtension(),
    }

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Text, nullable=False, unique=True)
    version = db.Column(db.Text)
    url = db.Column(db.Text)
    data = db.Column(postgresql.JSONB)
    data_hash = db.Column(db.Text, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime)

    source_data = db.relationship('SourceData', secondary=source_data_valueset)

    def __init__(self, data=None, data_hash=None):
        if data:
            self.data = data
            self.data_hash = data_hash
            self.set_attributes_from_fhir()

    def set_attributes_from_fhir(self):
        self.resource_id = self.fhir.id
        self.version = self.fhir.version
        self.url = self.fhir.url

    def update_from_fhir(self, data):
        self._fhir = self.get_fhir_obj(data=data)
        self.set_attributes_from_fhir()

    def __repr__(self):  # pragma: no cover
        return '<ValueSet {}:{}>'.format(self.id, self.resource_id)

    def get_fhir_obj(self, data=None):
        if not data:
            data = self.data
        try:
            return valueset.ValueSet(data)
        except FHIRValidationError:
            return None

    @property
    def fhir(self):
        if not hasattr(self, '_fhir'):
            self._fhir = self.get_fhir_obj()
        return self._fhir

    @fhir.setter
    def fhir(self, value):
        raise AttributeError('Property fhir is read-only.')

    @property
    def codesystem_dependencies(self):
        include = self.fhir.compose.include
        dependencies = []
        for x in include:
            if hasattr(x, 'system'):
                dependencies.append(x.system)
        return dependencies

    @property
    def resource_type(self):
        return self.fhir.resource_type

    @property
    def description(self):
        return self.fhir.description

    @property
    def publisher(self):
        return self.fhir.publisher

    @property
    def status(self):
        return self.fhir.status

    @property
    def date(self):
        return self.fhir.date.date

    @property
    def experimental(self):
        return self.fhir.experimental

    @property
    def code_set(self):
        code_set = set()
        for inc in self.fhir.compose.include:
            if hasattr(inc, 'system') and inc.system:
                if hasattr(inc, 'concept') and inc.concept:
                    for x in inc.concept:
                        code_set.add(x.code)
                else:
                    cs = CodeSystem.query.filter(CodeSystem.url == inc.system).first()
                    if cs:
                        code_set = code_set | cs.code_set
            if hasattr(inc, 'valueset') and inc.valueset:
                code_set = code_set | inc.valueset.code_set
        return code_set

    def dump_fhir_json(self):
        return self.data  # same as self.fhir.as_json()

    def before_insert(self):
        json_data = json.dumps(self.data, default=json_serial, sort_keys=True)
        self.data_hash = hashlib.sha1(json_data.encode('utf-8')).hexdigest()

    def before_update(self):
        json_data = json.dumps(self.data, default=json_serial, sort_keys=True)
        self.data_hash = hashlib.sha1(json_data.encode('utf-8')).hexdigest()


###########################################################
# HELPER FUNCTIONS TO RETRIEVE & PROCESS FHIR RESOURCES   #
###########################################################

def get_fhir_codeset(url):
    """
    Accepts a url of a FHIR ValueSet or CodeSystem resource
    Processes the the raw data into source_data and registers the appropriate route

    :param url: The url of the FHIR ValueSet or CodeSystem resource
    :return:
    Raises requests.exceptions.RequestException or child exception if request timeout, connection error or
    status code error.

    Returns None if data already exists and was processed through SourceData

    If new
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    try:
        response = request("GET", url, headers=headers)
        # response.raise_for_status()
        data_dict = response.json()
        resource_type = data_dict.get('resourceType')
    except RequestException:
        return None

    if not resource_type or resource_type not in ['CodeSystem', 'ValueSet']:
        raise TypeError('Fetched resource was not a FHIR resource type of CodeSystem or ValueSet')

    try:
        sd = SourceData(route='/{}'.format(resource_type.lower().strip()), payload=response.text, method='POST')
        db.session.add(sd)
        db.session.commit()
        return sd
    except ValidationError:
        db.session.rollback()
        return None


def process_fhir_codeset(source_data):
    """Accepts a source_data row as it's only parameter.  If the source_data row is valid, unpacks
    the source data payload into either a ValueSet or CodeSystem object.  Updates existing objects
    in place if they have been modified.  If ValueSet has a CodeSystem dependency that is not met,
    recursively calls this function to satisfy requirement and create CodeSystem object."""
    if source_data and isinstance(source_data, SourceData) and source_data.route in ['/codesystem', '/valueset']:
        # TODO: Error handling in this function
        # TODO: Process any codesets in source_data that do not have association object entries
        data = json.loads(source_data.payload)
        url = data.get('url')
        if source_data.route == '/codesystem':
            obj = CodeSystem.query.filter(CodeSystem.url == url).first()
            if not obj:
                obj = CodeSystem(data=data)
                source_data.status_code = 201
            else:
                obj.update_from_fhir(data)
                source_data.status_code = 200

            obj.source_data = [source_data]
            source_data.response = {}
            db.session.add(source_data)
            db.session.add(obj)
            db.session.commit()

        elif source_data.route == '/valueset':
            obj = ValueSet.query.filter(ValueSet.url == url).first()
            if not obj:
                obj = ValueSet(data=data)
                source_data.status_code = 201
            else:
                obj.update_from_fhir(data)
                source_data.status_code = 200

            obj.source_data = [source_data]
            source_data.response = {}
            db.session.add(source_data)
            db.session.add(obj)
            db.session.commit()

            if obj.codesystem_dependencies:
                for url in obj.codesystem_dependencies:
                    if not CodeSystem.query.filter(CodeSystem.url == url).first():
                        sd = get_fhir_codeset(url=url)
                        if sd:
                            process_fhir_codeset(source_data=sd)
