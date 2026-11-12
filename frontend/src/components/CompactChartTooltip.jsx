function CompactChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null

  const labelText = label == null ? '' : String(label)

  return (
    <div className="chart-tooltip-label" role="presentation">
      {labelText && <span className="chart-tooltip-category">{labelText}</span>}
      {payload.map((item, index) => {
        const showName = payload.length > 1 || !labelText || String(item.name) !== labelText
        const color = item.color || item.stroke || item.fill || 'var(--text)'

        return (
          <span className="chart-tooltip-value" style={{ color }} key={`${item.dataKey || item.name}-${index}`}>
            {showName && item.name ? `${item.name} ` : ''}{String(item.value ?? '')}
          </span>
        )
      })}
    </div>
  )
}

export default CompactChartTooltip