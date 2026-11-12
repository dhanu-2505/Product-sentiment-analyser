import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'

import { getProductReviews } from '../../services/api'

function ReviewsPage() {
  const { productId } = useParams()
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sentimentFilter, setSentimentFilter] = useState('all')
  const [ratingFilter, setRatingFilter] = useState('all')
  const [sortOrder, setSortOrder] = useState('newest')

  useEffect(() => {
    const fetchReviews = async () => {
      setLoading(true)
      try {
        const response = await getProductReviews(productId)
        setReviews(response.data.items || [])
      } catch (err) {
        setError(err?.response?.data?.detail || 'Unable to load reviews')
      } finally {
        setLoading(false)
      }
    }

    fetchReviews()
  }, [productId])

  const filteredReviews = useMemo(() => {
    const query = search.toLowerCase().trim()
    return [...reviews]
      .filter((review) => {
        const matchesText = !query || review.review_text.toLowerCase().includes(query)
        const matchesSentiment = sentimentFilter === 'all' || review.sentiment === sentimentFilter
        const matchesRating = ratingFilter === 'all' || String(review.rating) === ratingFilter
        return matchesText && matchesSentiment && matchesRating
      })
      .sort((a, b) => {
        if (sortOrder === 'rating') {
          return b.rating - a.rating
        }
        if (sortOrder === 'oldest') {
          return new Date(a.review_date || 0) - new Date(b.review_date || 0)
        }
        return new Date(b.review_date || 0) - new Date(a.review_date || 0)
      })
  }, [reviews, search, sentimentFilter, ratingFilter, sortOrder])

  if (loading) {
    return (
      <div className="page">
        <div className="loading-grid">
          <div className="skeleton-line large" />
          <div className="skeleton-card" />
          <div className="skeleton-card" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="error-state">
          <h3>Unable to load reviews</h3>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow muted">Reviews</p>
          <h3>Customer feedback explorer</h3>
        </div>
      </div>

      <div className="table-panel">
        <div className="filter-row" style={{ marginBottom: 18 }}>
          <input className="field" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search review text..." />
          <select className="select-field" value={sentimentFilter} onChange={(event) => setSentimentFilter(event.target.value)}>
            <option value="all">All sentiment</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </select>
          <select className="select-field" value={ratingFilter} onChange={(event) => setRatingFilter(event.target.value)}>
            <option value="all">All ratings</option>
            <option value="5">5 stars</option>
            <option value="4">4 stars</option>
            <option value="3">3 stars</option>
            <option value="2">2 stars</option>
            <option value="1">1 star</option>
          </select>
          <select className="select-field" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="rating">Highest rating</option>
          </select>
        </div>

        {filteredReviews.length === 0 ? (
          <div className="empty-state">
            <h3>No reviews match this filter</h3>
            <p>Try adjusting the search or sentiment filters.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reviewer</th>
                  <th>Rating</th>
                  <th>Review</th>
                  <th>Date</th>
                  <th>Sentiment</th>
                  <th>Score</th>
                  <th>Data origin</th>
                </tr>
              </thead>
              <tbody>
                {filteredReviews.map((review) => (
                  <tr key={review.id}>
                    <td>{review.reviewer_name || 'Anonymous'}</td>
                    <td>{review.rating}/5</td>
                    <td>{review.review_text}</td>
                    <td>{review.review_date ? new Date(review.review_date).toLocaleDateString() : '—'}</td>
                    <td><span className={`badge ${review.sentiment}`}>{review.sentiment}</span></td>
                    <td>{Number(review.sentiment_score || 0).toFixed(2)}</td>
                    <td>
                      <span className={`badge provenance-${review.data_type === 'seeded_demo' ? 'demo' : review.data_type === 'live_scraped' ? 'live' : 'unknown'}`}>
                        {review.data_type === 'seeded_demo' ? 'Seeded demo' : review.data_type === 'live_scraped' ? 'Live scraped' : 'Unverified'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default ReviewsPage
