/**
 * ConditionalConfigPanel - Configuration panel for conditional/control flow nodes
 *
 * Provides specialized config UIs for:
 * - If/Then: Conditional branching with comparison operators
 * - Switch: Multi-way branching based on value matching
 * - For Each: Iteration over arrays
 * - While: Loop with condition
 * - Compare: Value comparison with operators
 * - And/Or: Logical operator combination
 */

import React, { useState } from 'react';

// Comparison operators for conditional logic
const OPERATORS = [
  { value: '==', label: 'Equals (==)' },
  { value: '!=', label: 'Not Equals (!=)' },
  { value: '>', label: 'Greater Than (>)' },
  { value: '<', label: 'Less Than (<)' },
  { value: '>=', label: 'Greater or Equal (>=)' },
  { value: '<=', label: 'Less or Equal (<=)' },
  { value: 'contains', label: 'Contains' },
  { value: 'matches', label: 'Matches (regex)' },
];

// Logical operators
const LOGICAL_OPERATORS = [
  { value: 'AND', label: 'AND' },
  { value: 'OR', label: 'OR' },
];

interface ConditionalConfigPanelProps {
  nodeType: string;
  config: any;
  onChange: (config: any) => void;
}

/**
 * Configuration for If/Then conditional branching
 */
const IfThenConfig: React.FC<ConditionalConfigPanelProps> = ({ config, onChange }) => {
  const [leftOperand, setLeftOperand] = useState(config?.leftOperand || '');
  const [operator, setOperator] = useState(config?.operator || '==');
  const [rightOperand, setRightOperand] = useState(config?.rightOperand || '');

  const handleUpdate = (field: string, value: any) => {
    const updated = { ...config, [field]: value };
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Left Operand
        </label>
        <input
          type="text"
          value={leftOperand}
          onChange={(e) => {
            setLeftOperand(e.target.value);
            handleUpdate('leftOperand', e.target.value);
          }}
          placeholder="$.data.value or literal"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
        <p className="text-ice-navy-500 text-xs mt-1">
          Use JSONPath ($.field) or literal value
        </p>
      </div>

      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Operator
        </label>
        <select
          value={operator}
          onChange={(e) => {
            setOperator(e.target.value);
            handleUpdate('operator', e.target.value);
          }}
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        >
          {OPERATORS.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Right Operand
        </label>
        <input
          type="text"
          value={rightOperand}
          onChange={(e) => {
            setRightOperand(e.target.value);
            handleUpdate('rightOperand', e.target.value);
          }}
          placeholder="$.data.value or literal"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
        <p className="text-ice-navy-500 text-xs mt-1">
          Use JSONPath ($.field) or literal value
        </p>
      </div>

      <div className="pt-4 border-t border-ice-navy-600">
        <div className="text-ice-navy-400 text-xs">
          <p className="font-medium mb-1">Output Branches:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li className="text-green-400">True: Condition met</li>
            <li className="text-red-400">False: Condition not met</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

/**
 * Configuration for Switch multi-way branching
 */
const SwitchConfig: React.FC<ConditionalConfigPanelProps> = ({ config, onChange }) => {
  const [switchValue, setSwitchValue] = useState(config?.switchValue || '');
  const [cases, setCases] = useState(config?.cases || [{ value: '', branch: 'case1' }]);

  const handleUpdate = (field: string, value: any) => {
    onChange({ ...config, [field]: value });
  };

  const addCase = () => {
    const newCases = [...cases, { value: '', branch: `case${cases.length + 1}` }];
    setCases(newCases);
    handleUpdate('cases', newCases);
  };

  const removeCase = (index: number) => {
    const newCases = cases.filter((_: any, i: number) => i !== index);
    setCases(newCases);
    handleUpdate('cases', newCases);
  };

  const updateCase = (index: number, field: string, value: string) => {
    const newCases = [...cases];
    newCases[index] = { ...newCases[index], [field]: value };
    setCases(newCases);
    handleUpdate('cases', newCases);
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Switch Value
        </label>
        <input
          type="text"
          value={switchValue}
          onChange={(e) => {
            setSwitchValue(e.target.value);
            handleUpdate('switchValue', e.target.value);
          }}
          placeholder="$.data.field"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
        <p className="text-ice-navy-500 text-xs mt-1">
          JSONPath to value to switch on
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-ice-navy-300 text-sm font-medium">
            Cases
          </label>
          <button
            onClick={addCase}
            className="px-2 py-1 text-xs bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 rounded transition-colors"
          >
            Add Case
          </button>
        </div>

        <div className="space-y-2">
          {cases.map((caseItem: any, index: number) => (
            <div
              key={index}
              className="p-3 bg-ice-navy-700/50 border border-ice-navy-600 rounded-lg"
            >
              <div className="flex items-center gap-2 mb-2">
                <input
                  type="text"
                  value={caseItem.value}
                  onChange={(e) => updateCase(index, 'value', e.target.value)}
                  placeholder="Match value"
                  className="flex-1 px-2 py-1 bg-ice-navy-700 border border-ice-navy-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-ice-gold-500/50"
                />
                <button
                  onClick={() => removeCase(index)}
                  className="p-1 text-red-400 hover:text-red-300 transition-colors"
                  title="Remove case"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <input
                type="text"
                value={caseItem.branch}
                onChange={(e) => updateCase(index, 'branch', e.target.value)}
                placeholder="Branch name"
                className="w-full px-2 py-1 bg-ice-navy-700 border border-ice-navy-600 rounded text-white text-xs focus:outline-none focus:ring-1 focus:ring-ice-gold-500/50"
              />
            </div>
          ))}
        </div>
      </div>

      <div className="pt-4 border-t border-ice-navy-600">
        <div className="text-ice-navy-400 text-xs">
          <p className="font-medium mb-1">Output Branches:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            {cases.map((c: any, i: number) => (
              <li key={i} className="text-blue-400">
                {c.branch}: {c.value || '(empty)'}
              </li>
            ))}
            <li className="text-ice-navy-400">default: No match</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

/**
 * Configuration for For Each loop
 */
const ForEachConfig: React.FC<ConditionalConfigPanelProps> = ({ config, onChange }) => {
  const [arrayPath, setArrayPath] = useState(config?.arrayPath || '');
  const [itemVariable, setItemVariable] = useState(config?.itemVariable || 'item');

  const handleUpdate = (field: string, value: any) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Array Path
        </label>
        <input
          type="text"
          value={arrayPath}
          onChange={(e) => {
            setArrayPath(e.target.value);
            handleUpdate('arrayPath', e.target.value);
          }}
          placeholder="$.data.items"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
        <p className="text-ice-navy-500 text-xs mt-1">
          JSONPath to array in input data
        </p>
      </div>

      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Item Variable Name
        </label>
        <input
          type="text"
          value={itemVariable}
          onChange={(e) => {
            setItemVariable(e.target.value);
            handleUpdate('itemVariable', e.target.value);
          }}
          placeholder="item"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
        <p className="text-ice-navy-500 text-xs mt-1">
          Variable name for each item in the loop
        </p>
      </div>

      <div className="pt-4 border-t border-ice-navy-600">
        <div className="text-ice-navy-400 text-xs">
          <p className="font-medium mb-1">Output Branches:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li className="text-blue-400">item: For each item</li>
            <li className="text-green-400">complete: After all items</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

/**
 * Configuration for While loop
 */
const WhileConfig: React.FC<ConditionalConfigPanelProps> = ({ config, onChange }) => {
  const [condition, setCondition] = useState(config?.condition || '');
  const [maxIterations, setMaxIterations] = useState(config?.maxIterations || 100);

  const handleUpdate = (field: string, value: any) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Condition
        </label>
        <input
          type="text"
          value={condition}
          onChange={(e) => {
            setCondition(e.target.value);
            handleUpdate('condition', e.target.value);
          }}
          placeholder="$.data.count < 10"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
        <p className="text-ice-navy-500 text-xs mt-1">
          Expression that evaluates to true/false
        </p>
      </div>

      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Max Iterations
        </label>
        <input
          type="number"
          value={maxIterations}
          onChange={(e) => {
            setMaxIterations(parseInt(e.target.value));
            handleUpdate('maxIterations', parseInt(e.target.value));
          }}
          min="1"
          max="10000"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
        <p className="text-ice-navy-500 text-xs mt-1">
          Safety limit to prevent infinite loops
        </p>
      </div>

      <div className="pt-4 border-t border-ice-navy-600">
        <div className="text-ice-navy-400 text-xs">
          <p className="font-medium mb-1">Output Branches:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li className="text-blue-400">loop: While condition is true</li>
            <li className="text-green-400">complete: Condition becomes false</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

/**
 * Configuration for Compare operation
 */
const CompareConfig: React.FC<ConditionalConfigPanelProps> = ({ config, onChange }) => {
  const [leftValue, setLeftValue] = useState(config?.leftValue || '');
  const [operator, setOperator] = useState(config?.operator || '==');
  const [rightValue, setRightValue] = useState(config?.rightValue || '');

  const handleUpdate = (field: string, value: any) => {
    onChange({ ...config, [field]: value });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Left Value
        </label>
        <input
          type="text"
          value={leftValue}
          onChange={(e) => {
            setLeftValue(e.target.value);
            handleUpdate('leftValue', e.target.value);
          }}
          placeholder="$.data.a"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
      </div>

      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Operator
        </label>
        <select
          value={operator}
          onChange={(e) => {
            setOperator(e.target.value);
            handleUpdate('operator', e.target.value);
          }}
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        >
          {OPERATORS.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Right Value
        </label>
        <input
          type="text"
          value={rightValue}
          onChange={(e) => {
            setRightValue(e.target.value);
            handleUpdate('rightValue', e.target.value);
          }}
          placeholder="$.data.b"
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        />
      </div>

      <div className="pt-4 border-t border-ice-navy-600">
        <div className="text-ice-navy-400 text-xs">
          <p className="font-medium mb-1">Output:</p>
          <p className="ml-2">Boolean result (true/false)</p>
        </div>
      </div>
    </div>
  );
};

/**
 * Configuration for And/Or logical operators
 */
const AndOrConfig: React.FC<ConditionalConfigPanelProps> = ({ config, onChange }) => {
  const [operator, setOperator] = useState(config?.operator || 'AND');
  const [conditions, setConditions] = useState(config?.conditions || ['', '']);

  const handleUpdate = (field: string, value: any) => {
    onChange({ ...config, [field]: value });
  };

  const addCondition = () => {
    const newConditions = [...conditions, ''];
    setConditions(newConditions);
    handleUpdate('conditions', newConditions);
  };

  const removeCondition = (index: number) => {
    if (conditions.length <= 2) return; // Keep at least 2 conditions
    const newConditions = conditions.filter((_: any, i: number) => i !== index);
    setConditions(newConditions);
    handleUpdate('conditions', newConditions);
  };

  const updateCondition = (index: number, value: string) => {
    const newConditions = [...conditions];
    newConditions[index] = value;
    setConditions(newConditions);
    handleUpdate('conditions', newConditions);
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-ice-navy-300 text-sm font-medium mb-2">
          Logical Operator
        </label>
        <select
          value={operator}
          onChange={(e) => {
            setOperator(e.target.value);
            handleUpdate('operator', e.target.value);
          }}
          className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
        >
          {LOGICAL_OPERATORS.map((op) => (
            <option key={op.value} value={op.value}>
              {op.label}
            </option>
          ))}
        </select>
        <p className="text-ice-navy-500 text-xs mt-1">
          {operator === 'AND' ? 'All conditions must be true' : 'At least one condition must be true'}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-ice-navy-300 text-sm font-medium">
            Conditions
          </label>
          <button
            onClick={addCondition}
            className="px-2 py-1 text-xs bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 rounded transition-colors"
          >
            Add Condition
          </button>
        </div>

        <div className="space-y-2">
          {conditions.map((condition: string, index: number) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={condition}
                onChange={(e) => updateCondition(index, e.target.value)}
                placeholder="$.data.field == value"
                className="flex-1 px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
              />
              {conditions.length > 2 && (
                <button
                  onClick={() => removeCondition(index)}
                  className="p-2 text-red-400 hover:text-red-300 transition-colors"
                  title="Remove condition"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="pt-4 border-t border-ice-navy-600">
        <div className="text-ice-navy-400 text-xs">
          <p className="font-medium mb-1">Output:</p>
          <p className="ml-2">Boolean result (true/false)</p>
        </div>
      </div>
    </div>
  );
};

/**
 * Main conditional config panel component
 * Routes to appropriate sub-component based on node type
 */
export const ConditionalConfigPanel: React.FC<ConditionalConfigPanelProps> = ({
  nodeType,
  config,
  onChange,
}) => {
  // Render appropriate config panel based on node type
  const renderConfig = () => {
    switch (nodeType) {
      case 'If/Then':
      case 'transform_if_then':
        return <IfThenConfig nodeType={nodeType} config={config} onChange={onChange} />;

      case 'Switch':
      case 'transform_switch':
        return <SwitchConfig nodeType={nodeType} config={config} onChange={onChange} />;

      case 'For Each':
      case 'transform_for_each':
        return <ForEachConfig nodeType={nodeType} config={config} onChange={onChange} />;

      case 'While':
      case 'transform_while':
        return <WhileConfig nodeType={nodeType} config={config} onChange={onChange} />;

      case 'Compare':
      case 'transform_compare':
        return <CompareConfig nodeType={nodeType} config={config} onChange={onChange} />;

      case 'And/Or':
      case 'transform_and_or':
        return <AndOrConfig nodeType={nodeType} config={config} onChange={onChange} />;

      default:
        return (
          <div className="text-ice-navy-500 text-sm">
            No configuration available for this node type.
          </div>
        );
    }
  };

  return (
    <div className="p-4 bg-ice-navy-800 rounded-lg">
      <h3 className="text-sm font-semibold text-ice-navy-300 uppercase tracking-wider mb-4">
        {nodeType} Configuration
      </h3>
      {renderConfig()}
    </div>
  );
};

export default ConditionalConfigPanel;
