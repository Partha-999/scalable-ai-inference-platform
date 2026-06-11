class ModelArtifactsMissingError(Exception):
    """Exception raised when model weight or configuration files are missing in the local cache or unavailable offline."""
    pass
