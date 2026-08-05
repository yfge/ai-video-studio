class ConsistencyError(ValueError):
    """Raised when a generic consistency contract fails closed."""


class SchemaError(ConsistencyError):
    """Raised for invalid schema references or executable rules."""


class GraphError(ConsistencyError):
    """Raised for invalid facts, events, evidence, or transitions."""
