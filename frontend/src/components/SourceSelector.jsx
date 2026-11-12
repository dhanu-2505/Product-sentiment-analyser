import { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, Search, Store } from 'lucide-react'

const SOURCE_CATEGORIES = {
  amazon: 'General retail',
  flipkart: 'General retail',
  myntra: 'Fashion',
  ajio: 'Fashion',
  meesho: 'Fashion',
  snapdeal: 'General retail',
  tatacliq: 'Fashion & electronics',
  nykaa: 'Beauty',
  croma: 'Electronics',
  reliance_digital: 'Electronics',
  bigbasket: 'Grocery',
  blinkit: 'Grocery',
  zepto: 'Grocery',
  swiggy_instamart: 'Grocery',
  jiomart: 'Grocery',
  firstcry: 'Baby products',
  pepperfry: 'Furniture',
  lenskart: 'Eyewear',
  decathlon: 'Sports',
  ikea: 'Furniture',
}

const CATEGORY_PRIORITY = {
  electronics: ['amazon', 'flipkart', 'croma', 'reliance_digital', 'tatacliq'],
  fashion: ['myntra', 'ajio', 'tatacliq', 'meesho'],
  beauty: ['nykaa', 'myntra', 'amazon', 'flipkart'],
  grocery: ['bigbasket', 'blinkit', 'zepto', 'swiggy_instamart', 'jiomart'],
  furniture: ['pepperfry', 'ikea'],
  eyewear: ['lenskart'],
  sports: ['decathlon'],
  baby: ['firstcry'],
}

export function sourceCategoryLabel(code) {
  return SOURCE_CATEGORIES[code] || 'Retail'
}

export function prioritizeSources(sources, category) {
  const group = categoryGroup(category)
  const priority = CATEGORY_PRIORITY[group] || []
  const registryOrder = new Map(sources.map((source, index) => [source.code, index]))
  return [...sources].sort((left, right) => {
    const leftRank = priority.indexOf(left.code)
    const rightRank = priority.indexOf(right.code)
    const leftOrder = leftRank < 0 ? priority.length + registryOrder.get(left.code) : leftRank
    const rightOrder = rightRank < 0 ? priority.length + registryOrder.get(right.code) : rightRank
    return leftOrder - rightOrder
  })
}

function categoryGroup(category) {
  const value = String(category || '').toLowerCase()
  if (/phone|laptop|tablet|camera|tv|electronics|appliance/.test(value)) return 'electronics'
  if (/fashion|footwear|apparel|clothing/.test(value)) return 'fashion'
  if (/beauty|skincare|cosmetic/.test(value)) return 'beauty'
  if (/grocery|food/.test(value)) return 'grocery'
  if (/furniture|home decor/.test(value)) return 'furniture'
  if (/eyewear|glasses/.test(value)) return 'eyewear'
  if (/sport|fitness/.test(value)) return 'sports'
  if (/baby|child/.test(value)) return 'baby'
  return ''
}

function SourceSelector({ sources, value, onChange, category = '', loading = false, sourceEvidence = {} }) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const rootRef = useRef(null)
  const selectedSource = sources.find((source) => source.code === value)
  const categoryKey = categoryGroup(category)

  const orderedSources = useMemo(() => prioritizeSources(sources, categoryKey), [categoryKey, sources])

  const filteredSources = orderedSources.filter((source) => (
    `${source.name} ${source.code} ${sourceCategoryLabel(source.code)}`.toLowerCase().includes(search.trim().toLowerCase())
  ))

  useEffect(() => {
    if (!open) return undefined

    const closeOnOutsideClick = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false)
    }
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('pointerdown', closeOnOutsideClick)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('pointerdown', closeOnOutsideClick)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [open])

  const selectSource = (sourceCode) => {
    onChange(sourceCode)
    setOpen(false)
    setSearch('')
  }

  return (
    <div className="source-selector" ref={rootRef}>
      <button
        className="source-selector-trigger"
        type="button"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((current) => !current)}
      >
        <Store size={16} aria-hidden="true" />
        <span>{value === 'all' ? 'All Sources' : selectedSource?.name || (loading ? 'Loading sources...' : 'Choose source')}</span>
        <ChevronDown size={15} aria-hidden="true" />
      </button>
      {open && (
        <div className="source-selector-popover" role="dialog" aria-label="Choose a retailer">
          <label className="source-selector-search">
            <Search size={15} aria-hidden="true" />
            <input
              autoFocus
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search retailers"
              aria-label="Search retailers"
            />
          </label>
          <div className="source-selector-list" role="listbox" aria-label="Configured retailers">
            <button className={`source-option ${value === 'all' ? 'selected' : ''}`} type="button" role="option" aria-selected={value === 'all'} onClick={() => selectSource('all')}>
              <span className="source-option-icon"><Store size={15} /></span>
              <span className="source-option-details"><strong>All Sources</strong><small>Compare all {sources.length} configured retailers</small></span>
              <span className="source-option-badge">All</span>
            </button>
            {filteredSources.map((source) => {
              const evidenceTypes = sourceEvidence[source.code]?.dataTypes || []
              const statusTypes = [
                ...(evidenceTypes.some((type) => type === 'live' || type === 'live_scraped') ? ['live'] : []),
                ...(evidenceTypes.includes('stored') ? ['stored'] : []),
                ...(evidenceTypes.includes('seeded_demo') ? ['seeded_demo'] : []),
              ]
              const status = statusTypes.length
                ? statusTypes.map((type) => type === 'seeded_demo' ? 'Seeded Demo' : type[0].toUpperCase() + type.slice(1)).join(' + ')
                : source.live_connector_configured ? 'Connector configured' : 'Unavailable'
              const statusClass = statusTypes.includes('live')
                ? 'live'
                : statusTypes.includes('stored')
                  ? 'stored'
                  : statusTypes.includes('seeded_demo')
                    ? 'demo'
                    : source.live_connector_configured ? 'configured' : 'unavailable'
              return (
                <button className={`source-option ${value === source.code ? 'selected' : ''}`} type="button" role="option" aria-selected={value === source.code} key={source.code} onClick={() => selectSource(source.code)}>
                  <span className="source-option-icon"><Store size={15} /></span>
                  <span className="source-option-details"><strong>{source.name}</strong><small>{sourceCategoryLabel(source.code)}</small></span>
                  <span className={`source-option-badge ${statusClass}`}>{status}</span>
                </button>
              )
            })}
            {filteredSources.length === 0 && <p className="source-selector-empty">No configured retailers match this search.</p>}
          </div>
          <p className="source-selector-note">Registry status is not a product observation. Retailer data is verified after a product is selected.</p>
        </div>
      )}
    </div>
  )
}

export default SourceSelector