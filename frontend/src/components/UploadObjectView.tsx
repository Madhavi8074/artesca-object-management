import React, { useState, useRef, useEffect } from 'react'
import { formatBytes } from '../utils/formatters'
import { ApiClient } from '../services/api'
import type { MetadataSchema, SchemaField } from '../types'

interface UploadObjectViewProps {
  onUpload: (formData: FormData) => Promise<void>
  loading: boolean
  onSuccess?: () => void
}

export const UploadObjectView: React.FC<UploadObjectViewProps> = ({
  onUpload,
  loading: parentLoading,
  onSuccess,
}) => {
  // Single File State
  const [file, setFile] = useState<File | null>(null)

  // Standard Metadata Form Fields
  const [bucket, setBucket] = useState('')
  const [buckets, setBuckets] = useState<Array<{ name: string }>>([])
  const [bucketsLoading, setBucketsLoading] = useState(true)
  const [bucketError, setBucketError] = useState<string | null>(null)

  const [objectKey, setObjectKey] = useState('')
  const [classification, setClassification] = useState('INTERNAL')
  const [department, setDepartment] = useState('Engineering')
  const [project, setProject] = useState('Artesca')
  const [documentType, setDocumentType] = useState('Technical Specification')
  const [author, setAuthor] = useState('')
  const [description, setDescription] = useState('')

  // Metadata Schemas
  const [schemas, setSchemas] = useState<MetadataSchema[]>([])
  const [selectedSchemaId, setSelectedSchemaId] = useState<number | ''>('')
  const [dynamicFormValues, setDynamicFormValues] = useState<Record<string, unknown>>({})
  const [schemaValidationErrors, setSchemaValidationErrors] = useState<string[]>([])

  // Raw Custom Metadata Editor
  const [customMetadata, setCustomMetadata] = useState(
    '{\n  "environment": "production",\n  "review_status": "approved"\n}',
  )
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  const singleFileInputRef = useRef<HTMLInputElement | null>(null)

  // Load available schemas on mount
  useEffect(() => {
  let cancelled = false

  const loadSchemas = async () => {
    try {
      const data = await ApiClient.listSchemas()

      if (!cancelled) {
        setSchemas(data.filter((schema) => schema.is_active))
      }
    } catch (err) {
      if (!cancelled) {
        console.error('Failed to load schemas:', err)
      }
    }
  }

  const loadBuckets = async () => {
  try {
    setBucketsLoading(true)
    setBucketError(null)

    const rawBuckets = await ApiClient.listBuckets()

    const normalizedBuckets = rawBuckets
      .map((item) => {
        if (typeof item === 'string') {
          return item
        }

        if (item && typeof item.name === 'string') {
          return item.name
        }

        return ''
      })
      .filter((name) => name.length > 0)

    if (cancelled) return

    setBuckets(normalizedBuckets.map((name) => ({ name })))

    const preferredBucket = normalizedBuckets.find(
      (name) => name === 'artesca-documents',
    )

    setBucket((current) => {
      if (current && normalizedBuckets.includes(current)) {
        return current
      }

      return preferredBucket ?? normalizedBuckets[0] ?? ''
    })

    if (normalizedBuckets.length === 0) {
      setBucketError('No accessible S3 buckets were found.')
    }
  } catch (err) {
    if (!cancelled) {
      setBucketError(
        err instanceof Error ? err.message : 'Failed to load S3 buckets.',
      )
    }
  } finally {
    if (!cancelled) {
      setBucketsLoading(false)
    }
  }
}  
void loadSchemas()
  void loadBuckets()

  return () => {
    cancelled = true
  }
}, [])



  // When schema changes, initialize dynamic fields
  const handleSchemaChange = (schemaIdStr: string) => {
    if (!schemaIdStr) {
      setSelectedSchemaId('')
      setDynamicFormValues({})
      setSchemaValidationErrors([])
      return
    }
    const id = Number(schemaIdStr)
    setSelectedSchemaId(id)
    const schema = schemas.find((s) => s.id === id)
    if (schema && schema.fields) {
      const initial: Record<string, unknown> = {}
      schema.fields.forEach((f) => {
        if (f.default !== undefined) {
          initial[f.name] = f.default
        } else if (f.type === 'boolean') {
          initial[f.name] = false
        } else if (f.type === 'enum' && f.options && f.options.length > 0) {
          initial[f.name] = f.options[0]
        } else {
          initial[f.name] = ''
        }
      })
      setDynamicFormValues(initial)
      // Also sync to custom metadata preview
      setCustomMetadata(JSON.stringify(initial, null, 2))
    }
  }

  const handleDynamicFieldChange = (fieldName: string, val: unknown) => {
    const next = { ...dynamicFormValues, [fieldName]: val }
    setDynamicFormValues(next)
    setCustomMetadata(JSON.stringify(next, null, 2))
  }

  const handleSingleFileSelection = (selectedFile: File) => {
    setFile(selectedFile)
    if (!objectKey) {
      setObjectKey(`uploads/${selectedFile.name}`)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => {
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSingleFileSelection(e.dataTransfer.files[0])
    }
  }

  // Submit Upload
  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setJsonError(null)
    setSchemaValidationErrors([])

    if (!file) {
      alert('Please select a file to upload.')
      return
    }

    if (!objectKey.trim()) {
      alert('Please enter an object key.')
      return
    }

    let parsedCustom: Record<string, unknown> | null = null
    if (customMetadata.trim()) {
      try {
        parsedCustom = JSON.parse(customMetadata)
        if (typeof parsedCustom !== 'object' || Array.isArray(parsedCustom)) {
          setJsonError('Custom metadata must be a JSON object (key-value pairs).')
          return
        }
      } catch (err) {
        setJsonError(`Invalid JSON: ${err instanceof Error ? err.message : String(err)}`)
        return
      }
    }

    // If schema selected, validate against engine
    if (selectedSchemaId && parsedCustom) {
      try {
        const valRes = await ApiClient.validateSchema(selectedSchemaId, parsedCustom)
        if (!valRes.is_valid) {
          setSchemaValidationErrors(valRes.errors)
          alert(`Schema validation failed:\n• ${valRes.errors.join('\n• ')}`)
          return
        }
      } catch (err) {
        console.warn('Schema validation warning:', err)
      }
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('bucket', bucket.trim())
    formData.append('object_key', objectKey.trim())
    if (classification) formData.append('classification', classification)
    if (department) formData.append('department', department)
    if (project) formData.append('project', project)
    if (documentType) formData.append('document_type', documentType)
    if (author) formData.append('author', author)
    if (description) formData.append('description', description)
    if (selectedSchemaId) formData.append('schema_id', String(selectedSchemaId))
    if (parsedCustom && Object.keys(parsedCustom).length > 0) {
      formData.append('custom_metadata', JSON.stringify(parsedCustom))
    }

    await onUpload(formData)

    // Reset single form
    setFile(null)
    setObjectKey('')
    setDescription('')
    if (singleFileInputRef.current) singleFileInputRef.current.value = ''
    if (onSuccess) onSuccess()
  }

  const selectedSchema = schemas.find((s) => s.id === selectedSchemaId)

  return (
    <div className="page-content">
      <div className="page-actions">
        <div>
          <h2>Upload Object & Index Metadata</h2>
          <p>Stream directly into Scality ARTESCA S3 storage with schema enforcement and JSONB indexing.</p>
        </div>
      </div>

      {schemaValidationErrors.length > 0 && (
        <div className="alert alert-danger mb-4">
          <strong>Schema Validation Issues Detected:</strong>
          <ul className="mb-0 mt-1 ps-3">
            {schemaValidationErrors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="upload-layout">
        <form onSubmit={handleSingleSubmit} className="section-card upload-main">
          <div className="section-header">
            <div>
              <h3>1. Select Source File</h3>
              <p>Drag and drop or browse from your computer</p>
            </div>
          </div>

          <div
            className="drop-zone"
            style={{
              borderColor: isDragOver ? 'var(--primary)' : undefined,
              backgroundColor: isDragOver ? 'var(--primary-light)' : undefined,
            }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => singleFileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={singleFileInputRef}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleSingleFileSelection(e.target.files[0])
                }
              }}
              style={{ display: 'none' }}
              id="file-upload-input"
            />
            {file ? (
              <div className="selected-file">
                <div className="large-file-icon">
                  {(file.name.split('.').pop() || 'FILE').toUpperCase().slice(0, 4)}
                </div>
                <div>
                  <strong>{file.name}</strong>
                  <span>{formatBytes(file.size)} &bull; {file.type || 'unknown type'}</span>
                </div>
              </div>
            ) : (
              <>
                <div className="upload-icon">☁️</div>
                <strong>Click to choose a file or drag & drop here</strong>
                <span>Supports documents, PDFs, images, data files, and archives up to 500 MB</span>
              </>
            )}
          </div>

          {/* Storage & Metadata Configuration */}
          <div className="section-header" style={{ borderTop: '1px solid var(--border)' }}>
            <div>
              <h3>2. Storage & Metadata Configuration</h3>
              <p>Define storage key, catalog attributes, and schema validation</p>
            </div>
          </div>

          <div className="form-grid">
            <label>
  Target S3 Bucket *
  <select
    required
    value={bucket}
    onChange={(e) => setBucket(e.target.value)}
    disabled={bucketsLoading || buckets.length === 0}
  >
    <option value="" disabled>
      {bucketsLoading
        ? 'Loading available buckets...'
        : 'Select an existing bucket'}
    </option>

    {buckets.map((item) => (
      <option key={item.name} value={item.name}>
        {item.name}
      </option>
    ))}
  </select>

  {bucketError && (
    <span
      role="alert"
      style={{
        color: 'var(--danger)',
        fontSize: '12px',
        marginTop: '4px',
      }}
    >
      {bucketError}
    </span>
  )}
</label>


            <label>
              Object Key (S3 Path) *
              <input
                type="text"
                required
                value={objectKey}
                onChange={(e) => setObjectKey(e.target.value)}
                placeholder="uploads/filename.ext"
              />
            </label>

            <label>
              Metadata Schema Template
              <select
                value={selectedSchemaId}
                onChange={(e) => handleSchemaChange(e.target.value)}
              >
                <option value="">No Schema (Ad-hoc Custom Metadata)</option>
                {schemas.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} (v{s.version}) - {s.fields?.length || 0} fields
                  </option>
                ))}
              </select>
            </label>

            <label>
              Data Classification
              <select
                value={classification}
                onChange={(e) => setClassification(e.target.value)}
              >
                <option value="PUBLIC">PUBLIC</option>
                <option value="INTERNAL">INTERNAL</option>
                <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                <option value="RESTRICTED">RESTRICTED</option>
              </select>
            </label>

            <label>
              Department
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="Engineering, Legal, Finance..."
              />
            </label>

            <label>
              Project
              <input
                type="text"
                value={project}
                onChange={(e) => setProject(e.target.value)}
                placeholder="Project Name or Code"
              />
            </label>

            <label>
              Document Type
              <input
                type="text"
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                placeholder="Contract, Report, Spec..."
              />
            </label>

            <label>
              Author / Owner
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="Author Name"
              />
            </label>

            {/* Dynamic Schema Form Fields if Schema Selected */}
            {selectedSchema && selectedSchema.fields && selectedSchema.fields.length > 0 && (
              <div className="full-width p-3 border rounded bg-light mb-3">
                <h4 className="h6 fw-bold text-primary mb-2">
                  Enforced Schema Fields: {selectedSchema.name}
                </h4>
                <div className="row g-2">
                  {selectedSchema.fields.map((f: SchemaField) => (
                    <div key={f.name} className="col-md-6">
                      <label className="form-label small fw-bold mb-1">
                        {f.label} {f.required && <span className="text-danger">*</span>}
                      </label>
                      {f.type === 'enum' && f.options ? (
                        <select
                          className="form-control form-control-sm"
                          value={String(dynamicFormValues[f.name] || '')}
                          onChange={(e) => handleDynamicFieldChange(f.name, e.target.value)}
                          required={f.required}
                        >
                          <option value="">-- Select {f.label} --</option>
                          {f.options.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      ) : f.type === 'boolean' ? (
                        <div className="form-check mt-1">
                          <input
                            className="form-check-input"
                            type="checkbox"
                            id={`dyn_${f.name}`}
                            checked={Boolean(dynamicFormValues[f.name])}
                            onChange={(e) => handleDynamicFieldChange(f.name, e.target.checked)}
                          />
                          <label className="form-check-label small" htmlFor={`dyn_${f.name}`}>
                            Enable / Yes
                          </label>
                        </div>
                      ) : f.type === 'number' ? (
                        <input
                          type="number"
                          className="form-control form-control-sm"
                          required={f.required}
                          value={Number(dynamicFormValues[f.name] ?? '')}
                          onChange={(e) => handleDynamicFieldChange(f.name, Number(e.target.value))}
                        />
                      ) : f.type === 'date' ? (
                        <input
                          type="date"
                          className="form-control form-control-sm"
                          required={f.required}
                          value={String(dynamicFormValues[f.name] || '')}
                          onChange={(e) => handleDynamicFieldChange(f.name, e.target.value)}
                        />
                      ) : (
                        <input
                          type="text"
                          className="form-control form-control-sm"
                          required={f.required}
                          placeholder={f.description || f.label}
                          value={String(dynamicFormValues[f.name] || '')}
                          onChange={(e) => handleDynamicFieldChange(f.name, e.target.value)}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <label className="full-width">
              Description / Notes
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Enter summary or notes regarding this object..."
              />
            </label>

            <label className="full-width">
              <span>Custom Metadata JSON (PostgreSQL JSONB Indexed)</span>
              <textarea
                rows={4}
                value={customMetadata}
                onChange={(e) => {
                  setCustomMetadata(e.target.value)
                  setJsonError(null)
                }}
                placeholder='{"project_code": "PRJ-9001"}'
                style={{
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  borderColor: jsonError ? 'var(--danger)' : undefined,
                }}
              />
              {jsonError && (
                <span style={{ color: 'var(--danger)', fontSize: '11px', marginTop: '4px' }}>
                  {jsonError}
                </span>
              )}
            </label>
          </div>

          <div className="form-actions" style={{ padding: '0 22px 22px' }}>
            <button
              type="submit"
              className="primary-button"
              disabled={
  parentLoading ||
  !file ||
  !bucket ||
  bucketsLoading ||
  buckets.length === 0
}

              id="submit-upload-btn"
            >
              {parentLoading ? 'Uploading & Indexing...' : '🚀 Upload & Index Object'}
            </button>
          </div>
        </form>

        {/* Live Summary Card */}
        <aside className="upload-summary">
          <div className="summary-card">
            <h3>Ingestion Summary</h3>
            <div className="summary-row">
              <span>File to Ingest</span>
              <strong>{file ? file.name : '0 selected'}</strong>
            </div>

            <div className="summary-row">
              <span>Target S3 Bucket</span>
              <strong>s3://{bucket}</strong>
            </div>

            <div className="summary-row">
              <span>Active Schema</span>
              <strong>{selectedSchema ? selectedSchema.name : 'None (Ad-hoc)'}</strong>
            </div>

            <div className="summary-row">
              <span>Classification</span>
              <strong style={{ color: 'var(--primary)' }}>{classification}</strong>
            </div>

            <div className="summary-row">
              <span>Department</span>
              <strong>{department || 'Unassigned'}</strong>
            </div>
          </div>

          <div
            className="summary-card"
            style={{ marginTop: '16px', background: 'var(--surface-soft)' }}
          >
            <h3 style={{ fontSize: '13px' }}>⚡ Schema & JSONB Engine</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Objects are streamed directly to Scality ARTESCA S3 storage. Metadata attributes and custom JSON
              are indexed into PostgreSQL JSONB with GIN indexing for sub-millisecond query evaluation.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}
  