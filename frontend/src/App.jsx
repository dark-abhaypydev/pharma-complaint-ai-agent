import React, { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { setField, setForm, setAI, setLoading, setProgress, setError, setSavedId, resetForm } from './store'
import { extractComplaint, saveComplaint, listComplaints } from './services/api'
import './App.css'

function App() {
  const dispatch = useDispatch()
  const { form, ai, loading, progress, progressMessage, error, savedId } = useSelector((s) => s.complaint)
  const [pasteText, setPasteText] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [duplicateMsg, setDuplicateMsg] = useState('')
  const fileInputRef = React.useRef(null)

  const handleFieldChange = (field, value) => {
    dispatch(setField({ field, value }))
  }

  const runExtraction = async ({ file, text }) => {
    dispatch(setLoading(true))
    dispatch(setError(null))
    setDuplicateMsg('')
    dispatch(setProgress({ progress: 15, message: 'Reading document...' }))

    try {
      const stages = [
        { p: 35, m: 'Extracting fields with AI...' },
        { p: 55, m: 'Risk & completeness analysis...' },
        { p: 75, m: 'Generating CAPA & root cause...' },
        { p: 90, m: 'Checking duplicates...' },
      ]
      let i = 0
      const interval = setInterval(() => {
        if (i < stages.length) {
          dispatch(setProgress(stages[i]))
          i++
        }
      }, 700)

      const data = await extractComplaint({ file, text })
      clearInterval(interval)

      const extracted = data.extracted || {}
      dispatch(setForm({
        customer_name: extracted.customer_name || '',
        complaint_source: extracted.complaint_source || '',
        product_name: extracted.product_name || '',
        product_strength: extracted.product_strength || '',
        batch_lot_number: extracted.batch_lot_number || '',
        manufacturing_date: extracted.manufacturing_date || '',
        expiry_date: extracted.expiry_date || '',
        quantity_affected: extracted.quantity_affected || '',
        complaint_type: extracted.complaint_type || '',
        complaint_date: extracted.complaint_date || '',
        detailed_description: extracted.detailed_description || '',
        initial_severity: extracted.initial_severity || '',
        priority: extracted.priority || '',
      }))

      dispatch(setAI({
        risk_classification: data.risk_classification || '',
        ai_summary: data.ai_summary || '',
        capa_recommendation: data.capa_recommendation || '',
        completeness_score: data.completeness_score || 0,
        completeness_feedback: data.completeness_feedback || '',
        root_cause: data.root_cause || '',
      }))

      // Simple duplicate check (client side demo)
      if (extracted.batch_lot_number) {
        try {
          const list = await listComplaints()
          const dup = list.find(c => c.batch_lot_number === extracted.batch_lot_number)
          if (dup) {
            setDuplicateMsg(`Possible duplicate found (ID: ${dup.id}) for same Batch ${extracted.batch_lot_number}`)
          } else {
            setDuplicateMsg('No duplicate found for this batch.')
          }
        } catch {
          setDuplicateMsg('')
        }
      }

      dispatch(setProgress({ progress: 100, message: 'Done!' }))
    } catch (err) {
      dispatch(setError(err.response?.data?.detail || err.message || 'Extraction failed'))
      dispatch(setProgress({ progress: 0, message: '' }))
    } finally {
      dispatch(setLoading(false))
    }
  }

  const handleFile = (file) => {
    if (file) runExtraction({ file })
  }

  const handleSave = async () => {
    try {
      dispatch(setLoading(true))
      const payload = {
        ...form,
        risk_classification: ai.risk_classification,
        ai_summary: ai.ai_summary,
        capa_recommendation: ai.capa_recommendation,
        completeness_score: ai.completeness_score,
        root_cause: ai.root_cause,
      }
      const res = await saveComplaint(payload)
      dispatch(setSavedId(res.id))
      alert(`Complaint saved! ID: ${res.id}`)
    } catch (err) {
      dispatch(setError(err.response?.data?.detail || 'Save failed'))
    } finally {
      dispatch(setLoading(false))
    }
  }

  const loadHistory = async () => {
    try {
      const data = await listComplaints()
      setHistory(data)
      setShowHistory(true)
    } catch {
      setHistory([])
    }
  }

  const riskClass = (val = '') => {
    const v = val.toLowerCase()
    if (v.includes('critical')) return 'risk-critical'
    if (v.includes('major')) return 'risk-major'
    if (v.includes('minor')) return 'risk-minor'
    return ''
  }

  return (
    <div className="app-shell">
      {/* Top Bar */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">A</div>
          <div>
            <h1>AIVOA QMS</h1>
            <span>Customer Complaint Intelligence</span>
          </div>
        </div>
        <div className="top-actions">
          <button className="ghost-btn" onClick={loadHistory}>History</button>
          <button className="ghost-btn" onClick={() => dispatch(resetForm())}>New Complaint</button>
        </div>
      </header>

      <div className="workspace">
        {/* LEFT - Intake */}
        <aside className="intake-panel">
          <div className="panel-title">
            <h2>AI Intake</h2>
            <span className="pill">Live</span>
          </div>

          <div
            className={`upload-zone ${dragOver ? 'active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragOver(false)
              handleFile(e.dataTransfer.files[0])
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="upload-icon">↑</div>
            <p>Drop PDF / DOCX / TXT here</p>
            <span>or click to browse</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.eml"
              hidden
              onChange={(e) => handleFile(e.target.files[0])}
            />
          </div>

          <div className="divider-text">or paste text</div>

          <textarea
            className="paste-box"
            rows={6}
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder="Paste complaint email or text..."
          />

          <button
            className="primary-btn full"
            onClick={() => runExtraction({ text: pasteText })}
            disabled={loading || !pasteText.trim()}
          >
            {loading ? 'Analyzing...' : 'Run AI Extraction'}
          </button>

          {loading && (
            <div className="progress-wrap">
              <div className="progress-track">
                <div className="progress-bar" style={{ width: `${progress}%` }} />
              </div>
              <span>{progressMessage} {progress}%</span>
            </div>
          )}

          {error && <div className="alert error">{error}</div>}
          {duplicateMsg && <div className="alert info">{duplicateMsg}</div>}

          {/* AI Insights */}
          {(ai.risk_classification || ai.ai_summary) && (
            <div className="insights">
              <h3>AI Insights</h3>

              <div className="insight-row">
                <span>Risk</span>
                <span className={`risk-badge ${riskClass(ai.risk_classification)}`}>
                  {ai.risk_classification}
                </span>
              </div>

              <div className="insight-row">
                <span>Completeness</span>
                <span>{ai.completeness_score}% — {ai.completeness_feedback}</span>
              </div>

              {ai.ai_summary && (
                <div className="insight-block">
                  <strong>Summary</strong>
                  <p>{ai.ai_summary}</p>
                </div>
              )}

              {ai.root_cause && (
                <div className="insight-block">
                  <strong>Root Cause</strong>
                  <pre>{ai.root_cause}</pre>
                </div>
              )}

              {ai.capa_recommendation && (
                <div className="insight-block">
                  <strong>CAPA Suggestion</strong>
                  <pre>{ai.capa_recommendation}</pre>
                </div>
              )}
            </div>
          )}
        </aside>

        {/* RIGHT - Form */}
        <main className="form-panel">
          <div className="panel-title">
            <h2>Log Complaint</h2>
            <span className="status-chip">Triage</span>
          </div>

          <div className="form-grid">
            <div className="field">
              <label>Complaint Source</label>
              <input value={form.complaint_source} onChange={(e) => handleFieldChange('complaint_source', e.target.value)} />
            </div>
            <div className="field">
              <label>Customer Name</label>
              <input value={form.customer_name} onChange={(e) => handleFieldChange('customer_name', e.target.value)} />
            </div>

            <div className="field">
              <label>Product Name</label>
              <input value={form.product_name} onChange={(e) => handleFieldChange('product_name', e.target.value)} />
            </div>
            <div className="field">
              <label>Strength / Grade</label>
              <input value={form.product_strength} onChange={(e) => handleFieldChange('product_strength', e.target.value)} />
            </div>

            <div className="field">
              <label>Batch / Lot No.</label>
              <input value={form.batch_lot_number} onChange={(e) => handleFieldChange('batch_lot_number', e.target.value)} />
            </div>
            <div className="field">
              <label>Qty Affected</label>
              <input value={form.quantity_affected} onChange={(e) => handleFieldChange('quantity_affected', e.target.value)} />
            </div>

            <div className="field">
              <label>Mfg Date</label>
              <input value={form.manufacturing_date} onChange={(e) => handleFieldChange('manufacturing_date', e.target.value)} />
            </div>
            <div className="field">
              <label>Expiry Date</label>
              <input value={form.expiry_date} onChange={(e) => handleFieldChange('expiry_date', e.target.value)} />
            </div>

            <div className="field">
              <label>Complaint Type</label>
              <input value={form.complaint_type} onChange={(e) => handleFieldChange('complaint_type', e.target.value)} />
            </div>
            <div className="field">
              <label>Complaint Date</label>
              <input value={form.complaint_date} onChange={(e) => handleFieldChange('complaint_date', e.target.value)} />
            </div>

            <div className="field">
              <label>Severity</label>
              <input value={form.initial_severity} onChange={(e) => handleFieldChange('initial_severity', e.target.value)} />
            </div>
            <div className="field">
              <label>Priority</label>
              <input value={form.priority} onChange={(e) => handleFieldChange('priority', e.target.value)} />
            </div>

            <div className="field full">
              <label>Detailed Description</label>
              <textarea
                rows={4}
                value={form.detailed_description}
                onChange={(e) => handleFieldChange('detailed_description', e.target.value)}
              />
            </div>
          </div>

          <div className="form-footer">
            <button className="ghost-btn" onClick={() => dispatch(resetForm())}>Reset</button>
            <button className="primary-btn" onClick={handleSave} disabled={loading}>
              Save Complaint
            </button>
          </div>

          {savedId && <p className="save-ok">Saved successfully • ID {savedId}</p>}
        </main>
      </div>

      {/* History Drawer */}
      {showHistory && (
        <div className="drawer-overlay" onClick={() => setShowHistory(false)}>
          <div className="drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-head">
              <h3>Recent Complaints</h3>
              <button onClick={() => setShowHistory(false)}>✕</button>
            </div>
            <div className="drawer-body">
              {history.length === 0 && <p className="muted">No complaints yet</p>}
              {history.map((c) => (
                <div key={c.id} className="history-item">
                  <div>
                    <strong>#{c.id}</strong> {c.customer_name || '—'}
                  </div>
                  <div className="muted">{c.product_name} • {c.batch_lot_number}</div>
                  <div className={`risk-badge ${riskClass(c.risk_classification)}`}>
                    {c.risk_classification || '—'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App