/**
 * Playbook Edge Components
 *
 * Custom edge components for the playbook workflow editor.
 * All edges are directional with animated data flow indicators.
 */

export { AnimatedFlowEdge, type AnimatedFlowEdgeData } from './AnimatedFlowEdge';

// Edge type registration for ReactFlow
import { AnimatedFlowEdge } from './AnimatedFlowEdge';

// Use 'any' to avoid type compatibility issues with ReactFlow EdgeTypes
export const playbookEdgeTypes: Record<string, React.ComponentType<any>> = {
  animatedFlow: AnimatedFlowEdge,
};
