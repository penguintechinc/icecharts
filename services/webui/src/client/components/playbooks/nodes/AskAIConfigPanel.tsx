/**
 * AskAIConfigPanel - Configuration panel for Ask AI transform node
 *
 * Allows querying LLMs (Ollama, Claude, OpenAI) with configurable:
 * - Provider selection
 * - Model selection (with provider-specific suggestions)
 * - Prompt and system prompt
 * - Temperature and max tokens
 * - Input data mapping via JSONPath
 */

import React from 'react';

interface AskAIConfig {
  provider: 'ollama' | 'claude' | 'openai';
  model: string;
  prompt: string;
  systemPrompt?: string;
  temperature?: number;
  maxTokens?: number;
  inputMapping?: string; // JSONPath to extract from input data
}

interface Props {
  config: AskAIConfig;
  onChange: (config: AskAIConfig) => void;
}

// Provider-specific model suggestions
const MODEL_SUGGESTIONS = {
  ollama: ['llama2', 'mistral', 'codellama', 'mixtral'],
  claude: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
  openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
};

const AskAIConfigPanel: React.FC<Props> = ({ config, onChange }) => {
  const handleChange = <K extends keyof AskAIConfig>(
    key: K,
    value: AskAIConfig[K]
  ) => {
    onChange({ ...config, [key]: value });
  };

  const suggestedModels = MODEL_SUGGESTIONS[config.provider] || [];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 pb-3 border-b border-ice-navy-700">
        <span className="text-2xl">🤖</span>
        <h3 className="text-lg font-semibold text-white">Ask AI Configuration</h3>
      </div>

      {/* Provider Selection */}
      <div>
        <label className="block text-ice-navy-400 text-sm font-medium mb-2">
          LLM Provider
        </label>
        <select
          value={config.provider}
          onChange={(e) =>
            handleChange('provider', e.target.value as AskAIConfig['provider'])
          }
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 transition-all"
        >
          <option value="ollama">Ollama (Local)</option>
          <option value="claude">Anthropic Claude</option>
          <option value="openai">OpenAI</option>
        </select>
        <p className="mt-1 text-xs text-ice-navy-500">
          {config.provider === 'ollama' && 'Local Ollama instance required'}
          {config.provider === 'claude' && 'Requires Anthropic API key'}
          {config.provider === 'openai' && 'Requires OpenAI API key'}
        </p>
      </div>

      {/* Model Selection */}
      <div>
        <label className="block text-ice-navy-400 text-sm font-medium mb-2">
          Model
        </label>
        <input
          type="text"
          value={config.model}
          onChange={(e) => handleChange('model', e.target.value)}
          placeholder={`e.g., ${suggestedModels[0] || 'model-name'}`}
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 transition-all"
        />
        {suggestedModels.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-ice-navy-500 mb-1">Suggested models:</p>
            <div className="flex flex-wrap gap-1">
              {suggestedModels.map((model) => (
                <button
                  key={model}
                  type="button"
                  onClick={() => handleChange('model', model)}
                  className="px-2 py-1 text-xs bg-ice-navy-600 hover:bg-ice-gold-500/20 border border-ice-navy-500 hover:border-ice-gold-500/50 rounded text-ice-navy-300 hover:text-ice-gold-400 transition-all"
                >
                  {model}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Prompt */}
      <div>
        <label className="block text-ice-navy-400 text-sm font-medium mb-2">
          Prompt
          <span className="ml-1 text-xs text-ice-navy-500 font-normal">
            (Use {'{input}'} for data interpolation)
          </span>
        </label>
        <textarea
          value={config.prompt}
          onChange={(e) => handleChange('prompt', e.target.value)}
          placeholder="Analyze this data and provide insights: {input}"
          rows={4}
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 transition-all font-mono"
        />
        <p className="mt-1 text-xs text-ice-navy-500">
          Variables from input data can be referenced using {'{path.to.field}'}
        </p>
      </div>

      {/* System Prompt (Optional) */}
      <div>
        <label className="block text-ice-navy-400 text-sm font-medium mb-2">
          System Prompt
          <span className="ml-1 text-xs text-ice-navy-500 font-normal">(Optional)</span>
        </label>
        <textarea
          value={config.systemPrompt || ''}
          onChange={(e) => handleChange('systemPrompt', e.target.value || undefined)}
          placeholder="You are a helpful assistant specialized in data analysis..."
          rows={3}
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 transition-all font-mono"
        />
      </div>

      {/* Advanced Settings */}
      <div className="pt-3 border-t border-ice-navy-700">
        <h4 className="text-sm font-semibold text-ice-navy-300 mb-3">
          Advanced Settings
        </h4>

        {/* Temperature */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-ice-navy-400 text-sm font-medium">
              Temperature
            </label>
            <span className="text-ice-gold-400 text-sm font-mono">
              {config.temperature !== undefined ? config.temperature.toFixed(2) : '1.00'}
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={config.temperature !== undefined ? config.temperature : 1.0}
            onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
            className="w-full h-2 bg-ice-navy-700 rounded-lg appearance-none cursor-pointer accent-ice-gold-500"
          />
          <div className="flex justify-between text-xs text-ice-navy-500 mt-1">
            <span>Precise (0.0)</span>
            <span>Balanced (1.0)</span>
            <span>Creative (2.0)</span>
          </div>
        </div>

        {/* Max Tokens */}
        <div className="mb-4">
          <label className="block text-ice-navy-400 text-sm font-medium mb-2">
            Max Tokens
          </label>
          <input
            type="number"
            min="1"
            max="8000"
            value={config.maxTokens || 1000}
            onChange={(e) =>
              handleChange('maxTokens', parseInt(e.target.value) || undefined)
            }
            placeholder="1000"
            className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 transition-all"
          />
          <p className="mt-1 text-xs text-ice-navy-500">
            Maximum length of the generated response
          </p>
        </div>

        {/* Input Mapping */}
        <div>
          <label className="block text-ice-navy-400 text-sm font-medium mb-2">
            Input Mapping
            <span className="ml-1 text-xs text-ice-navy-500 font-normal">(JSONPath)</span>
          </label>
          <input
            type="text"
            value={config.inputMapping || ''}
            onChange={(e) => handleChange('inputMapping', e.target.value || undefined)}
            placeholder="$.data.items[*]"
            className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 transition-all font-mono"
          />
          <p className="mt-1 text-xs text-ice-navy-500">
            Extract specific data from input using JSONPath (leave empty for full input)
          </p>
        </div>
      </div>

      {/* Info Panel */}
      <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <svg
            className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="text-xs text-blue-300">
            <p className="font-medium mb-1">How it works:</p>
            <ul className="list-disc list-inside space-y-0.5 text-blue-400/80">
              <li>Input data flows from previous nodes</li>
              <li>Prompt is interpolated with input variables</li>
              <li>LLM generates response based on configuration</li>
              <li>Output is passed to connected nodes</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AskAIConfigPanel;
