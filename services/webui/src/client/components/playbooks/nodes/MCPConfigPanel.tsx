/**
 * MCPConfigPanel - Configuration panel for MCP Server and Client nodes
 *
 * Features:
 * - MCP Server (Trigger): Configure server name, port, and tool definitions
 * - MCP Client (Action): Configure server URL, tool name, and argument mapping
 *
 * Uses ice-navy theme colors with Tailwind CSS
 */

import React, { useState } from 'react';

/**
 * MCP Server Configuration Interface
 * Used when the node type is "MCP Server" (trigger)
 */
export interface MCPServerConfig {
  serverName: string;
  port: number;
  tools: Array<{
    name: string;
    description: string;
    inputSchema: Record<string, any>;
  }>;
}

/**
 * MCP Client Configuration Interface
 * Used when the node type is "MCP Client" (action)
 */
export interface MCPClientConfig {
  serverUrl: string;
  toolName: string;
  argumentsMapping: Record<string, string>; // Maps input data paths to tool arguments
}

interface MCPConfigPanelProps {
  nodeType: 'MCP Server' | 'MCP Client';
  config: MCPServerConfig | MCPClientConfig;
  onChange: (config: MCPServerConfig | MCPClientConfig) => void;
}

/**
 * MCPConfigPanel Component
 *
 * Renders different configuration forms based on the node type:
 * - MCP Server: Server configuration with tool definitions
 * - MCP Client: Client configuration with argument mapping
 */
export const MCPConfigPanel: React.FC<MCPConfigPanelProps> = ({
  nodeType,
  config,
  onChange,
}) => {
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set());

  const toggleToolExpansion = (index: number) => {
    const newExpanded = new Set(expandedTools);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedTools(newExpanded);
  };

  /**
   * Render MCP Server configuration form
   */
  const renderServerConfig = () => {
    const serverConfig = config as MCPServerConfig;

    const updateServerName = (serverName: string) => {
      onChange({ ...serverConfig, serverName });
    };

    const updatePort = (port: number) => {
      onChange({ ...serverConfig, port });
    };

    const addTool = () => {
      const newTool = {
        name: '',
        description: '',
        inputSchema: {},
      };
      onChange({
        ...serverConfig,
        tools: [...serverConfig.tools, newTool],
      });
      // Expand the newly added tool
      setExpandedTools(new Set([...expandedTools, serverConfig.tools.length]));
    };

    const removeTool = (index: number) => {
      const newTools = serverConfig.tools.filter((_, i) => i !== index);
      onChange({ ...serverConfig, tools: newTools });
      // Remove from expanded set if it was expanded
      const newExpanded = new Set(expandedTools);
      newExpanded.delete(index);
      setExpandedTools(newExpanded);
    };

    const updateTool = (index: number, field: keyof typeof serverConfig.tools[0], value: any) => {
      const newTools = [...serverConfig.tools];
      newTools[index] = { ...newTools[index], [field]: value };
      onChange({ ...serverConfig, tools: newTools });
    };

    const updateInputSchema = (index: number, schemaJson: string) => {
      try {
        const schema = JSON.parse(schemaJson);
        updateTool(index, 'inputSchema', schema);
      } catch (e) {
        // Invalid JSON - don't update
      }
    };

    return (
      <div className="space-y-4">
        {/* Server Name */}
        <div>
          <label className="block text-ice-navy-300 text-sm font-medium mb-2">
            Server Name
          </label>
          <input
            type="text"
            value={serverConfig.serverName}
            onChange={(e) => updateServerName(e.target.value)}
            placeholder="my-mcp-server"
            className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 focus:border-ice-gold-500/50 transition-colors"
          />
          <p className="mt-1 text-xs text-ice-navy-400">
            Unique name for this MCP server instance
          </p>
        </div>

        {/* Port */}
        <div>
          <label className="block text-ice-navy-300 text-sm font-medium mb-2">
            Port
          </label>
          <input
            type="number"
            value={serverConfig.port}
            onChange={(e) => updatePort(parseInt(e.target.value) || 0)}
            placeholder="8080"
            min="1"
            max="65535"
            className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 focus:border-ice-gold-500/50 transition-colors"
          />
          <p className="mt-1 text-xs text-ice-navy-400">
            Port number for the MCP server (1-65535)
          </p>
        </div>

        {/* Tools List */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-ice-navy-300 text-sm font-medium">
              Tool Definitions
            </label>
            <button
              onClick={addTool}
              className="flex items-center gap-1 px-3 py-1 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 text-xs font-medium rounded-lg transition-colors"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Tool
            </button>
          </div>

          {serverConfig.tools.length === 0 ? (
            <div className="p-4 bg-ice-navy-700/50 border border-ice-navy-600 rounded-lg text-center">
              <p className="text-ice-navy-400 text-sm">No tools defined yet</p>
              <p className="text-ice-navy-500 text-xs mt-1">Click "Add Tool" to create your first tool</p>
            </div>
          ) : (
            <div className="space-y-2">
              {serverConfig.tools.map((tool, index) => (
                <div
                  key={index}
                  className="bg-ice-navy-700 border border-ice-navy-600 rounded-lg overflow-hidden"
                >
                  {/* Tool Header */}
                  <div className="flex items-center gap-2 p-3">
                    <button
                      onClick={() => toggleToolExpansion(index)}
                      className="p-1 hover:bg-ice-navy-600 rounded transition-colors"
                    >
                      <svg
                        className={`w-4 h-4 text-ice-navy-300 transition-transform duration-200 ${
                          expandedTools.has(index) ? 'rotate-90' : ''
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                    <div className="flex-1">
                      <input
                        type="text"
                        value={tool.name}
                        onChange={(e) => updateTool(index, 'name', e.target.value)}
                        placeholder="tool_name"
                        className="w-full px-2 py-1 bg-ice-navy-800 border border-ice-navy-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-ice-gold-500/50"
                      />
                    </div>
                    <button
                      onClick={() => removeTool(index)}
                      className="p-1 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>

                  {/* Tool Details (Expandable) */}
                  {expandedTools.has(index) && (
                    <div className="px-3 pb-3 space-y-3 border-t border-ice-navy-600">
                      {/* Description */}
                      <div className="pt-3">
                        <label className="block text-ice-navy-400 text-xs font-medium mb-1">
                          Description
                        </label>
                        <textarea
                          value={tool.description}
                          onChange={(e) => updateTool(index, 'description', e.target.value)}
                          placeholder="What this tool does..."
                          rows={2}
                          className="w-full px-2 py-1 bg-ice-navy-800 border border-ice-navy-600 rounded text-white text-sm resize-none focus:outline-none focus:ring-1 focus:ring-ice-gold-500/50"
                        />
                      </div>

                      {/* Input Schema */}
                      <div>
                        <label className="block text-ice-navy-400 text-xs font-medium mb-1">
                          Input Schema (JSON)
                        </label>
                        <textarea
                          value={JSON.stringify(tool.inputSchema, null, 2)}
                          onChange={(e) => updateInputSchema(index, e.target.value)}
                          placeholder='{"type": "object", "properties": {...}}'
                          rows={4}
                          className="w-full px-2 py-1 bg-ice-navy-800 border border-ice-navy-600 rounded text-white text-xs font-mono resize-none focus:outline-none focus:ring-1 focus:ring-ice-gold-500/50"
                        />
                        <p className="mt-1 text-xs text-ice-navy-500">
                          JSON Schema defining the tool's input parameters
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  /**
   * Render MCP Client configuration form
   */
  const renderClientConfig = () => {
    const clientConfig = config as MCPClientConfig;

    const updateServerUrl = (serverUrl: string) => {
      onChange({ ...clientConfig, serverUrl });
    };

    const updateToolName = (toolName: string) => {
      onChange({ ...clientConfig, toolName });
    };

    const addArgumentMapping = () => {
      const newMapping = { ...clientConfig.argumentsMapping, '': '' };
      onChange({ ...clientConfig, argumentsMapping: newMapping });
    };

    const removeArgumentMapping = (key: string) => {
      const newMapping = { ...clientConfig.argumentsMapping };
      delete newMapping[key];
      onChange({ ...clientConfig, argumentsMapping: newMapping });
    };

    const updateArgumentMapping = (oldKey: string, newKey: string, value: string) => {
      const newMapping = { ...clientConfig.argumentsMapping };
      if (oldKey !== newKey) {
        delete newMapping[oldKey];
      }
      newMapping[newKey] = value;
      onChange({ ...clientConfig, argumentsMapping: newMapping });
    };

    return (
      <div className="space-y-4">
        {/* Server URL */}
        <div>
          <label className="block text-ice-navy-300 text-sm font-medium mb-2">
            Server URL
          </label>
          <input
            type="text"
            value={clientConfig.serverUrl}
            onChange={(e) => updateServerUrl(e.target.value)}
            placeholder="http://localhost:8080"
            className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 focus:border-ice-gold-500/50 transition-colors"
          />
          <p className="mt-1 text-xs text-ice-navy-400">
            URL of the MCP server to connect to
          </p>
        </div>

        {/* Tool Name */}
        <div>
          <label className="block text-ice-navy-300 text-sm font-medium mb-2">
            Tool Name
          </label>
          <input
            type="text"
            value={clientConfig.toolName}
            onChange={(e) => updateToolName(e.target.value)}
            placeholder="tool_name"
            className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 focus:border-ice-gold-500/50 transition-colors"
          />
          <p className="mt-1 text-xs text-ice-navy-400">
            Name of the tool to call on the MCP server
          </p>
        </div>

        {/* Arguments Mapping */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-ice-navy-300 text-sm font-medium">
              Arguments Mapping
            </label>
            <button
              onClick={addArgumentMapping}
              className="flex items-center gap-1 px-3 py-1 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 text-xs font-medium rounded-lg transition-colors"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Mapping
            </button>
          </div>

          <p className="text-xs text-ice-navy-400 mb-3">
            Map input data paths to tool arguments (e.g., <code className="px-1 py-0.5 bg-ice-navy-700 rounded">$.user.name</code> → <code className="px-1 py-0.5 bg-ice-navy-700 rounded">userName</code>)
          </p>

          {Object.keys(clientConfig.argumentsMapping).length === 0 ? (
            <div className="p-4 bg-ice-navy-700/50 border border-ice-navy-600 rounded-lg text-center">
              <p className="text-ice-navy-400 text-sm">No argument mappings defined</p>
              <p className="text-ice-navy-500 text-xs mt-1">Click "Add Mapping" to create a mapping</p>
            </div>
          ) : (
            <div className="space-y-2">
              {Object.entries(clientConfig.argumentsMapping).map(([key, value], index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg"
                >
                  {/* Input Path */}
                  <div className="flex-1">
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => updateArgumentMapping(key, key, e.target.value)}
                      placeholder="$.data.path"
                      className="w-full px-2 py-1 bg-ice-navy-800 border border-ice-navy-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-ice-gold-500/50"
                    />
                  </div>

                  {/* Arrow */}
                  <svg className="w-4 h-4 text-ice-navy-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>

                  {/* Argument Name */}
                  <div className="flex-1">
                    <input
                      type="text"
                      value={key}
                      onChange={(e) => updateArgumentMapping(key, e.target.value, value)}
                      placeholder="argumentName"
                      className="w-full px-2 py-1 bg-ice-navy-800 border border-ice-navy-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-ice-gold-500/50"
                    />
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => removeArgumentMapping(key)}
                    className="p-1 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Help Text */}
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-xs text-blue-300">
              <p className="font-medium mb-1">JSONPath Syntax</p>
              <p className="text-blue-400">
                Use JSONPath notation to reference input data:
                <code className="block mt-1 px-2 py-1 bg-ice-navy-800 rounded">$.user.id</code>
                <code className="block mt-1 px-2 py-1 bg-ice-navy-800 rounded">$.items[0].name</code>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-4 bg-ice-navy-800">
      {/* Header */}
      <div className="mb-4 pb-3 border-b border-ice-navy-700">
        <h3 className="text-sm font-semibold text-ice-navy-200 uppercase tracking-wider flex items-center gap-2">
          {nodeType === 'MCP Server' ? (
            <>
              <span className="text-lg">🔌</span>
              MCP Server Configuration
            </>
          ) : (
            <>
              <span className="text-lg">📡</span>
              MCP Client Configuration
            </>
          )}
        </h3>
        <p className="mt-1 text-xs text-ice-navy-400">
          {nodeType === 'MCP Server'
            ? 'Configure your MCP server to receive tool calls'
            : 'Configure connection to an MCP server and call its tools'}
        </p>
      </div>

      {/* Configuration Form */}
      {nodeType === 'MCP Server' ? renderServerConfig() : renderClientConfig()}
    </div>
  );
};

export default MCPConfigPanel;
