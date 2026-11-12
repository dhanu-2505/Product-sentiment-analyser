import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import CompactChartTooltip from './CompactChartTooltip'
import { getAnalytics, getProductReviews, getProductSources, getProducts, getReviewQuality, compareProducts } from '../services/api'
import { prioritizeSources, sourceCategoryLabel } from './SourceSelector'

const TRUSTED_TYPES = new Set(['live', 'live_scraped', 'stored', 'seeded_demo'])
const FACTOR_WEIGHTS = {
  price: 18,
  sentiment: 20,
  rating: 20,
  reviewVolume: 12,
  reviewQuality: 5,
  aspects: 10,
  historicalPrice: 5,
  sentimentConsistency: 5,
  availability: 3,
  freshness: 2,
}
const HISTORY_COLORS = ['#34d399', '#60a5fa', '#fbbf24', '#f87171', '#a78bfa']

const displayType = (value) => value === 'live_scraped' ? 'live' : value || 'unavailable'
const normalizeText = (value) => String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '')

function matchingSourceReviews(reviews, source) {
  const keys = [normalizeText(source.code), normalizeText(source.name), normalizeText(source.source_name)]
    .filter(Boolean)
  return reviews.filter((review) => {
    const reviewSource = normalizeText(review.source)
    const reviewType = displayType(review.data_type)
    return keys.some((key) => reviewSource === key || (key.length >= 5 && reviewSource.startsWith(key))) && TRUSTED_TYPES.has(reviewType)
  })
}

function buildStoreRows(registry, observations, reviews) {
  const observationMap = new Map((observations || []).map((source) => [source.source, source]))

  return registry.map((registeredSource) => {
    const observedSource = observationMap.get(registeredSource.code) || {}
    const sourceReviews = matchingSourceReviews(reviews, { ...registeredSource, ...observedSource })
    const sourceTypes = new Set()
    const hasObservedFields = [observedSource.price, observedSource.rating, observedSource.review_count, observedSource.availability]
      .some((value) => value !== null && value !== undefined)
    const observedType = displayType(observedSource.status)
    const priceHistory = (Array.isArray(observedSource.price_history) ? observedSource.price_history : [])
      .filter((point) => point.price != null && point.observed_at && point.currency && TRUSTED_TYPES.has(displayType(point.data_type)))

    if (hasObservedFields && TRUSTED_TYPES.has(observedType)) sourceTypes.add(observedType)
    sourceReviews.forEach((review) => sourceTypes.add(displayType(review.data_type)))
    if (priceHistory.length >= 2) priceHistory.forEach((point) => sourceTypes.add(displayType(point.data_type)))

    const ratings = sourceReviews.map((review) => Number(review.rating)).filter(Number.isFinite)
    const qualityScores = sourceReviews.map((review) => Number(review.quality_score)).filter(Number.isFinite)
    const verifiedShare = sourceReviews.length
      ? (sourceReviews.filter((review) => review.verified_purchase).length / sourceReviews.length) * 100
      : null
    const averageReviewQuality = qualityScores.length
      ? qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length
      : null
    const sentiments = sourceReviews.reduce((counts, review) => {
      if (Object.hasOwn(counts, review.sentiment)) counts[review.sentiment] += 1
      return counts
    }, { positive: 0, neutral: 0, negative: 0 })
    const sentimentTotal = sentiments.positive + sentiments.neutral + sentiments.negative
    const aspectCounts = {}
    const ratingDistribution = { star1: 0, star2: 0, star3: 0, star4: 0, star5: 0 }
    const sentimentByMonth = new Map()

    sourceReviews.forEach((review) => {
      const rating = Math.round(Number(review.rating))
      if (rating >= 1 && rating <= 5) ratingDistribution[`star${rating}`] += 1
      if (!review.review_date || !Object.hasOwn(sentiments, review.sentiment)) return
      const month = String(review.review_date).slice(0, 7)
      const counts = sentimentByMonth.get(month) || { positive: 0, total: 0 }
      counts.total += 1
      if (review.sentiment === 'positive') counts.positive += 1
      sentimentByMonth.set(month, counts)
    })

    sourceReviews.forEach((review) => {
      ;(Array.isArray(review.aspects) ? review.aspects : []).forEach((aspect) => {
        if (!aspect?.aspect || !['positive', 'neutral', 'negative'].includes(aspect.sentiment)) return
        const item = aspectCounts[aspect.aspect] || { positive: 0, neutral: 0, negative: 0 }
        item[aspect.sentiment] += 1
        aspectCounts[aspect.aspect] = item
      })
    })

    const aspectMentions = Object.values(aspectCounts).reduce((sum, item) => sum + item.positive + item.neutral + item.negative, 0)
    const ratingSpread = ratings.length > 1
      ? Math.sqrt(ratings.reduce((sum, rating) => sum + ((rating - ratings.reduce((total, value) => total + value, 0) / ratings.length) ** 2), 0) / ratings.length)
      : null
    const monthlyPositiveShares = [...sentimentByMonth.values()]
      .filter((month) => month.total >= 2)
      .map((month) => (month.positive / month.total) * 100)
    const meanMonthlyPositive = monthlyPositiveShares.length
      ? monthlyPositiveShares.reduce((sum, value) => sum + value, 0) / monthlyPositiveShares.length
      : 0
    const monthlyPositiveSpread = monthlyPositiveShares.length > 1
      ? Math.sqrt(monthlyPositiveShares.reduce((sum, value) => sum + ((value - meanMonthlyPositive) ** 2), 0) / monthlyPositiveShares.length)
      : null
    const hasEvidence = hasObservedFields || sourceReviews.length > 0
    const price = hasObservedFields ? observedSource.price : null
    const rating = hasObservedFields && observedSource.rating != null
      ? Number(observedSource.rating)
      : ratings.length ? ratings.reduce((sum, value) => sum + value, 0) / ratings.length : null
    const reviewCount = hasObservedFields && observedSource.review_count != null
      ? Number(observedSource.review_count)
      : sourceReviews.length || null
    const positivePercentage = sentimentTotal ? (sentiments.positive / sentimentTotal) * 100 : null
    const neutralPercentage = sentimentTotal ? (sentiments.neutral / sentimentTotal) * 100 : null
    const negativePercentage = sentimentTotal ? (sentiments.negative / sentimentTotal) * 100 : null
    const positiveAspectShare = aspectMentions
      ? ((Object.values(aspectCounts).reduce((sum, item) => sum + item.positive + item.neutral * 0.5, 0)) / aspectMentions) * 100
      : null
    const observedAt = hasObservedFields ? observedSource.observed_at : null
    const ageDays = observedAt ? Math.max(0, (Date.now() - new Date(observedAt).getTime()) / 86400000) : null
    const matchingHistory = priceHistory.filter((point) => String(point.currency).toUpperCase() === String(observedSource.currency || '').toUpperCase())
    const historicalPrices = matchingHistory.map((point) => Number(point.price)).filter(Number.isFinite)
    const historicalMinimum = historicalPrices.length >= 2 ? Math.min(...historicalPrices) : null
    const historicalMaximum = historicalPrices.length >= 2 ? Math.max(...historicalPrices) : null
    const historicalPricePosition = price != null && historicalPrices.length >= 2
      ? historicalMaximum === historicalMinimum
        ? 50
        : Math.max(0, Math.min(100, ((historicalMaximum - price) / (historicalMaximum - historicalMinimum)) * 100))
      : null

    return {
      ...registeredSource,
      ...observedSource,
      hasEvidence,
      sourceTypes: [...sourceTypes],
      provenance: sourceTypes.size ? [...sourceTypes].join(', ') : 'unavailable',
      sourceReviews,
      price: price == null ? null : Number(price),
      rating,
      reviewCount,
      sentimentTotal,
      averageReviewQuality,
      verifiedShare,
      reviewQualityScore: averageReviewQuality == null || verifiedShare == null
        ? null
        : (averageReviewQuality * 75) + (verifiedShare * 0.25),
      positivePercentage,
      neutralPercentage,
      negativePercentage,
      aspectCounts,
      ratingDistribution,
      positiveAspectShare,
      aspectMentions,
      ratingSpread,
      sentimentConsistency: monthlyPositiveSpread == null ? null : Math.max(0, 100 - monthlyPositiveSpread),
      consistencyMonths: monthlyPositiveShares.length,
      priceHistory,
      historicalPricePosition,
      historicalMinimum,
      historicalMaximum,
      historicalPointCount: historicalPrices.length,
      ageDays: Number.isFinite(ageDays) ? ageDays : null,
      currency: hasObservedFields ? observedSource.currency || null : null,
      availability: hasObservedFields ? observedSource.availability : null,
      productUrl: observedSource.product_url || null,
      observedAt,
    }
  })
}

function recommendationFor(allRows) {
  const evidenceRows = allRows.filter((row) => row.hasEvidence)
  const nonDemoRows = evidenceRows.filter((row) => row.sourceTypes.some((type) => type === 'live' || type === 'live_scraped' || type === 'stored'))
  const demoOnly = nonDemoRows.length === 0
  const candidates = demoOnly
    ? evidenceRows.filter((row) => row.sourceTypes.length && row.sourceTypes.every((type) => type === 'seeded_demo'))
    : nonDemoRows

  if (candidates.length === 1) {
    return { candidates, winner: null, reason: 'Only 1 retailer has sufficient evidence for this product.', factors: [], dataLabel: '' }
  }
  if (candidates.length < 2) {
    return { candidates, winner: null, reason: 'Insufficient evidence to make a purchase recommendation.', factors: [], dataLabel: '' }
  }

  const priced = candidates.filter((row) => row.price != null && row.currency)
  const currencyGroups = new Map()
  priced.forEach((row) => {
    const currency = String(row.currency).toUpperCase()
    currencyGroups.set(currency, [...(currencyGroups.get(currency) || []), row])
  })
  const largestCurrencyGroup = [...currencyGroups.values()].sort((left, right) => right.length - left.length)[0] || []
  const canComparePrice = largestCurrencyGroup.length === candidates.length && candidates.length > 1
  const comparablePrices = largestCurrencyGroup.map((row) => row.price)
  const minimumPrice = canComparePrice ? Math.min(...comparablePrices) : null
  const maximumPrice = canComparePrice ? Math.max(...comparablePrices) : null

  const scored = candidates.map((row) => {
    const factors = {}
    if (canComparePrice) {
      factors.price = maximumPrice === minimumPrice ? 50 : ((maximumPrice - row.price) / (maximumPrice - minimumPrice)) * 100
    }
    if (row.historicalPricePosition != null) factors.historicalPrice = row.historicalPricePosition
    if (row.sentimentTotal) factors.sentiment = row.positivePercentage + row.neutralPercentage * 0.5
    if (row.rating != null) factors.rating = Math.max(0, Math.min(100, (row.rating / 5) * 100))
    if (row.reviewCount != null && row.reviewCount > 0) factors.reviewVolume = Math.min(100, (Math.log10(row.reviewCount + 1) / 3) * 100)
    if (row.reviewQualityScore != null) factors.reviewQuality = row.reviewQualityScore
    if (row.positiveAspectShare != null) factors.aspects = row.positiveAspectShare
    if (row.sentimentConsistency != null) factors.sentimentConsistency = row.sentimentConsistency
    if (row.availability === true) factors.availability = 100
    if (row.availability === false) factors.availability = 0
    if (row.ageDays != null) factors.freshness = Math.max(0, 100 - (row.ageDays / 30) * 100)
    return { row, factors }
  })

  const commonFactors = Object.keys(FACTOR_WEIGHTS).filter((key) => scored.every((item) => item.factors[key] != null))
  const commonCustomerFactors = commonFactors.filter((key) => ['sentiment', 'rating', 'reviewVolume', 'reviewQuality', 'aspects', 'sentimentConsistency'].includes(key))
  if (!commonCustomerFactors.length) {
    return { candidates, winner: null, reason: `Recommendation based on ${candidates.length} observed retailers is not possible: no customer-evidence factor is available for every retailer.`, factors: [], dataLabel: '' }
  }

  const applicableWeight = commonFactors.reduce((sum, key) => sum + FACTOR_WEIGHTS[key], 0)
  const results = scored.map(({ row, factors }) => {
    const factorDetails = commonFactors.map((key) => {
      const points = FACTOR_WEIGHTS[key] * factors[key] / 100
      let reason = ''
      if (key === 'price') reason = `${row.currency} ${row.price.toLocaleString()} observed price`
      if (key === 'historicalPrice') reason = `${row.historicalPointCount} same-currency observations; current ${row.currency} ${row.price.toLocaleString()} within recorded ${row.currency} ${row.historicalMinimum.toLocaleString()}–${row.historicalMaximum.toLocaleString()} range`
      if (key === 'sentiment') reason = `${row.positivePercentage.toFixed(1)}% positive in ${row.sentimentTotal} source-matched reviews`
      if (key === 'rating') reason = `${row.rating.toFixed(1)}/5 observed rating`
      if (key === 'reviewVolume') reason = `${row.reviewCount} observed/source-matched reviews`
      if (key === 'reviewQuality') reason = `${(row.averageReviewQuality * 100).toFixed(1)}% average text-quality score; ${row.verifiedShare.toFixed(1)}% verified-purchase share`
      if (key === 'aspects') reason = `${row.positiveAspectShare.toFixed(1)}% positive/neutral-weighted aspect share`
      if (key === 'sentimentConsistency') reason = `${row.consistencyMonths} dated review months; score reflects positive-sentiment variation`
      if (key === 'availability') reason = row.availability ? 'Availability observed as available' : 'Availability observed as unavailable'
      if (key === 'freshness') reason = `Observation age ${Math.floor(row.ageDays)} days`
      return { key, label: key === 'reviewVolume' ? 'Review evidence' : key === 'reviewQuality' ? 'Review quality' : key === 'aspects' ? 'Aspect satisfaction' : key === 'historicalPrice' ? 'Price vs history' : key === 'sentimentConsistency' ? 'Sentiment consistency' : key[0].toUpperCase() + key.slice(1), weight: FACTOR_WEIGHTS[key], points, reason }
    })
    const totalPoints = factorDetails.reduce((sum, factor) => sum + factor.points, 0)
    return { ...row, factors: factorDetails, score: totalPoints / applicableWeight * 100, totalPoints }
  }).sort((left, right) => right.score - left.score)

  const topScore = results[0].score
  const tied = results.filter((item) => Math.abs(item.score - topScore) < 0.01).length > 1
  const sourceTypes = [...new Set(candidates.flatMap((row) => row.sourceTypes))]
  const hasLive = sourceTypes.includes('live') || sourceTypes.includes('live_scraped')
  const hasStored = sourceTypes.includes('stored')
  const hasDemo = sourceTypes.includes('seeded_demo')
  const dataLabel = sourceTypes.every((type) => type === 'seeded_demo')
    ? 'Recommendation based on seeded demo observations'
    : `Recommendation based on ${[
      ...(hasLive ? ['live'] : []),
      ...(hasStored ? ['stored'] : []),
      ...(hasDemo ? ['seeded demo'] : []),
    ].join(', ')} observations`

  return {
    candidates,
    winner: tied ? null : results[0],
    results,
    factors: commonFactors,
    dataLabel,
    reason: tied ? `Recommendation based on ${candidates.length} observed retailers is tied on the available evidence.` : '',
    applicableWeight,
  }
}

function EvidenceChart({ title, data, dataKey = 'value', color = '#34d399', emptyMessage, domain }) {
  return (
    <article className="chart-panel source-evidence-chart">
      <h4>{title}</h4>
      {data.length ? <div className="source-chart-canvas">
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 8, right: 6, bottom: 18, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
            <XAxis dataKey="name" interval={0} angle={-18} textAnchor="end" height={48} />
            <YAxis domain={domain} />
            <Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} />
            {dataKey === 'sentiment' ? <>
              <Bar dataKey="positive" name="Positive %" fill="#34d399" />
              <Bar dataKey="neutral" name="Neutral %" fill="#fbbf24" />
              <Bar dataKey="negative" name="Negative %" fill="#f87171" />
            </> : dataKey === 'ratingDistribution' ? <>
              <Bar dataKey="star1" name="1 star" fill="#f87171" />
              <Bar dataKey="star2" name="2 stars" fill="#fb923c" />
              <Bar dataKey="star3" name="3 stars" fill="#fbbf24" />
              <Bar dataKey="star4" name="4 stars" fill="#60a5fa" />
              <Bar dataKey="star5" name="5 stars" fill="#34d399" />
            </> : <Bar dataKey={dataKey} name={title} fill={color} />}
          </BarChart>
        </ResponsiveContainer>
      </div> : <p className="empty-state source-chart-empty">{emptyMessage}</p>}
    </article>
  )
}

function buildPriceHistoryGroups(rows) {
  const groups = new Map()
  rows.forEach((row) => {
    const currencies = [...new Set(row.priceHistory.map((point) => String(point.currency).toUpperCase()))]
    currencies.forEach((currency) => {
      const points = row.priceHistory.filter((point) => String(point.currency).toUpperCase() === currency)
      if (points.length < 2) return
      groups.set(currency, [...(groups.get(currency) || []), { row, points }])
    })
  })

  return [...groups.entries()].map(([currency, sources]) => {
    const dates = [...new Set(sources.flatMap(({ points }) => points.map((point) => point.observed_at)))].sort()
    return {
      currency,
      sources,
      data: dates.map((date) => ({
        date,
        ...Object.fromEntries(sources.map(({ row, points }) => [
          row.code,
          points.find((point) => point.observed_at === date)?.price ?? null,
        ])),
      })),
    }
  })
}

function formatPriceHistoryDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString()
}

function HistoricalPriceCharts({ groups }) {
  if (!groups.length) return <p className="empty-state">Historical price trends are unavailable; no retailer has at least two dated, provenance-approved observations.</p>

  return <div className="dashboard-grid source-history-charts">{groups.map((group) => (
    <article className="chart-panel source-evidence-chart" key={group.currency}>
      <h4>Recorded price history ({group.currency})</h4>
      <div className="source-chart-canvas">
        <ResponsiveContainer>
          <LineChart data={group.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
            <XAxis dataKey="date" tickFormatter={formatPriceHistoryDate} />
            <YAxis />
            <Tooltip labelFormatter={formatPriceHistoryDate} content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} />
            <Legend />
            {group.sources.map(({ row }, index) => <Line key={row.code} type="monotone" dataKey={row.code} name={row.name} stroke={HISTORY_COLORS[index % HISTORY_COLORS.length]} connectNulls={false} />)}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  ))}</div>
}

function validProductUrl(value) {
  try {
    const url = new URL(value)
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return false
    if (url.hostname === 'example.com' || url.hostname.endsWith('.example.com')) return false
    if (/(^|\/)(search|search-results?|catalog|browse|query|s)(\/|$)/i.test(url.pathname)) return false
    if (['q', 'k', 'query', 'search', 'search_query', 'keyword'].some((key) => url.searchParams.has(key))) return false
    return url.pathname.split('/').filter(Boolean).length > 0
  } catch {
    return false
  }
}

function StoreComparison({ query, selectedSource, sources, onCategoryChange, onSourceEvidenceChange }) {
  const [matches, setMatches] = useState([])
  const [selectedProductId, setSelectedProductId] = useState('')
  const [observations, setObservations] = useState([])
  const [reviews, setReviews] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [reviewQuality, setReviewQuality] = useState(null)
  const [catalogComparisons, setCatalogComparisons] = useState([])
  const [loadingMatches, setLoadingMatches] = useState(true)
  const [loadingEvidence, setLoadingEvidence] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    const loadMatches = async () => {
      setLoadingMatches(true)
      setError('')
      setMatches([])
      setSelectedProductId('')
      setObservations([])
      setReviews([])
      setAnalytics(null)
      setReviewQuality(null)
      setCatalogComparisons([])

      try {
        const response = await getProducts({ q: query })
        const queryKey = normalizeText(query)
        const products = (response.data.items || []).sort((left, right) => {
          const leftExact = normalizeText(left.name) === queryKey ? 0 : 1
          const rightExact = normalizeText(right.name) === queryKey ? 0 : 1
          return leftExact - rightExact || Number(right.total_reviews || 0) - Number(left.total_reviews || 0)
        })
        if (cancelled) return
        setMatches(products)
        if (products.length) setSelectedProductId(String(products[0].id))

        if (products.length > 1) {
          compareProducts({ product_ids: products.slice(0, 4).map((item) => item.id) })
            .then((comparison) => {
              if (!cancelled) setCatalogComparisons(comparison.data.items || [])
            })
            .catch(() => {
              if (!cancelled) setCatalogComparisons([])
            })
        }
      } catch (requestError) {
        if (!cancelled) setError(requestError?.response?.data?.detail || 'Unable to search the stored product catalog.')
      } finally {
        if (!cancelled) setLoadingMatches(false)
      }
    }

    loadMatches()
    return () => { cancelled = true }
  }, [query])

  const selectedProduct = matches.find((item) => String(item.id) === String(selectedProductId))

  useEffect(() => {
    onCategoryChange?.(selectedProduct?.category || '')
  }, [selectedProduct?.category, onCategoryChange])

  useEffect(() => {
    if (!selectedProductId) return undefined
    let cancelled = false
    const loadEvidence = async () => {
      setLoadingEvidence(true)
      const [sourceResult, reviewResult, analyticsResult, qualityResult] = await Promise.allSettled([
        getProductSources(selectedProductId),
        getProductReviews(selectedProductId, { limit: 100 }),
        getAnalytics(selectedProductId),
        getReviewQuality(selectedProductId),
      ])
      if (cancelled) return
      if (sourceResult.status === 'fulfilled') setObservations(sourceResult.value.data.items || [])
      else setObservations([])
      if (reviewResult.status === 'fulfilled') setReviews(reviewResult.value.data.items || [])
      else setReviews([])
      if (analyticsResult.status === 'fulfilled') setAnalytics(analyticsResult.value.data)
      else setAnalytics(null)
      if (qualityResult.status === 'fulfilled') setReviewQuality(qualityResult.value.data)
      else setReviewQuality(null)
      setLoadingEvidence(false)
    }

    loadEvidence()
    return () => { cancelled = true }
  }, [selectedProductId])

  const storeRows = useMemo(() => buildStoreRows(sources, observations, reviews), [sources, observations, reviews])
  const orderedRows = useMemo(() => prioritizeSources(storeRows, selectedProduct?.category), [storeRows, selectedProduct?.category])
  useEffect(() => {
    onSourceEvidenceChange?.(Object.fromEntries(orderedRows.map((row) => [row.code, { hasEvidence: row.hasEvidence, dataTypes: row.sourceTypes }])))
  }, [onSourceEvidenceChange, orderedRows])
  const visibleRows = selectedSource === 'all' ? orderedRows : orderedRows.filter((source) => source.code === selectedSource)
  const recommendation = useMemo(() => recommendationFor(orderedRows), [orderedRows])
  const observationCount = orderedRows.filter((row) => row.hasEvidence).length
  const selectedCatalogComparison = catalogComparisons.find((item) => String(item.id) === String(selectedProductId))
  const candidateRows = recommendation.results || []

  const priceChart = visibleRows.filter((row) => row.price != null).map((row) => ({ name: row.name, value: row.price, currency: row.currency || 'Currency unavailable', dataType: row.provenance }))
  const priceHistoryGroups = useMemo(() => buildPriceHistoryGroups(visibleRows), [visibleRows])
  const ratingChart = visibleRows.filter((row) => row.rating != null).map((row) => ({ name: row.name, value: row.rating }))
  const ratingDistributionChart = visibleRows
    .filter((row) => row.sourceReviews.length && Object.values(row.ratingDistribution).some(Boolean))
    .map((row) => ({ name: row.name, ...row.ratingDistribution }))
  const reviewChart = visibleRows.filter((row) => row.reviewCount != null).map((row) => ({ name: row.name, value: row.reviewCount }))
  const sentimentChart = visibleRows.filter((row) => row.sentimentTotal).map((row) => ({ name: row.name, positive: row.positivePercentage, neutral: row.neutralPercentage, negative: row.negativePercentage }))
  const aspectChart = visibleRows.filter((row) => row.positiveAspectShare != null).map((row) => ({ name: row.name, value: row.positiveAspectShare }))
  const intelligenceChart = catalogComparisons
    .filter((item) => item.intelligence_score != null)
    .map((item) => ({ name: item.name, value: item.intelligence_score }))

  return (
    <section className="source-comparison-section" aria-live="polite">
      <header className="source-comparison-header">
        <div>
          <p className="eyebrow muted">Stored product and retailer evidence</p>
          <h3>Where can I buy this product?</h3>
          <p className="muted">ReviewLens checks recorded catalog and source observations. It does not contact every retailer or invent missing market data.</p>
        </div>
        <div className="source-comparison-counts">
          <span><strong>{matches.length}</strong> catalog matches</span>
          <span><strong>{observationCount}</strong> retailers with evidence</span>
          <span><strong>{orderedRows.length}</strong> configured retailers</span>
        </div>
      </header>

      {loadingMatches ? <p className="empty-state">Searching stored product records...</p> : error ? <div className="error-state" role="alert">{error}</div> : matches.length === 0 ? <p className="empty-state">No stored catalog products match “{query}”. No retailer comparison was made.</p> : <>
        <div className="source-product-context">
          <label htmlFor="comparison-product">Matched catalog product</label>
          {matches.length > 1 ? <select id="comparison-product" className="select-field" value={selectedProductId} onChange={(event) => setSelectedProductId(event.target.value)}>
            {matches.map((item) => <option value={item.id} key={item.id}>{item.name} · {item.brand || 'Brand unavailable'} · {item.total_reviews > 0 ? `${item.total_reviews} reviews` : 'reviews unavailable'} · ${displayType(item.data_type)}</option>)}
          </select> : <strong>{selectedProduct?.name}</strong>}
          <span className="badge provenance-unknown">Catalog data: {displayType(selectedProduct?.data_type)}</span>
          {matches.length > 4 && <span className="muted">Catalog charts compare the first 4 matching products.</span>}
        </div>

        {loadingEvidence ? <p className="empty-state">Loading recorded retailer evidence...</p> : <>
          <div className="table-wrap source-comparison-table-wrap">
            <table className="data-table source-comparison-table">
              <thead><tr><th>Store</th><th>Product</th><th>Price</th><th>Rating</th><th>Reviews</th><th>Review quality</th><th>Sentiment</th><th>Availability</th><th>Data type</th><th>Source link</th></tr></thead>
              <tbody>{visibleRows.map((row) => (
                <tr key={row.code}>
                  <td><strong>{row.name}</strong><small>{sourceCategoryLabel(row.code)}</small></td>
                  <td>{row.hasEvidence ? selectedProduct?.name : 'No verified observation available'}</td>
                  <td>{row.price == null ? 'unavailable' : `${row.currency || 'Currency unavailable'} ${row.price.toLocaleString()}`}</td>
                  <td>{row.rating == null ? 'unavailable' : `${row.rating.toFixed(1)} / 5`}</td>
                  <td>{row.reviewCount == null ? 'unavailable' : row.review_count != null ? `${row.reviewCount} observed` : `${row.reviewCount} source-matched`}</td>
                  <td>{row.reviewQualityScore == null ? 'unavailable' : `${row.reviewQualityScore.toFixed(0)}/100`}</td>
                  <td>{row.sentimentTotal ? `${row.positivePercentage.toFixed(1)}% / ${row.neutralPercentage.toFixed(1)}% / ${row.negativePercentage.toFixed(1)}%` : 'unavailable'}</td>
                  <td>{row.availability === true ? 'Available' : row.availability === false ? 'Not available (observed)' : 'unavailable'}</td>
                  <td><span className={`badge ${row.provenance === 'unavailable' ? 'provenance-unknown' : row.sourceTypes.includes('seeded_demo') ? 'provenance-demo' : row.sourceTypes.includes('live') || row.sourceTypes.includes('live_scraped') ? 'provenance-live' : 'provenance-unknown'}`}>{row.provenance}</span></td>
                  <td>{validProductUrl(row.productUrl) ? <a href={row.productUrl} target="_blank" rel="noreferrer">View Product →</a> : 'Source link unavailable'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>

          <section className="purchase-decision" aria-labelledby="purchase-decision-title">
            <div className="purchase-decision-heading">
              <div><p className="eyebrow muted">Evidence-weighted result</p><h3 id="purchase-decision-title">Purchase Decision</h3></div>
              <span className="muted">{recommendation.candidates.length} retailer{recommendation.candidates.length === 1 ? '' : 's'} with sufficient evidence</span>
            </div>
            {recommendation.winner ? <>
              <h4>Recommended Purchase Option</h4>
              <p className="purchase-recommendation">{recommendation.winner.name} — Recommended based on observed evidence</p>
              <p className="muted">{recommendation.dataLabel} · Evidence score {recommendation.winner.score.toFixed(1)}/100 across {recommendation.factors.length} common factors.</p>
              <div className="recommendation-factor-list">
                {recommendation.winner.factors.map((factor) => <div className="recommendation-factor" key={factor.key}><strong>{factor.label}</strong><span>+{factor.points.toFixed(1)} / {factor.weight}</span><small>{factor.reason}</small></div>)}
              </div>
              {recommendation.factors.includes('price') && recommendation.factors.some((factor) => ['sentiment', 'rating', 'reviewVolume', 'reviewQuality', 'aspects', 'sentimentConsistency'].includes(factor)) && <details className="recommendation-explanation"><summary>Why this recommendation?</summary><p>The score compares only factors present for every included retailer. Price is compared only when currencies match. Customer evidence comes from source-matched records; unavailable factors are excluded.</p></details>}
              {recommendation.factors.includes('price') && recommendation.factors.some((factor) => ['sentiment', 'rating', 'reviewVolume', 'reviewQuality', 'aspects', 'sentimentConsistency'].includes(factor)) && <p className="muted">Value indicator: {recommendation.winner.score.toFixed(1)}/100 from comparable observed price and customer evidence.</p>}
            </> : <p className="empty-state">{recommendation.reason || (observationCount === 1 ? 'Only 1 retailer has sufficient evidence for this product.' : 'Insufficient evidence to make a purchase recommendation.')}</p>}
          </section>

          <section className="source-charts-section">
            <header><p className="eyebrow muted">Interactive evidence</p><h3>Retailer comparison</h3><p className="muted">Charts include only recorded values. Product intelligence is a catalog-level score, not a retailer rating.</p></header>
            <div className="dashboard-grid source-comparison-charts">
              <EvidenceChart title="Observed price comparison" data={priceChart} emptyMessage="No observed retailer prices are available." />
              <EvidenceChart title="Observed rating comparison" data={ratingChart} emptyMessage="No retailer-specific ratings are available." domain={[0, 5]} color="#60a5fa" />
              <EvidenceChart title="Source-matched rating distribution" data={ratingDistributionChart} dataKey="ratingDistribution" emptyMessage="No source-matched review ratings are available." color="#60a5fa" />
              <EvidenceChart title="Observed review volume" data={reviewChart} emptyMessage="No retailer-specific review counts are available." color="#fbbf24" />
              <EvidenceChart title="Source-matched sentiment (%)" data={sentimentChart} dataKey="sentiment" emptyMessage="No retailer-matched sentiment reviews are available." domain={[0, 100]} />
              <EvidenceChart title="Catalog product intelligence" data={intelligenceChart} emptyMessage="Product-level intelligence is unavailable for these catalog matches." domain={[0, 100]} color="#a78bfa" />
              <EvidenceChart title="Source-matched aspect satisfaction (%)" data={aspectChart} emptyMessage="No retailer-matched aspect evidence is available." domain={[0, 100]} color="#fb7185" />
            </div>
            <HistoricalPriceCharts groups={priceHistoryGroups} />
          </section>

          <section className="product-evidence-context table-panel">
            <div className="section-header"><div><p className="eyebrow muted">Product-level review evidence</p><h3>{selectedProduct?.name} insight context</h3></div><span className="badge provenance-unknown">{analytics?.total_reviews ? displayType(selectedProduct?.data_type) : 'unavailable'}</span></div>
            <p>{analytics?.total_reviews ? `${analytics.total_reviews} reviews · ${analytics.average_rating}/5 · ${analytics.positive_percentage}% positive · ${analytics.neutral_percentage}% neutral · ${analytics.negative_percentage}% negative` : 'Rating and sentiment evidence unavailable.'}</p>
            <p className="muted">Product intelligence: {selectedCatalogComparison?.intelligence_score == null ? 'unavailable' : `${selectedCatalogComparison.intelligence_score}/100`}. Review quality: {reviewQuality ? `${reviewQuality.review_count} analyzed · ${reviewQuality.signals.length} pattern signal(s)` : 'unavailable'}.</p>
            {reviewQuality?.signals?.length > 0 && <ul className="source-quality-signals">{reviewQuality.signals.slice(0, 3).map((signal) => <li key={signal.type}>{signal.message} This is a pattern signal, not an authenticity conclusion.</li>)}</ul>}
          </section>
        </>}
      </>}
    </section>
  )
}

export default StoreComparison