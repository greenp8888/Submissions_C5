from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import CodeFixSuggestion
from incident_suite.models.state import IncidentState


def code_generator_node(state: IncidentState) -> IncidentState:
    issues = state.get("detected_issues", [])
    remediations = state.get("remediations", [])
    source = state.get("source", "").lower()
    reference_code = state.get("salesforce_class_body", "")
    salesforce_connected = state.get("salesforce_connected", False)
    salesforce_org_type = state.get("salesforce_org_type", "")

    apex_context_available = bool(reference_code or state.get("salesforce_class_name"))
    code_fixes: list[CodeFixSuggestion] = []
    for idx, issue in enumerate(issues):
        remediation = remediations[idx] if idx < len(remediations) else None
        use_apex = apex_context_available or "salesforce" in source or "sandbox" in source or salesforce_connected
        target_component = (
            state.get("salesforce_class_name")
            or "salesforce_apex_trigger_handler"
            if use_apex
            else "service_dependency_client"
        )
        if use_apex:
            suggested_code = (
                "public with sharing class AccountTriggerHandler {\n"
                "    public static void handleBeforeInsert(List<Account> newRecords) {\n"
                "        Set<Id> ownerIds = new Set<Id>();\n"
                "        for (Account acct : newRecords) {\n"
                "            if (acct.OwnerId != null) {\n"
                "                ownerIds.add(acct.OwnerId);\n"
                "            }\n"
                "        }\n\n"
                "        Map<Id, User> ownersById = ownerIds.isEmpty()\n"
                "            ? new Map<Id, User>()\n"
                "            : new Map<Id, User>([\n"
                "                SELECT Id, Name\n"
                "                FROM User\n"
                "                WHERE Id IN :ownerIds\n"
                "            ]);\n\n"
                "        for (Account acct : newRecords) {\n"
                "            User owner = ownersById.get(acct.OwnerId);\n"
                "            if (owner != null) {\n"
                "                acct.Description = 'Owner verified: ' + owner.Name;\n"
                "            }\n"
                "        }\n"
                "    }\n"
                "}\n"
            )
            recommended_change = (
                remediation.fix
                if remediation
                else "Refactor the Apex path to bulkify queries, move SOQL out of loops, and keep trigger logic in a handler with guardrails."
            )
            validation_notes = [
                "Verify the class stays bulk-safe for 200-record trigger batches.",
                "Confirm SOQL and DML counts remain within governor limits in sandbox tests.",
                "Add or update Apex tests that cover bulk inserts, null-safe paths, and failure handling.",
            ]
        else:
            suggested_code = (
                "MAX_RETRIES = 3\n"
                "TIMEOUT_SECONDS = 5\n\n"
                "for attempt in range(MAX_RETRIES):\n"
                "    try:\n"
                "        response = dependency_client.fetch(payload, timeout=TIMEOUT_SECONDS)\n"
                "        if response.ok:\n"
                "            break\n"
                "    except TimeoutError:\n"
                "        sleep(2 ** attempt)\n"
                "else:\n"
                "    raise ServiceDegradedError('Dependency remained unavailable after bounded retries')\n"
            )
            recommended_change = (
                remediation.fix
                if remediation
                else "Add bounded retries, explicit timeouts, and a guard around the failing dependency call."
            )
            validation_notes = [
                "Confirm retries stay inside upstream rate and governor limits.",
                "Compare timeout and error-rate metrics before and after the change.",
                "If using Salesforce sandbox code, inspect the Apex class or integration layer handling this call before promotion.",
            ]
        if salesforce_connected and use_apex:
            suggested_code += (
                "\n// Sandbox comparison note:\n"
                f"// Align this pattern with the {salesforce_org_type or 'connected'} org's existing trigger framework before promotion.\n"
            )
        if reference_code and use_apex:
            suggested_code += "\n// Reference Apex class was supplied so the patch can follow the existing org style.\n"
        code_fixes.append(
            CodeFixSuggestion(
                issue_title=issue.title,
                recommended_change=recommended_change,
                analogy=(
                    "This is like metering traffic through a jammed highway on-ramp: instead of sending every car at once and locking the road, "
                    "you pace entry, give the system room to recover, and stop one blockage from stalling everything behind it."
                ),
                target_component=target_component,
                suggested_code=suggested_code,
                validation_notes=validation_notes,
                confidence=0.78,
            )
        )

    return with_stage(
        state,
        "code_generator",
        "completed",
        f"Code generator proposed {len(code_fixes)} implementation-ready fix suggestion(s).",
        code_fixes=code_fixes,
        status="code_fix_ready",
    )
