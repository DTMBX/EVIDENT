import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { PricePoint } from '@/lib/types'

interface PriceChartProps {
  data: Array<{
    itemId: string
    itemName: string
    points: Array<PricePoint & { realPrice?: number, cpiValue?: number }>
    color: string
  }>
  metricMode?: 'nominal' | 'real' | 'hours-of-work'
  hourlyWage?: number
}

export function PriceChart({ data, metricMode = 'nominal', hourlyWage = 15 }: PriceChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 })

  useEffect(() => {
    const handleResize = () => {
      if (svgRef.current?.parentElement) {
        const { width } = svgRef.current.parentElement.getBoundingClientRect()
        setDimensions({ width, height: Math.min(400, width * 0.5) })
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const margin = { top: 20, right: 120, bottom: 60, left: 60 }
    const width = dimensions.width - margin.left - margin.right
    const height = dimensions.height - margin.top - margin.bottom

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    const allPoints = data.flatMap(d => d.points)
    
    const xExtent = d3.extent(allPoints, d => new Date(d.date)) as [Date, Date]
    const x = d3.scaleTime()
      .domain(xExtent)
      .range([0, width])

    const getYValue = (point: PricePoint & { realPrice?: number }) => {
      if (metricMode === 'hours-of-work') {
        return point.nominalPrice / hourlyWage
      }
      if (metricMode === 'real' && point.realPrice) {
        return point.realPrice
      }
      return point.nominalPrice
    }

    const yMax = d3.max(allPoints, getYValue) || 100
    const y = d3.scaleLinear()
      .domain([0, yMax * 1.1])
      .range([height, 0])

    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat((d) => {
        const date = d as Date
        return d3.timeFormat('%b %y')(date)
      }))
      .selectAll('text')
      .style('font-family', 'var(--font-body)')
      .style('font-size', '11px')
      .attr('transform', 'rotate(-45)')
      .style('text-anchor', 'end')
      .attr('dx', '-0.5em')
      .attr('dy', '0.5em')

    const yAxis = g.append('g')
      .call(d3.axisLeft(y))
    
    yAxis.selectAll('text')
      .style('font-family', 'var(--font-mono)')
      .style('font-size', '12px')

    let yLabel = 'Price ($)'
    if (metricMode === 'hours-of-work') {
      yLabel = 'Hours of Work'
    } else if (metricMode === 'real') {
      yLabel = 'Inflation-Adjusted Price (1982 $)'
    }
    
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-family', 'var(--font-body)')
      .style('font-size', '13px')
      .style('fill', 'var(--foreground)')
      .text(yLabel)

    const line = d3.line<PricePoint & { realPrice?: number }>()
      .x(d => x(new Date(d.date)))
      .y(d => y(getYValue(d)))

    data.forEach(series => {
      g.append('path')
        .datum(series.points)
        .attr('fill', 'none')
        .attr('stroke', series.color)
        .attr('stroke-width', 2)
        .attr('d', line)

      const lastPoint = series.points[series.points.length - 1]
      if (lastPoint) {
        g.append('text')
          .attr('x', width + 5)
          .attr('y', y(getYValue(lastPoint)))
          .attr('dy', '0.35em')
          .style('font-family', 'var(--font-body)')
          .style('font-size', '12px')
          .style('fill', series.color)
          .text(series.itemName)
      }
    })

  }, [data, dimensions, metricMode, hourlyWage])

  return (
    <div className="w-full">
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="bg-card"
      />
    </div>
  )
}
