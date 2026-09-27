import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import VillageLookup from './VillageLookup'
import * as api from '../lib/api'
import * as VillageContext from './VillageContext'

vi.mock('../lib/api', () => ({
  getVillageAnalytics: vi.fn(),
}))

vi.mock('./VillageContext', () => ({
  useVillageContext: vi.fn(),
}))

describe('VillageLookup Component', () => {
  const mockSetSelectedVillageContext = vi.fn()
  const mockSetSelectedLgdCode = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(VillageContext.useVillageContext).mockReturnValue({
      selectedLgdCode: null,
      selectedVillageContext: null,
      setSelectedVillageContext: mockSetSelectedVillageContext,
      setSelectedLgdCode: mockSetSelectedLgdCode
    })
  })

  it('renders initial state correctly', () => {
    render(<VillageLookup />)
    expect(screen.getByText('Village Analytics Lookup')).toBeInTheDocument()
    const input = screen.getByPlaceholderText('6-digit LGD Code')
    expect(input).toBeInTheDocument()

    const button = screen.getByRole('button', { name: /lookup/i })
    // Disabled initially because input is empty
    expect(button).toBeDisabled()
  })

  it('allows 6 digit input and submits successfully', async () => {
    vi.mocked(api.getVillageAnalytics).mockResolvedValueOnce({
      lgd_village_code: '123456',
      readiness: 'READY',
      evidence_quality: 'HIGH_CONFIDENCE',
      calculation_version: 'v1.0',
      normalized_gap: 0.5,
      normalized_exposure: 0.5,
      normalized_demand: 0.5,
      reported_household_gap: 50,
      household_exposure: 100,
      priority_score: 0.75
    })

    render(<VillageLookup />)

    const input = screen.getByPlaceholderText('6-digit LGD Code')
    const button = screen.getByRole('button', { name: /lookup/i })

    // Type 6 digits
    fireEvent.change(input, { target: { value: '123456' } })
    expect(button).not.toBeDisabled()

    fireEvent.click(button)

    await waitFor(() => {
      expect(mockSetSelectedLgdCode).toHaveBeenCalledWith('123456')
    })

    expect(mockSetSelectedVillageContext).toHaveBeenCalledWith(expect.objectContaining({
      lgd_village_code: '123456',
      reported_household_gap: 50,
      household_exposure: 100,
      evidence_quality: 'HIGH_CONFIDENCE',
      readiness: 'READY',
      priority_score: 0.75
    }))
  })

  it('handles API errors', async () => {
    vi.mocked(api.getVillageAnalytics).mockRejectedValueOnce(new Error('Village with LGD code 999999 not found.'))

    render(<VillageLookup />)

    fireEvent.change(screen.getByPlaceholderText('6-digit LGD Code'), { target: { value: '999999' } })
    fireEvent.click(screen.getByRole('button', { name: /lookup/i }))

    await waitFor(() => {
      expect(screen.getByText('Village with LGD code 999999 not found.')).toBeInTheDocument()
    })
  })
})
