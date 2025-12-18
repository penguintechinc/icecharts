"""
NodeData - Standard data transfer object for workflow nodes in IceStreams.

This module provides the core data structure for passing information between
workflow nodes, including payload data, metadata, source tracking, and timestamps.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass(slots=True)
class NodeData:
    """
    Standard data transfer object for workflow nodes in IceStreams.

    This dataclass represents a unit of data flowing through the workflow system,
    containing the actual payload, associated metadata, source tracking, and timing
    information.

    Attributes:
        data: The main data payload containing the actual information being processed.
        metadata: Additional metadata associated with the data (defaults to empty dict).
        source_node_id: ID of the source node that created or last modified this data.
        timestamp: UTC timestamp of when this NodeData was created.
    """

    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_node_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a detailed string representation of the NodeData."""
        return (
            f"NodeData(data={self.data}, metadata={self.metadata}, "
            f"source_node_id={self.source_node_id!r}, timestamp={self.timestamp})"
        )
