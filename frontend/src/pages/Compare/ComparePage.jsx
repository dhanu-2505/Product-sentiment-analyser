import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Plus, X } from 'lucide-react'
import CompactChartTooltip from '../../components/CompactChartTooltip'
import { compareProducts, getProducts } from '../../services/api'

const provenanceLabel = (value) => ({ seeded_demo: 'Seeded demo', live: 'Live', stored: 'Stored', mixed: 'Mixed', unavailable: 'Unavailable' }[value] || 'Unverified')

function ComparePage() {
  const [products, setProducts] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [pickerValue, setPickerValue] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [comparing, setComparing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getProducts()
      .then((response) => setProducts(response.data.items || []))
      .catch((requestError) => setError(requestError?.response?.data?.detail || 'Unable to load products for comparison.'))
      .finally(() => setLoading(false))
  }, [])

  const unselectedProducts = products.filter((product) => !selectedIds.includes(String(product.id)))
  const priceEvidence = useMemo(() => items.filter((item) => item.price_value > 0), [items])
  const ratedEvidence = useMemo(() => items.filter((item) => item.total_reviews > 0), [items])
  const lowestPrice = priceEvidence.length ? [...priceEvidence].sort((a, b) => a.price_value - b.price_value)[0] : null
  const highestRating = ratedEvidence.length ? [...ratedEvidence].sort((a, b) => b.average_rating - a.average_rating)[0] : null
  const largestReviewVolume = ratedEvidence.length ? [...ratedEvidence].sort((a, b) => b.total_reviews - a.total_reviews)[0] : null
  const aspects = [...new Set(items.flatMap((item) => Object.keys(item.aspect_sentiment || {})))].sort()

  const addProduct = () => {
    if (!pickerValue || selectedIds.length >= 4) return
    setSelectedIds((current) => [...current, pickerValue])
    setPickerValue('')
    setItems([])
  }

  const runComparison = async () => {
    setComparing(true)
    setError('')
    try {
      const response = await compareProducts({ product_ids: selectedIds.map(Number) })
      setItems(response.data.items || [])
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Unable to compare these products.')
      setItems([])
    } finally {
      setComparing(false)
    }
  }

  if (loading) return <main className="page"><div className="loading-grid"><div className="skeleton-line large" /><div className="skeleton-card" /></div></main>

  return (
    <main className="page">
      <header className="section-header"><div><p className="eyebrow muted">Evidence comparison</p><h2>Compare products</h2></div></header>

      <section className="table-panel">
        <div className="filter-row">
          <select className="select-field" value={pickerValue} onChange={(event) => setPickerValue(event.target.value)} aria-label="Choose a product">
            <option value="">Choose a product</option>
            {unselectedProducts.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
          </select>
          <button className="ghost-button" type="button" onClick={addProduct} disabled={!pickerValue || selectedIds.length >= 4}><Plus size={16} /> Add product</button>
          <button className="primary-button" type="button" onClick={runComparison} disabled={selectedIds.length < 2 || selectedIds.length > 4 || comparing}>{comparing ? 'Comparing...' : `Compare ${selectedIds.length} products`}</button>
        </div>
        {selectedIds.length > 0 && <div className="filter-row">{selectedIds.map((id) => {
          const product = products.find((item) => String(item.id) === id)
          return <span className="badge" key={id}>{product?.name || `Product ${id}`} <button className="icon-button" type="button" onClick={() => { setSelectedIds((current) => current.filter((value) => value !== id)); setItems([]) }} aria-label={`Remove ${product?.name || 'product'}`} title="Remove product"><X size={14} /></button></span>
        })}</div>}
        <p className="muted">Select 2–4 products. Ratings and sentiment retain their data provenance; no universal winner is assigned.</p>
      </section>
      {error && <div className="error-state" role="alert"><p>{error}</p></div>}

      {items.length === 0 ? <div className="empty-state"><h3>Choose products to compare</h3><p>Price, review volume, ratings, and aspects appear only when supported by records.</p></div> : <>
        <section className="table-panel">
          <h3>Purchase decision insights</h3>
          <ul>
            {lowestPrice ? <li>{lowestPrice.price_data_type === 'seeded_demo' ? 'Lowest seeded demo catalog price' : 'Lowest stored price'}: {lowestPrice.name} ({lowestPrice.price}). {lowestPrice.price_data_type === 'seeded_demo' ? 'This is not a current offer.' : ''}</li> : <li>Price comparison unavailable: no selected product has a recorded price.</li>}
            {highestRating ? <li>Highest recorded average rating: {highestRating.name} ({Number(highestRating.average_rating).toFixed(2)}/5), from {provenanceLabel(highestRating.review_data_type).toLowerCase()} reviews.</li> : <li>Rating comparison unavailable: no selected product has review data.</li>}
            {largestReviewVolume ? <li>Largest recorded review volume: {largestReviewVolume.name} ({largestReviewVolume.total_reviews}), from {provenanceLabel(largestReviewVolume.review_data_type).toLowerCase()} reviews.</li> : null}
            {aspects.length === 0 ? <li>Feature satisfaction cannot be compared because no aspect evidence is stored.</li> : <li>Aspect comparisons below use only detected review mentions.</li>}
          </ul>
        </section>

        <section className="dashboard-grid">
          <div className="chart-panel"><h4>Average rating</h4><div style={{ width: '100%', height: 280 }}><ResponsiveContainer><BarChart data={items}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis domain={[0, 5]} /><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} /><Bar dataKey="average_rating" fill="#60a5fa" isAnimationActive /></BarChart></ResponsiveContainer></div></div>
          <div className="chart-panel"><h4>Review volume</h4><div style={{ width: '100%', height: 280 }}><ResponsiveContainer><BarChart data={items}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} /><Bar dataKey="total_reviews" fill="#34d399" isAnimationActive /></BarChart></ResponsiveContainer></div></div>
        </section>

        <section className="table-panel"><div className="table-wrap"><table className="data-table">
          <thead><tr><th>Product</th><th>Price</th><th>Price data</th><th>Avg rating</th><th>Reviews</th><th>Review data</th><th>Positive</th><th>Neutral</th><th>Negative</th><th>Intelligence</th></tr></thead>
          <tbody>{items.map((item) => <tr key={item.id}>
            <td>{item.name}</td>
            <td>{item.price || 'Unavailable'}</td>
            <td>{provenanceLabel(item.price_data_type)}</td>
            <td>{item.total_reviews ? Number(item.average_rating || 0).toFixed(1) : 'Unavailable'}</td>
            <td>{item.total_reviews}</td>
            <td>{provenanceLabel(item.review_data_type)}</td>
            <td>{Number(item.positive_percentage || 0).toFixed(1)}%</td>
            <td>{Number(item.neutral_percentage || 0).toFixed(1)}%</td>
            <td>{Number(item.negative_percentage || 0).toFixed(1)}%</td>
            <td>{item.intelligence_score == null ? 'Unavailable' : Number(item.intelligence_score).toFixed(1)}</td>
          </tr>)}</tbody>
        </table></div></section>

        {aspects.length > 0 && <section className="table-panel"><h3>Aspect evidence</h3><div className="table-wrap"><table className="data-table"><thead><tr><th>Aspect</th>{items.map((item) => <th key={item.id}>{item.name}</th>)}</tr></thead><tbody>{aspects.map((aspect) => <tr key={aspect}><td>{aspect}</td>{items.map((item) => { const counts = item.aspect_sentiment?.[aspect]; const total = counts ? counts.positive + counts.neutral + counts.negative : 0; return <td key={item.id}>{total ? `${Math.round((counts.positive / total) * 100)}% positive (${total} mentions)` : 'No evidence'}</td> })}</tr>)}</tbody></table></div></section>}
      </>}
    </main>
  )
}

export default ComparePage
