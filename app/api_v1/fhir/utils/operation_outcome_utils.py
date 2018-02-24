from fhirclient.models.codeableconcept import CodeableConcept
from fhirclient.models.narrative import Narrative
from fhirclient.models.operationoutcome import OperationOutcome, OperationOutcomeIssue
from flask import render_template
from app.models.fhir.codesets import ValueSet


def create_operation_outcome(outcome_list):
    """
    Helper function to construct and OperationOutcome object from the appropriate data structure

    :param outcome_list:
    An array of dicts containing the keys necessary to generate an OperationOutcome FHIR STU 3.0 object

        outcome_list = [{'severity': None, 'type': None, 'location': [], 'diagnostics': None, 'expression': None,
                'details': None}]
        # Severity and Type are REQUIRED

    :return:
    A FHIR-Client OperationOutcome Object
    """
    oo = OperationOutcome()

    narrative = Narrative()
    narrative.status = 'additional'
    narrative.div = render_template('fhir/operation_outcome.html', outcome_list=outcome_list)
    oo.text = narrative

    severity_codes = ValueSet.query.filter(ValueSet.resource_id == 'issue-severity').first().code_set
    type_codes = ValueSet.query.filter(ValueSet.resource_id == 'issue-type').first().code_set

    for x in outcome_list:
        issue_severity = None
        issue_type = None
        issue_location = []
        issue_diagnostics = None
        issue_expression = None
        issue_details = None
        if 'severity' in x.keys():
            issue_severity = x.get('severity').lower().strip()
            if issue_severity not in severity_codes:
                issue_severity = None

        if 'type' in x.keys():
            issue_type = x.get('type').lower().strip()
            if issue_type not in type_codes:
                issue_type = None

        if 'details' in x.keys():
            details = x.get('details')
            if details:
                details_cc = CodeableConcept()
                details_cc.text = details
                issue_details = details_cc
            pass

        if 'diagnostics' in x.keys():
            diagnostics = x.get('diagnostics')
            if diagnostics:
                issue_diagnostics = diagnostics

        if 'location' in x.keys():
            location = x.get('location')
            if location:
                if isinstance(location, list):
                    for i in location:
                        issue_location.append(i)
                elif isinstance(location, str):
                    issue_location.append(location)

        if 'expression' in x.keys():
            expression = x.get('expression')
            if expression:
                issue_expression = expression

        issue = OperationOutcomeIssue()
        if issue_severity:
            issue.severity = issue_severity
        if issue_type:
            issue.code = issue_type
        if issue_location:
            issue.location = issue_location
        if issue_diagnostics:
            issue.diagnostics = issue_diagnostics
        if issue_expression:
            issue.expression = issue_expression
        if issue_details:
            issue.details = issue_details

        try:
            oo.issue.append(issue)
        except AttributeError:
            oo.issue = [issue]

    return oo
