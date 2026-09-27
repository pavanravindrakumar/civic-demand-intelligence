import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import AnalyticsOverview from './AnalyticsOverview'
import * as api from '../lib/api'

vi.mock('../lib/api', () => ({
  getAnalyticsSummary: vi.fn(),
}))

describe('AnalyticsOverview Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    // Provide a promise that doesn't resolve immediately
    vi.mocked(api.getAnalyticsSummary).mockImplementation(() => new Promise(() => {}))
    const { container } = render(<AnalyticsOverview />)

    // Check if loading placeholder elements are present (we used animate-pulse class)
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('renders summary data on success', async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValueOnce({
      total_villages_analyzed: 100,
      total_households: 5000,
      total_fhtc: 2000,
      total_reported_household_gap: 3000,
      readiness_state: 'READY',
      calculation_version: 'v1.0',
      data_source: 'LOCAL_CSV'
    })

    render(<AnalyticsOverview />)

    await waitFor(() => {
      expect(screen.getByText('National Overview')).toBeInTheDocument()
    })

    expect(screen.getByText('READY')).toBeInTheDocument()
    expect(screen.getByText('Ver: v1.0')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument() // villages
    expect(screen.getByText('5,000')).toBeInTheDocument() // households
    expect(screen.getByText('2,000')).toBeInTheDocument() // fhtc
    expect(screen.getByText('3,000')).toBeInTheDocument() // gap
  })

  it('renders PUBLIC EVIDENCE ONLY warning properly', async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValueOnce({
      total_villages_analyzed: 100,
      total_households: 5000,
      total_fhtc: 2000,
      total_reported_household_gap: 3000,
      readiness_state: 'PUBLIC_EVIDENCE_ONLY',
      calculation_version: 'v1.0',
      data_source: 'LOCAL_CSV'
    })

    render(<AnalyticsOverview />)

    await waitFor(() => {
      expect(screen.getByText('PUBLIC EVIDENCE ONLY')).toBeInTheDocument()
    })
  })

  it('handles API errors', async () => {
    vi.mocked(api.getAnalyticsSummary).mockRejectedValueOnce(new Error('Failed to fetch analytics summary.'))

    render(<AnalyticsOverview />)

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch analytics summary.')).toBeInTheDocument()
    })
  })
})
