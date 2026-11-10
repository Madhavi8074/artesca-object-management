import React, { useState, useEffect } from 'react'
import { ApiClient } from '../services/api'
import type { MetadataSchema, SchemaField, UserProfile } from '../types'

export const SchemaAdminView: React.FC<{ userProfile: UserProfile | null }> = ({ userProfile }) => {
  const [schemas, setSchemas] = useState<MetadataSchema[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Modal State for Create / Edit
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingSchemaId, setEditingSchemaId] = useState<number | null>(null)
  const [schemaName, setSchemaName] = useState('')
  const [schemaDesc, setSchemaDesc] = useState('')
  const [schemaActive, setSchemaActive] = useState(true)
  const [fields, setFields] = useState<SchemaField[]>([])
  const [submitting, setSubmitting] = useState(false)

  // Validation Sandbox State
  const [selectedSchemaForTest, setSelectedSchemaForTest] = useState<MetadataSchema | null>(null)
  const [testPayloadJson, setTestPayloadJson] = useState('{\n  "project_code": "PRJ-101",\n  "classification": "Secret"\n}')
  const [valResult, setValResult] = useState<{ is_valid: boolean; errors: string[] } | null>(null)
  const [validating, setValidating] = useState(false)

  const loadSchemas = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await ApiClient.listSchemas()
      setSchemas(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load schemas')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSchemas()
  }, [])

  const openCreateModal = () => {
    setEditingSchemaId(null)
    setSchemaName('')
    setSchemaDesc('')
    setSchemaActive(true)
    setFields([
      { name: 'document_category', label: 'Document Category', type: 'string', required: true },
      { name: 'security_level', label: 'Security Level', type: 'enum', required: true, options: ['Unclassified', 'Restricted', 'Secret', 'Top Secret'] },
    ])
    setIsModalOpen(true)
  }

  const openEditModal = (schema: MetadataSchema) => {
    setEditingSchemaId(schema.id)
    setSchemaName(schema.name)
    setSchemaDesc(schema.description || '')
    setSchemaActive(schema.is_active)
    setFields(schema.fields ? [...schema.fields] : [])
    setIsModalOpen(true)
  }

  const addField = () => {
    const newField: SchemaField = {
      name: `field_${fields.length + 1}`,
      label: `Field ${fields.length + 1}`,
      type: 'string',
      required: false,
    }
    setFields([...fields, newField])
  }

  const updateField = (index: number, updated: Partial<SchemaField>) => {
    const next = [...fields]
    next[index] = { ...next[index], ...updated }
    setFields(next)
  }

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index))
  }

  const handleSaveSchema = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!schemaName.trim()) {
      alert('Please provide a schema name')
      return
    }

    try {
      setSubmitting(true)
      setError(null)

      if (editingSchemaId) {
        await ApiClient.updateSchema(editingSchemaId, {
          name: schemaName.trim(),
          description: schemaDesc.trim(),
          is_active: schemaActive,
          fields,
        })
        setSuccessMsg(`Schema "${schemaName}" updated successfully!`)
      } else {
        await ApiClient.createSchema({
          name: schemaName.trim(),
          description: schemaDesc.trim(),
          is_active: schemaActive,
          fields,
        })
        setSuccessMsg(`Schema "${schemaName}" created successfully!`)
      }

      setIsModalOpen(false)
      loadSchemas()
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save schema')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteSchema = async (id: number, name: string) => {
    if (!window.confirm(`Are you sure you want to delete schema "${name}"? This cannot be undone.`)) {
      return
    }
    try {
      setError(null)
      await ApiClient.deleteSchema(id)
      setSuccessMsg(`Schema "${name}" deleted.`)
      loadSchemas()
      if (selectedSchemaForTest?.id === id) {
        setSelectedSchemaForTest(null)
      }
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete schema')
    }
  }

  const handleTestValidation = async () => {
    if (!selectedSchemaForTest) return
    try {
      setValidating(true)
      setValResult(null)
      let parsed = {}
      try {
        parsed = JSON.parse(testPayloadJson)
      } catch {
        alert('Invalid JSON in payload editor')
        setValidating(false)
        return
      }

      const res = await ApiClient.validateSchema(selectedSchemaForTest.id, parsed)
      setValResult(res)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Validation test request failed')
    } finally {
      setValidating(false)
    }
  }

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">Metadata Schema Administration</h1>
          <p className="view-subtitle">
            Define, version, and enforce structured JSONB metadata schemas with field data types, mandatory rules, and enum validations.
          </p>
        </div>
<div className="view-actions">
  {userProfile?.roles.includes('ADMIN') && (
    <button className="btn btn-primary" onClick={openCreateModal}>
      + Create New Schema
    </button>
  )}
</div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      {/* Schema List */}
      <div className="card mb-4">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="card-title">Registered Schemas ({schemas.length})</h3>
          <button className="btn btn-sm btn-secondary" onClick={loadSchemas}>
            Refresh
          </button>
        </div>

        <div className="card-body p-0">
          {loading ? (
            <div className="p-4 text-center text-muted">Loading metadata schemas...</div>
          ) : schemas.length === 0 ? (
            <div className="p-4 text-center text-muted">
              No schemas found. Click "+ Create New Schema" to create your first enterprise document template.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Version</th>
                    <th>Status</th>
                    <th>Fields</th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {schemas.map((s) => (
                    <tr key={s.id}>
                      <td>#{s.id}</td>
                      <td>
                        <strong>{s.name}</strong>
                      </td>
                      <td className="text-muted small" style={{ maxWidth: '280px' }}>
                        {s.description || '—'}
                      </td>
                      <td>v{s.version}</td>
                      <td>
                        <span className={`badge ${s.is_active ? 'badge-success' : 'badge-secondary'}`}>
                          {s.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-info">{s.fields?.length || 0} fields</span>
                      </td>
                      <td className="text-end">
                        <button
                          className="btn btn-sm btn-secondary me-2"
                          onClick={() => {
                            setSelectedSchemaForTest(s)
                            // generate initial sample JSON
                            const sample: Record<string, unknown> = {}
                            s.fields?.forEach((f) => {
                              if (f.type === 'number') sample[f.name] = 100
                              else if (f.type === 'boolean') sample[f.name] = true
                              else if (f.type === 'enum' && f.options && f.options.length > 0) sample[f.name] = f.options[0]
                              else sample[f.name] = `Sample ${f.label}`
                            })
                            setTestPayloadJson(JSON.stringify(sample, null, 2))
                            setValResult(null)
                          }}
                          title="Open Validation Sandbox"
                        >
                          Test Sandbox
                        </button>
                        <button
                          className="btn btn-sm btn-secondary me-2"
                          onClick={() => openEditModal(s)}
                          title="Edit Schema"
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm btn-danger-outline"
                          onClick={() => handleDeleteSchema(s.id, s.name)}
                          title="Delete Schema"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Live Validation Sandbox */}
      {selectedSchemaForTest && (
        <div className="card mb-4 border-primary">
          <div className="card-header bg-light d-flex justify-content-between align-items-center">
            <div>
              <h3 className="card-title text-primary mb-0">
                Interactive Validation Sandbox: <strong>{selectedSchemaForTest.name}</strong> (v{selectedSchemaForTest.version})
              </h3>
              <p className="text-muted small mb-0">
                Test custom metadata payloads against this schema before applying them to uploads or updates.
              </p>
            </div>
            <button className="btn btn-sm btn-secondary" onClick={() => setSelectedSchemaForTest(null)}>
              Close Sandbox
            </button>
          </div>
          <div className="card-body">
            <div className="row">
              <div className="col-md-6">
                <label className="form-label fw-bold">Test Metadata JSON:</label>
                <textarea
                  className="form-control font-monospace"
                  rows={8}
                  value={testPayloadJson}
                  onChange={(e) => setTestPayloadJson(e.target.value)}
                />
                <button
                  className="btn btn-primary mt-3"
                  onClick={handleTestValidation}
                  disabled={validating}
                >
                  {validating ? 'Validating against engine...' : 'Validate Payload'}
                </button>
              </div>

              <div className="col-md-6">
                <label className="form-label fw-bold">Validation Engine Result:</label>
                {valResult ? (
                  <div
                    className={`p-3 rounded border ${
                      valResult.is_valid ? 'bg-success-subtle border-success' : 'bg-danger-subtle border-danger'
                    }`}
                  >
                    <div className="d-flex align-items-center mb-2">
                      <span className={`badge ${valResult.is_valid ? 'badge-success' : 'badge-danger'} me-2`}>
                        {valResult.is_valid ? 'PASSED: VALID PAYLOAD' : 'FAILED: INVALID PAYLOAD'}
                      </span>
                    </div>
                    {valResult.is_valid ? (
                      <p className="text-success mb-0 small">
                        All mandatory fields, enum selections, and data type constraints are satisfied by this metadata object.
                      </p>
                    ) : (
                      <div>
                        <p className="text-danger fw-bold small mb-1">
                          The schema validator detected {valResult.errors.length} issue(s):
                        </p>
                        <ul className="text-danger small mb-0 ps-3">
                          {valResult.errors.map((err, i) => (
                            <li key={i}>{err}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 text-center text-muted border rounded bg-light">
                    Click "Validate Payload" to inspect schema compliance.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create / Edit Modal */}
      {isModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h3 className="modal-title">{editingSchemaId ? 'Edit Schema' : 'Create Metadata Schema'}</h3>
                <button type="button" className="btn-close" onClick={() => setIsModalOpen(false)}>
                  ✕
                </button>
              </div>

              <form onSubmit={handleSaveSchema}>
                <div className="modal-body">
                  <div className="row g-3 mb-3">
                    <div className="col-md-8">
                      <label className="form-label fw-bold">Schema Name *</label>
                      <input
                        type="text"
                        className="form-control"
                        required
                        placeholder="e.g., Defense Project Spec"
                        value={schemaName}
                        onChange={(e) => setSchemaName(e.target.value)}
                      />
                    </div>
                    <div className="col-md-4 d-flex align-items-end">
                      <div className="form-check form-switch mb-2">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          id="schemaActiveSwitch"
                          checked={schemaActive}
                          onChange={(e) => setSchemaActive(e.target.checked)}
                        />
                        <label className="form-check-label" htmlFor="schemaActiveSwitch">
                          Active & Enforced
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Description</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Brief summary of document category requirements..."
                      value={schemaDesc}
                      onChange={(e) => setSchemaDesc(e.target.value)}
                    />
                  </div>

                  <div className="d-flex justify-content-between align-items-center mt-4 mb-2">
                    <h4 className="h6 fw-bold mb-0">Schema Fields ({fields.length})</h4>
                    <button type="button" className="btn btn-sm btn-secondary" onClick={addField}>
                      + Add Field
                    </button>
                  </div>

                  <div className="schema-fields-builder border rounded p-2 mb-3 bg-light">
                    {fields.length === 0 ? (
                      <div className="text-center text-muted p-3">No fields defined yet. Click "+ Add Field".</div>
                    ) : (
                      fields.map((field, idx) => (
                        <div key={idx} className="card p-3 mb-2 shadow-none border">
                          <div className="row g-2 align-items-center">
                            <div className="col-md-3">
                              <label className="small text-muted mb-0">Key (name) *</label>
                              <input
                                type="text"
                                className="form-control form-control-sm font-monospace"
                                required
                                placeholder="field_key"
                                value={field.name}
                                onChange={(e) => updateField(idx, { name: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                              />
                            </div>
                            <div className="col-md-3">
                              <label className="small text-muted mb-0">Display Label *</label>
                              <input
                                type="text"
                                className="form-control form-control-sm"
                                required
                                placeholder="Label"
                                value={field.label}
                                onChange={(e) => updateField(idx, { label: e.target.value })}
                              />
                            </div>
                            <div className="col-md-3">
                              <label className="small text-muted mb-0">Data Type</label>
                              <select
                                className="form-control form-control-sm"
                                value={field.type}
                                onChange={(e) => updateField(idx, { type: e.target.value as SchemaField['type'] })}
                              >
                                <option value="string">String (Text)</option>
                                <option value="number">Number</option>
                                <option value="boolean">Boolean (True/False)</option>
                                <option value="date">Date</option>
                                <option value="enum">Enum (Option List)</option>
                              </select>
                            </div>
                            <div className="col-md-2 text-center">
                              <label className="small text-muted mb-0 d-block">Required</label>
                              <input
                                type="checkbox"
                                className="form-check-input mt-1"
                                checked={field.required}
                                onChange={(e) => updateField(idx, { required: e.target.checked })}
                              />
                            </div>
                            <div className="col-md-1 text-end">
                              <label className="small text-muted mb-0 d-block">&nbsp;</label>
                              <button
                                type="button"
                                className="btn btn-sm btn-icon btn-danger-outline"
                                onClick={() => removeField(idx)}
                                title="Remove field"
                              >
                                ✕
                              </button>
                            </div>
                          </div>

                          {field.type === 'enum' && (
                            <div className="mt-2 pt-2 border-top">
                              <label className="small text-muted mb-1">
                                Enum Options (comma-separated):
                              </label>
                              <input
                                type="text"
                                className="form-control form-control-sm"
                                placeholder="Option 1, Option 2, Option 3"
                                value={(field.options || []).join(', ')}
                                onChange={(e) =>
                                  updateField(idx, {
                                    options: e.target.value
                                      .split(',')
                                      .map((s) => s.trim())
                                      .filter(Boolean),
                                  })
                                }
                              />
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Saving Schema...' : editingSchemaId ? 'Update Schema' : 'Create Schema'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
