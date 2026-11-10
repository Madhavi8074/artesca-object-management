import React from 'react'
import type { QueryGroup, QueryRule } from '../types'

interface QueryBuilderProps {
  rootGroup: QueryGroup
  onChange: (newGroup: QueryGroup) => void
  onExecute: () => void
  loading?: boolean
}

const AVAILABLE_FIELDS = [
  { value: 'filename', label: 'File Name', type: 'string' },
  { value: 'bucket', label: 'S3 Bucket', type: 'string' },
  { value: 'size_bytes', label: 'File Size (bytes)', type: 'number' },
  { value: 'content_type', label: 'Content Type', type: 'string' },
  { value: 'status', label: 'Status', type: 'string' },
  { value: 'created_at', label: 'Created Date', type: 'date' },
  { value: 'classification', label: 'Classification', type: 'string' },
  { value: 'department', label: 'Department', type: 'string' },
  { value: 'project', label: 'Project', type: 'string' },
  { value: 'document_type', label: 'Document Type', type: 'string' },
  { value: 'author', label: 'Author', type: 'string' },
  { value: 'schema_id', label: 'Schema ID', type: 'number' },
  { value: 'custom_metadata.', label: 'Custom JSONB Property...', type: 'custom' },
]

const OPERATORS_BY_TYPE: Record<string, Array<{ value: string; label: string }>> = {
  string: [
    { value: 'equals', label: 'equals (=)' },
    { value: 'not_equals', label: 'not equals (!=)' },
    { value: 'contains', label: 'contains (like)' },
    { value: 'not_contains', label: 'does not contain' },
    { value: 'starts_with', label: 'starts with' },
    { value: 'ends_with', label: 'ends with' },
    { value: 'regex', label: 'matches regex (~*)' },
    { value: 'is_null', label: 'is empty / null' },
    { value: 'is_not_null', label: 'is not null' },
  ],
  number: [
    { value: 'equals', label: 'equals (=)' },
    { value: 'not_equals', label: 'not equals (!=)' },
    { value: '>', label: 'greater than (>)' },
    { value: '>=', label: 'greater than or equal (>=)' },
    { value: '<', label: 'less than (<)' },
    { value: '<=', label: 'less than or equal (<=)' },
    { value: 'is_null', label: 'is empty' },
    { value: 'is_not_null', label: 'is present' },
  ],
  date: [
    { value: 'equals', label: 'on date (=)' },
    { value: '>', label: 'after (>)' },
    { value: '<', label: 'before (<)' },
  ],
  custom: [
    { value: 'equals', label: 'equals (=)' },
    { value: 'not_equals', label: 'not equals (!=)' },
    { value: 'contains', label: 'contains text' },
    { value: '>', label: 'greater than (>)' },
    { value: '<', label: 'less than (<)' },
    { value: 'exists', label: 'key exists in JSONB' },
    { value: 'is_null', label: 'key does not exist' },
  ],
}

function isGroup(item: QueryRule | QueryGroup): item is QueryGroup {
  return 'combinator' in item && Array.isArray((item as QueryGroup).rules)
}

interface GroupEditorProps {
  group: QueryGroup
  path: number[]
  onChange: (updated: QueryGroup) => void
  onRemove?: () => void
  isRoot?: boolean
}

const GroupEditor: React.FC<GroupEditorProps> = ({ group, onChange, onRemove, isRoot = false }) => {
  const setCombinator = (c: 'AND' | 'OR' | 'NOT') => {
    onChange({ ...group, combinator: c })
  }

  const addRule = () => {
    const newRule: QueryRule = { field: 'filename', operator: 'contains', value: '' }
    onChange({ ...group, rules: [...group.rules, newRule] })
  }

  const addSubgroup = () => {
    const newSub: QueryGroup = {
      combinator: 'OR',
      rules: [{ field: 'classification', operator: 'equals', value: 'Restricted' }],
    }
    onChange({ ...group, rules: [...group.rules, newSub] })
  }

  const updateChild = (index: number, updatedItem: QueryRule | QueryGroup) => {
    const nextRules = [...group.rules]
    nextRules[index] = updatedItem
    onChange({ ...group, rules: nextRules })
  }

  const removeChild = (index: number) => {
    const nextRules = group.rules.filter((_, i) => i !== index)
    onChange({ ...group, rules: nextRules })
  }

  return (
    <div className={`qb-group ${isRoot ? 'qb-root-group' : 'qb-nested-group'}`}>
      <div className="qb-group-header">
        <div className="qb-combinator-selector">
          <span className="qb-match-label">Match:</span>
          {(['AND', 'OR', 'NOT'] as const).map((comb) => (
            <button
              key={comb}
              type="button"
              className={`qb-comb-btn ${group.combinator === comb ? `active active-${comb.toLowerCase()}` : ''}`}
              onClick={() => setCombinator(comb)}
            >
              {comb === 'AND' ? 'ALL (AND)' : comb === 'OR' ? 'ANY (OR)' : 'NONE (NOT)'}
            </button>
          ))}
        </div>

        <div className="qb-group-actions">
          <button type="button" className="btn btn-sm btn-secondary" onClick={addRule}>
            + Add Condition
          </button>
          <button type="button" className="btn btn-sm btn-secondary" onClick={addSubgroup}>
            + Add Group
          </button>
          {!isRoot && onRemove && (
            <button type="button" className="btn btn-sm btn-danger-outline" onClick={onRemove} title="Remove Group">
              Delete Group
            </button>
          )}
        </div>
      </div>

      <div className="qb-rules-list">
        {group.rules.length === 0 ? (
          <div className="qb-empty-group">No conditions in this group. Click "+ Add Condition" above.</div>
        ) : (
          group.rules.map((child, index) => {
            if (isGroup(child)) {
              return (
                <div key={index} className="qb-nested-row">
                  <div className="qb-tree-line" />
                  <GroupEditor
                    group={child}
                    path={[index]}
                    onChange={(updated) => updateChild(index, updated)}
                    onRemove={() => removeChild(index)}
                  />
                </div>
              )
            }

            return (
              <div key={index} className="qb-rule-row">
                <div className="qb-tree-line" />
                <RuleEditor
                  rule={child}
                  onChange={(updated) => updateChild(index, updated)}
                  onRemove={() => removeChild(index)}
                />
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

interface RuleEditorProps {
  rule: QueryRule
  onChange: (updated: QueryRule) => void
  onRemove: () => void
}

const RuleEditor: React.FC<RuleEditorProps> = ({ rule, onChange, onRemove }) => {
  const isCustomField = rule.field.startsWith('custom_metadata.') || !AVAILABLE_FIELDS.some((f) => f.value === rule.field)

  const handleFieldSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value
    if (val === 'custom_metadata.') {
      onChange({ ...rule, field: 'custom_metadata.custom_key', operator: 'equals', value: '' })
    } else {
      const match = AVAILABLE_FIELDS.find((f) => f.value === val)
      const fType = match?.type || 'string'
      const ops = OPERATORS_BY_TYPE[fType] || OPERATORS_BY_TYPE.string
      onChange({ ...rule, field: val, operator: ops[0].value, value: '' })
    }
  }

  const handleCustomKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawKey = e.target.value.trim().replace(/^custom_metadata\./, '')
    onChange({ ...rule, field: `custom_metadata.${rawKey}` })
  }

  // Determine current field type
  let fieldType = 'string'
  if (isCustomField) {
    fieldType = 'custom'
  } else {
    const match = AVAILABLE_FIELDS.find((f) => f.value === rule.field)
    if (match) fieldType = match.type
  }

  const operators = OPERATORS_BY_TYPE[fieldType] || OPERATORS_BY_TYPE.string
  const needsValue = !['is_null', 'is_not_null', 'exists', 'not_exists'].includes(rule.operator)

  return (
    <div className="qb-rule-inputs">
      {/* Field Selector */}
      <div className="qb-field-select-wrap">
        <select
          className="form-control form-control-sm"
          value={isCustomField ? 'custom_metadata.' : rule.field}
          onChange={handleFieldSelect}
        >
          {AVAILABLE_FIELDS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
        {isCustomField && (
          <input
            type="text"
            className="form-control form-control-sm qb-custom-key-input"
            placeholder="json_key"
            value={rule.field.replace(/^custom_metadata\./, '')}
            onChange={handleCustomKeyChange}
            title="JSONB property key inside custom_metadata"
          />
        )}
      </div>

      {/* Operator */}
      <select
        className="form-control form-control-sm qb-op-select"
        value={rule.operator}
        onChange={(e) => onChange({ ...rule, operator: e.target.value })}
      >
        {operators.map((op) => (
          <option key={op.value} value={op.value}>
            {op.label}
          </option>
        ))}
      </select>

      {/* Value Input */}
      {needsValue ? (
        <input
          type={fieldType === 'number' ? 'number' : fieldType === 'date' ? 'date' : 'text'}
          className="form-control form-control-sm qb-val-input"
          placeholder="Comparison value..."
          value={String(rule.value ?? '')}
          onChange={(e) => {
            const val = fieldType === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value
            onChange({ ...rule, value: val })
          }}
        />
      ) : (
        <span className="qb-no-value-badge">(no value needed)</span>
      )}

      {/* Delete Rule */}
      <button type="button" className="btn btn-sm btn-icon btn-danger-outline" onClick={onRemove} title="Delete Condition">
        ✕
      </button>
    </div>
  )
}

export const QueryBuilder: React.FC<QueryBuilderProps> = ({
  rootGroup,
  onChange,
  onExecute,
  loading = false,
}) => {
  return (
    <div className="qb-container">
      <div className="qb-toolbar">
        <div>
          <h3 className="qb-title">Visual Query Engine</h3>
          <p className="qb-subtitle">
            Construct complex nested boolean queries with AND / OR / NOT expressions across standard metadata and native PostgreSQL JSONB fields.
          </p>
        </div>
        <div className="qb-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={onExecute}
            disabled={loading}
          >
            {loading ? 'Executing Query...' : 'Execute Visual Query'}
          </button>
        </div>
      </div>

      <div className="qb-workspace">
        <GroupEditor group={rootGroup} path={[]} onChange={onChange} isRoot={true} />
      </div>
    </div>
  )
}
