import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import CopilotChat from './CopilotChat'
import * as api from '../lib/api'

// Mock the scrollIntoView to prevent errors in JSDOM
window.HTMLElement.prototype.scrollIntoView = vi.fn()

vi.mock('../lib/api', () => ({
  sendCopilotMessage: vi.fn(),
}))

vi.mock('../components/VillageContext', () => ({
  useVillageContext: () => ({
    selectedLgdCode: null,
  }),
}))

describe('CopilotChat Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders initial empty state with examples', () => {
    render(<CopilotChat />)
    expect(screen.getByText('Intelligence Copilot')).toBeInTheDocument()
    expect(screen.getByText('PUBLIC EVIDENCE ONLY')).toBeInTheDocument()
    expect(screen.getByText('Ask questions about civic analytics data.')).toBeInTheDocument()

    // Check for examples
    expect(screen.getByText('"What is the current reported household tap-connection gap?"')).toBeInTheDocument()
  })

  it('handles user input and API success', async () => {
    vi.mocked(api.sendCopilotMessage).mockResolvedValueOnce({
      text: 'The gap is 50%.',
      status: 'success',
      metadata: {
        tool_calls: [],
        provenance: []
      }
    })

    render(<CopilotChat />)
    const input = screen.getByPlaceholderText('Ask a question...')
    const button = screen.getByRole('button', { name: /send/i })

    // User types and submits
    fireEvent.change(input, { target: { value: 'What is the gap?' } })
    fireEvent.click(button)

    // User message should appear
    expect(screen.getByText('What is the gap?')).toBeInTheDocument()
    expect(input).toHaveValue('')

    // Loading state is tricky to test, but we can wait for response
    await waitFor(() => {
      expect(screen.getByText('The gap is 50%.')).toBeInTheDocument()
    })

    // Internal API should have been called
    expect(api.sendCopilotMessage).toHaveBeenCalledWith('What is the gap?')
  })

  it('handles API error gracefully', async () => {
    vi.mocked(api.sendCopilotMessage).mockRejectedValueOnce(new Error('Internal error'))

    render(<CopilotChat />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question...'), { target: { value: 'Break it' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(screen.getByText('Internal error')).toBeInTheDocument()
    })
  })

  it('renders provenance metadata when supplied', async () => {
    vi.mocked(api.sendCopilotMessage).mockResolvedValueOnce({
      text: 'Here is the data.',
      status: 'success',
      metadata: {
        tool_calls: [{ name: 'get_analytics', args: {} }],
        provenance: [{ source_dataset: 'Official Survey Data', calculation_version: '1.0' }]
      }
    })

    render(<CopilotChat />)

    fireEvent.change(screen.getByPlaceholderText('Ask a question...'), { target: { value: 'Give data' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))

    await waitFor(() => {
      expect(screen.getByText('Official Survey Data')).toBeInTheDocument()
    })
  })

  it('prevents submission when input is empty or loading', async () => {
    render(<CopilotChat />)
    const button = screen.getByRole('button', { name: /send/i })

    expect(button).toBeDisabled()

    fireEvent.change(screen.getByPlaceholderText('Ask a question...'), { target: { value: '  ' } })
    expect(button).toBeDisabled()
  })
})
