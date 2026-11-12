import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Download, FileBarChart2, FileSpreadsheet, RefreshCw } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { downloadReport, exportCsv, generateReport, getProducts, getReport, getReports } from '../../services/api'

const EXPORTS = [
  ['products', 'Product data'], ['reviews', 'Reviews'], ['sentiments', 'Sentiment data'],
  ['aspects', 'Aspect analysis'], ['prices', 'Price observations'], ['comparison', 'Source comparison'],
  ['search_history', 'Search history'], ['analytics', 'Analytics summary'],
]

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function ReportsPage() {
  const { token } = useAuth()
  const [searchParams] = useSearchParams()
  const [products, setProducts] = useState([])
  const [reports, setReports] = useState([])
  const [productId, setProductId] = useState(searchParams.get('productId') || '')
  const [selectedReport, setSelectedReport] = useState(null)
  const [sourceFilter, setSourceFilter] = useState('')
  const [sentimentFilter, setSentimentFilter] = useState('')
  const [provenanceFilter, setProvenanceFilter] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const refresh = async () => {
    const [productResponse, reportResponse] = await Promise.all([getProducts(), getReports(token)])
    const productItems = productResponse.data.items || []
    setProducts(productItems)
    setReports(reportResponse.data.items || [])
    setProductId((current) => current || searchParams.get('productId') || String(productItems[0]?.id || ''))
  }

  useEffect(() => {
    refresh().catch((requestError) => setError(requestError?.response?.data?.detail || 'Unable to load reports.'))
  }, [token])

  const openReport = async (reportId) => {
    setBusy(true)
    setError('')
    try {
      const response = await getReport(reportId, token)
      setSelectedReport(response.data)
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Unable to open this report.')
    } finally {
      setBusy(false)
    }
  }

  const createProductReport = async () => {
    if (!productId) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const response = await generateReport({ product_id: Number(productId), report_type: 'product_intelligence' }, token)
      setSelectedReport(response.data)
      await refresh()
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Report generation failed.')
    } finally {
      setBusy(false)
    }
  }

  const downloadPdf = async (reportId) => {
    setBusy(true)
    setError('')
    try {
      const response = await downloadReport(reportId, token)
      downloadBlob(response.data, `reviewlens-report-${reportId}.pdf`)
      setNotice('PDF downloaded.')
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'PDF is not available for this report.')
    } finally {
      setBusy(false)
    }
  }

  const downloadCsv = async (dataType) => {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const params = productId ? { product_id: Number(productId) } : {}
      if (['reviews', 'sentiments', 'aspects'].includes(dataType)) {
        if (sourceFilter) params.source = sourceFilter
        if (sentimentFilter) params.sentiment = sentimentFilter
        if (provenanceFilter) params.provenance = provenanceFilter
      }
      if (['reviews', 'sentiments', 'aspects', 'prices', 'comparison', 'search_history'].includes(dataType)) {
        if (startDate) params.start_date = `${startDate}T00:00:00`
        if (endDate) params.end_date = `${endDate}T23:59:59`
      }
      if (['prices', 'comparison'].includes(dataType) && sourceFilter) params.source = sourceFilter
      if (['prices', 'comparison'].includes(dataType) && provenanceFilter) params.provenance = provenanceFilter
      const response = await exportCsv(dataType, params, token)
      downloadBlob(response.data, `reviewlens-${dataType}.csv`)
      setNotice(`${dataType.replaceAll('_', ' ')} CSV downloaded.`)
    } catch (requestError) {
      const blob = requestError?.response?.data
      const message = blob instanceof Blob ? await blob.text() : ''
      let detail = requestError?.response?.data?.detail || 'No matching data to export.'
      if (message) {
        try { detail = JSON.parse(message).detail || detail } catch { /* keep the readable fallback */ }
      }
      setError(detail)
    } finally {
      setBusy(false)
    }
  }

  const content = selectedReport?.content || {}
  const overview = content.product_overview || {}
  const summary = content.summary || {}

  return (
    <main className="page">
      <header className="section-header">
        <div><p className="eyebrow muted">Reports & exports</p><h2>Product intelligence center</h2></div>
        <button className="ghost-button" type="button" onClick={() => refresh().catch(() => setError('Unable to refresh reports.'))} disabled={busy} title="Refresh reports"><RefreshCw size={16} /> Refresh</button>
      </header>
      {error && <div className="error-state" role="alert"><p>{error}</p></div>}
      {notice && <p className="success-message" role="status">{notice}</p>}

      <section className="table-panel">
        <div className="section-header"><div><p className="eyebrow muted">Generate</p><h3>New product report</h3></div></div>
        <div className="filter-row">
          <select className="select-field" value={productId} onChange={(event) => setProductId(event.target.value)} aria-label="Select product">
            <option value="">Select a product</option>
            {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
          </select>
          <button className="primary-button" type="button" onClick={createProductReport} disabled={busy || !productId}><FileBarChart2 size={16} /> Generate report</button>
        </div>
      </section>

      <section className="table-panel">
        <div className="section-header"><div><p className="eyebrow muted">Persisted reports</p><h3>Reports you generated</h3></div></div>
        {reports.length === 0 ? <p className="empty-state">No reports have been generated for this account.</p> : (
          <div className="table-wrap"><table className="data-table">
            <thead><tr><th>Report</th><th>Type</th><th>Created</th><th>Actions</th></tr></thead>
            <tbody>{reports.map((report) => (
              <tr key={report.id}>
                <td><button className="text-button" type="button" onClick={() => openReport(report.id)}>{report.product_name} intelligence</button></td>
                <td>{report.report_type}</td>
                <td>{report.created_at ? new Date(report.created_at).toLocaleString() : 'Unknown'}</td>
                <td className="action-row">
                  <button className="icon-button" type="button" onClick={() => openReport(report.id)} aria-label="Open report" title="Open report"><FileBarChart2 size={16} /></button>
                  <button className="icon-button" type="button" onClick={() => downloadPdf(report.id)} disabled={busy || !report.file_path} aria-label="Download PDF" title={report.file_path ? 'Download PDF' : 'PDF unavailable'}><Download size={16} /></button>
                </td>
              </tr>
            ))}</tbody>
          </table></div>
        )}
      </section>

      {selectedReport && <section className="table-panel" aria-live="polite">
        <div className="section-header"><div><p className="eyebrow muted">Report detail</p><h3>{overview.name || selectedReport.product_name}</h3></div><button className="icon-button" type="button" onClick={() => setSelectedReport(null)} aria-label="Close report detail" title="Close report detail">×</button></div>
        <p>{overview.brand || 'Brand unavailable'} · {overview.category || 'Category unavailable'} · {overview.price || 'Price unavailable'}</p>
        <div className="kpi-grid">
          <div className="kpi-card"><span className="label">Reviews</span><strong>{summary.total_reviews ?? 'Unavailable'}</strong></div>
          <div className="kpi-card"><span className="label">Average rating</span><strong>{summary.average_rating ?? 'Unavailable'}</strong></div>
          <div className="kpi-card"><span className="label">Positive</span><strong>{summary.positive_percentage ?? 'Unavailable'}%</strong></div>
          <div className="kpi-card"><span className="label">Negative</span><strong>{summary.negative_percentage ?? 'Unavailable'}%</strong></div>
        </div>
        <h4>Product intelligence</h4><pre className="report-json">{JSON.stringify(content.intelligence || {}, null, 2)}</pre>
        <h4>Source comparison</h4><pre className="report-json">{JSON.stringify(content.source_comparison || [], null, 2)}</pre>
        <h4>Price history</h4>{content.price_history?.length ? <pre className="report-json">{JSON.stringify(content.price_history, null, 2)}</pre> : <p>Insufficient historical price data.</p>}
        <h4>Aspect analysis</h4><pre className="report-json">{JSON.stringify(content.aspect_analysis || {}, null, 2)}</pre>
        <h4>Review quality signals</h4><p>{content.review_quality?.summary || 'Insufficient review data.'}</p><pre className="report-json">{JSON.stringify(content.review_quality?.signals || [], null, 2)}</pre>
        <h4>Sentiment history</h4>{content.sentiment_history?.length ? <pre className="report-json">{JSON.stringify(content.sentiment_history, null, 2)}</pre> : <p>Insufficient stored sentiment history.</p>}
        <h4>Representative reviews</h4><ul>{(content.top_reviews || []).map((review) => <li key={review.review_id}>{review.rating}/5 · {review.sentiment || 'unscored'} · {review.data_type}: {review.review_text}</li>)}</ul>
        <h4>Top praises</h4><ul>{(content.customer_praises || []).map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
        <h4>Top complaints</h4><ul>{(content.customer_complaints || []).map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul>
        <h4>Data provenance</h4><pre className="report-json">{JSON.stringify(content.data_provenance || {}, null, 2)}</pre>
      </section>}

      <section className="table-panel">
        <div className="section-header"><div><p className="eyebrow muted">Data export</p><h3>Download CSV</h3></div><FileSpreadsheet size={20} /></div>
        <div className="filter-row">
          <select className="select-field" value={productId} onChange={(event) => setProductId(event.target.value)} aria-label="Filter export by product">
            <option value="">All products</option>
            {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
          </select>
          <select className="select-field" value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)} aria-label="Filter export by source">
            <option value="">All sources</option>
            <option value="amazon">Amazon</option>
            <option value="flipkart">Flipkart</option>
          </select>
          <select className="select-field" value={sentimentFilter} onChange={(event) => setSentimentFilter(event.target.value)} aria-label="Filter export by sentiment">
            <option value="">All sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </select>
          <select className="select-field" value={provenanceFilter} onChange={(event) => setProvenanceFilter(event.target.value)} aria-label="Filter export by data provenance">
            <option value="">All provenance</option>
            <option value="live_scraped">Live scraped</option>
            <option value="stored">Stored</option>
            <option value="seeded_demo">Seeded demo</option>
          </select>
          <label className="auth-field"><span>From</span><input className="field" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
          <label className="auth-field"><span>To</span><input className="field" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
          {EXPORTS.map(([dataType, label]) => <button key={dataType} className="ghost-button" type="button" onClick={() => downloadCsv(dataType)} disabled={busy}>{label} CSV</button>)}
        </div>
      </section>
    </main>
  )
}

export default ReportsPage
