import { configureStore, createSlice } from '@reduxjs/toolkit'

const initialFormState = {
  customer_name: '',
  complaint_source: '',
  product_name: '',
  product_strength: '',
  batch_lot_number: '',
  manufacturing_date: '',
  expiry_date: '',
  quantity_affected: '',
  complaint_type: '',
  complaint_date: '',
  detailed_description: '',
  initial_severity: '',
  priority: '',
}

const complaintSlice = createSlice({
  name: 'complaint',
  initialState: {
    form: initialFormState,
    ai: {
      risk_classification: '',
      ai_summary: '',
      capa_recommendation: '',
      completeness_score: 0,
      completeness_feedback: '',
      root_cause: '',
    },
    loading: false,
    progress: 0,
    progressMessage: '',
    error: null,
    savedId: null,
  },
  reducers: {
    setField: (state, action) => {
      const { field, value } = action.payload
      state.form[field] = value
    },
    setForm: (state, action) => {
      state.form = { ...state.form, ...action.payload }
    },
    setAI: (state, action) => {
      state.ai = { ...state.ai, ...action.payload }
    },
    setLoading: (state, action) => {
      state.loading = action.payload
    },
    setProgress: (state, action) => {
      state.progress = action.payload.progress
      state.progressMessage = action.payload.message || ''
    },
    setError: (state, action) => {
      state.error = action.payload
    },
    setSavedId: (state, action) => {
      state.savedId = action.payload
    },
    resetForm: (state) => {
      state.form = initialFormState
      state.ai = {
        risk_classification: '',
        ai_summary: '',
        capa_recommendation: '',
        completeness_score: 0,
        completeness_feedback: '',
        root_cause: '',
      }
      state.loading = false
      state.progress = 0
      state.progressMessage = ''
      state.error = null
      state.savedId = null
    },
  },
})

export const {
  setField,
  setForm,
  setAI,
  setLoading,
  setProgress,
  setError,
  setSavedId,
  resetForm,
} = complaintSlice.actions

export const store = configureStore({
  reducer: {
    complaint: complaintSlice.reducer,
  },
})
