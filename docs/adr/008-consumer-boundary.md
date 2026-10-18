# Separate consuming agents from the reusable runtime

Status: accepted and implemented in 0.3.0.

The initial repository could demonstrate ports but not a real project consuming them. The existing Agent N stack already owns business authorization and data safety. Moving those concerns into a generic SDK would couple all agents to one business domain.

Decision: package shared execution, transport, configuration and service routes in the SDK; create an independent Agent N consumer package containing only its composition, tools, instructions and fixtures. Access existing APIs, not private implementation modules or database tables. Preserve existing backend/MCP/frontend.

Alternative: rewrite the existing backend or copy its MCP runtime into every new agent. Rejected because that duplicates infrastructure and risks changing mature authorization paths. A framework-specific base class was also rejected; a protocol-based runner can be called by any framework.

Consequences: two independently versioned repositories, explicit SDK dependency, contract-test seam at HTTP, and no public redistribution of inspected private source. Live backend/model certification remains a deployment gate.
