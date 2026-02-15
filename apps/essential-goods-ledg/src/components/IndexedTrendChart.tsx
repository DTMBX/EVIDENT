import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

interface IndexedTrendChartProps {
  dates: string[]
  wageIndexed: number[]
  basketIndexed: number[]
  wageLabel: string
}

export function IndexedTrendChart({ dates, wageIndexed, basketIndexed, wageLabel }: IndexedTrendChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || dates.length === 0) return

    const container = containerRef.current
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const margin = { top: 20, right: 120, bottom: 70, left: 60 }
    const width = container.clientWidth - margin.left - margin.right
    const height = 400 - margin.top - margin.bottom

    const g = svg
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    const parseDate = d3.timeParse('%Y-%m-%d')
    const parsedDates = dates.map(d => parseDate(d)!)

    const xScale = d3.scaleTime()
      .domain(d3.extent(parsedDates) as [Date, Date])
      .range([0, width])

    const allValues = [...wageIndexed, ...basketIndexed]
    const yScale = d3.scaleLinear()
      .domain([
        Math.min(d3.min(allValues) || 0, 95),
        Math.max(d3.max(allValues) || 0, 105)
      ])
      .range([height, 0])
      .nice()

    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).ticks(6).tickFormat((d) => {
        const date = d as Date
        return d3.timeFormat('%b %y')(date)
      }))
      .call(g => g.select('.domain').attr('stroke', 'oklch(0.88 0.01 250)'))
      .call(g => g.selectAll('.tick line').attr('stroke', 'oklch(0.88 0.01 250)'))
      .call(g => g.selectAll('.tick text')
        .attr('fill', 'oklch(0.50 0.01 250)')
        .style('font-family', 'IBM Plex Sans, sans-serif')
        .style('font-size', '11px')
        .attr('transform', 'rotate(-45)')
        .style('text-anchor', 'end')
        .attr('dx', '-0.5em')
        .attr('dy', '0.5em'))

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(8))
      .call(g => g.select('.domain').attr('stroke', 'oklch(0.88 0.01 250)'))
      .call(g => g.selectAll('.tick line').attr('stroke', 'oklch(0.88 0.01 250)'))
      .call(g => g.selectAll('.tick text')
        .attr('fill', 'oklch(0.50 0.01 250)')
        .style('font-family', 'JetBrains Mono, monospace')
        .style('font-size', '12px'))

    g.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', yScale(100))
      .attr('y2', yScale(100))
      .attr('stroke', 'oklch(0.70 0 0)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4 4')
      .attr('opacity', 0.5)

    g.append('text')
      .attr('x', width - 5)
      .attr('y', yScale(100) - 5)
      .attr('text-anchor', 'end')
      .attr('fill', 'oklch(0.50 0.01 250)')
      .style('font-family', 'IBM Plex Sans, sans-serif')
      .style('font-size', '11px')
      .text('Base (100)')

    const wageData = parsedDates.map((d, i) => ({ date: d, value: wageIndexed[i] }))
    const basketData = parsedDates.map((d, i) => ({ date: d, value: basketIndexed[i] }))

    const line = d3.line<{ date: Date; value: number }>()
      .x(d => xScale(d.date))
      .y(d => yScale(d.value))
      .curve(d3.curveMonotoneX)

    g.append('path')
      .datum(wageData)
      .attr('fill', 'none')
      .attr('stroke', 'oklch(0.55 0.22 250)')
      .attr('stroke-width', 3)
      .attr('d', line)

    g.append('path')
      .datum(basketData)
      .attr('fill', 'none')
      .attr('stroke', 'oklch(0.62 0.20 30)')
      .attr('stroke-width', 3)
      .attr('d', line)

    const legend = g.append('g')
      .attr('transform', `translate(${width + 10}, 0)`)

    legend.append('line')
      .attr('x1', 0)
      .attr('x2', 30)
      .attr('y1', 10)
      .attr('y2', 10)
      .attr('stroke', 'oklch(0.55 0.22 250)')
      .attr('stroke-width', 3)

    legend.append('text')
      .attr('x', 35)
      .attr('y', 10)
      .attr('dy', '0.32em')
      .attr('fill', 'oklch(0.20 0.01 250)')
      .style('font-family', 'IBM Plex Sans, sans-serif')
      .style('font-size', '13px')
      .text(wageLabel)

    legend.append('line')
      .attr('x1', 0)
      .attr('x2', 30)
      .attr('y1', 35)
      .attr('y2', 35)
      .attr('stroke', 'oklch(0.62 0.20 30)')
      .attr('stroke-width', 3)

    legend.append('text')
      .attr('x', 35)
      .attr('y', 35)
      .attr('dy', '0.32em')
      .attr('fill', 'oklch(0.20 0.01 250)')
      .style('font-family', 'IBM Plex Sans, sans-serif')
      .style('font-size', '13px')
      .text('Basket Cost')

    g.append('text')
      .attr('x', width / 2)
      .attr('y', height + 60)
      .attr('text-anchor', 'middle')
      .attr('fill', 'oklch(0.50 0.01 250)')
      .style('font-family', 'IBM Plex Sans, sans-serif')
      .style('font-size', '12px')
      .text('Date')

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -45)
      .attr('text-anchor', 'middle')
      .attr('fill', 'oklch(0.50 0.01 250)')
      .style('font-family', 'IBM Plex Sans, sans-serif')
      .style('font-size', '12px')
      .text('Index (Base = 100)')

  }, [dates, wageIndexed, basketIndexed, wageLabel])

  return (
    <div ref={containerRef} className="w-full">
      <svg ref={svgRef}></svg>
    </div>
  )
}
