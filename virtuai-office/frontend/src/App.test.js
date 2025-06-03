import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import { NotificationProvider } from './components/NotificationSystem';
import ErrorBoundary from './components/ErrorBoundary';

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  close: jest.fn(),
  send: jest.fn()
}));

// Mock fetch
global.fetch = jest.fn();

// Mock API responses
const mockApiResponse = (data) => ({
  ok: true,
  status: 200,
  json: async () => data
});

const mockAgents = [
  {
    id: '1',
    name: 'Alice Chen',
    type: 'product_manager',
    description: 'Senior Product Manager',
    expertise: ['user stories', 'requirements'],
    is_active: true,
    task_count: 5,
    completed_tasks: 4
  },
  {
    id: '2',
    name: 'Marcus Dev',
    type: 'frontend_developer',
    description: 'Senior Frontend Developer',
    expertise: ['react', 'javascript'],
    is_active: true,
    task_count: 8,
    completed_tasks: 6
  }
];

const mockTasks = [
  {
    id: '1',
    title: 'Create login page',
    description: 'Build a responsive login page',
    status: 'completed',
    priority: 'medium',
    agent_id: '2',
    agent_name: 'Marcus Dev',
    output: 'Login component created successfully',
    created_at: '2024-01-01T10:00:00Z'
  }
];

const mockSystemStatus = {
  status: 'healthy',
  ollama_status: 'connected',
  available_models: ['llama2:7b'],
  agents_count: 5
};

// Test wrapper component
const TestWrapper = ({ children }) => (
  <ErrorBoundary>
    <NotificationProvider>
      {children}
    </NotificationProvider>
  </ErrorBoundary>
);

describe('VirtuAI Office App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default fetch mocks
    fetch.mockImplementation((url) => {
      if (url.includes('/api/agents')) {
        return Promise.resolve(mockApiResponse(mockAgents));
      }
      if (url.includes('/api/tasks')) {
        return Promise.resolve(mockApiResponse(mockTasks));
      }
      if (url.includes('/api/projects')) {
        return Promise.resolve(mockApiResponse([]));
      }
      if (url.includes('/api/analytics')) {
        return Promise.resolve(mockApiResponse({
          total_tasks: 10,
          completed_tasks: 8,
          in_progress_tasks: 1,
          pending_tasks: 1,
          completion_rate: 0.8,
          agent_performance: []
        }));
      }
      if (url.includes('/api/status')) {
        return Promise.resolve(mockApiResponse(mockSystemStatus));
      }
      return Promise.reject(new Error('Unknown API endpoint'));
    });
  });

  test('renders VirtuAI Office header', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('VirtuAI Office')).toBeInTheDocument();
    });
  });

  test('displays loading state initially', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    expect(screen.getByText('Loading VirtuAI Office...')).toBeInTheDocument();
  });

  test('loads and displays agents after loading', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Chen')).toBeInTheDocument();
      expect(screen.getByText('Marcus Dev')).toBeInTheDocument();
    });
  });

  test('displays system status when healthy', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });
  });

  test('navigation between tabs works', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Chen')).toBeInTheDocument();
    });

    // Click on Tasks tab
    fireEvent.click(screen.getByText('📋 Tasks'));
    
    await waitFor(() => {
      expect(screen.getByText('All Tasks')).toBeInTheDocument();
    });

    // Click on Agents tab
    fireEvent.click(screen.getByText('🤖 Agents'));
    
    await waitFor(() => {
      expect(screen.getByText('AI Development Team')).toBeInTheDocument();
    });
  });

  test('can open task creation modal', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('+ New Task')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('+ New Task'));

    await waitFor(() => {
      expect(screen.getByText('Create New Task')).toBeInTheDocument();
    });
  });

  test('task creation form validation', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('+ New Task'));
    });

    await waitFor(() => {
      const createButton = screen.getByRole('button', { name: /create task/i });
      fireEvent.click(createButton);
    });

    // Form should not submit without required fields
    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/tasks'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  test('displays task completion notification', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Chen')).toBeInTheDocument();
    });

    // Simulate WebSocket message
    const wsInstance = WebSocket.mock.results[0].value;
    const messageHandler = wsInstance.addEventListener.mock.calls
      .find(call => call[0] === 'message')[1];

    messageHandler({
      data: JSON.stringify({
        type: 'task_completed',
        task_id: '1',
        agent_name: 'Marcus Dev'
      })
    });

    await waitFor(() => {
      expect(screen.getByText(/Marcus Dev completed/)).toBeInTheDocument();
    });
  });

  test('handles API errors gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('API Error'));

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Should still render without crashing
    await waitFor(() => {
      expect(screen.getByText('VirtuAI Office')).toBeInTheDocument();
    });
  });

  test('agent performance display', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check for completion rates
      expect(screen.getByText('80% success')).toBeInTheDocument();
      expect(screen.getByText('75% success')).toBeInTheDocument();
    });
  });

  test('task status filtering', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Navigate to tasks tab
    await waitFor(() => {
      fireEvent.click(screen.getByText('📋 Tasks'));
    });

    await waitFor(() => {
      expect(screen.getByText('All Tasks')).toBeInTheDocument();
    });

    // Task status filters should be present
    expect(screen.getByDisplayValue('All Statuses')).toBeInTheDocument();
    expect(screen.getByDisplayValue('All Priorities')).toBeInTheDocument();
  });

  test('task details modal functionality', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      fireEvent.click(screen.getByText('📋 Tasks'));
    });

    await waitFor(() => {
      const viewDetailsButton = screen.getByText('View Details');
      fireEvent.click(viewDetailsButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Create login page')).toBeInTheDocument();
      expect(screen.getByText('Login component created successfully')).toBeInTheDocument();
    });
  });

  test('agent workload indicators', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should show task counts for agents
      expect(screen.getByText('4 / 5 tasks')).toBeInTheDocument();
      expect(screen.getByText('6 / 8 tasks')).toBeInTheDocument();
    });
  });

  test('responsive design elements', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      const dashboard = screen.getByText('VirtuAI Office');
      expect(dashboard).toBeInTheDocument();
    });

    // Check for responsive classes (these would be in the DOM)
    const mainElement = document.querySelector('main');
    expect(mainElement).toHaveClass('max-w-7xl', 'mx-auto');
  });

  test('accessibility features', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check for proper ARIA labels and roles
      const navigation = screen.getByRole('navigation', { name: /main navigation/i });
      expect(navigation).toBeInTheDocument();
    });

    // Check for keyboard navigation support
    const firstButton = screen.getByRole('button', { name: /dashboard/i });
    firstButton.focus();
    expect(firstButton).toHaveFocus();
  });

  test('real-time updates via WebSocket', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws');
    });

    const wsInstance = WebSocket.mock.results[0].value;
    expect(wsInstance.addEventListener).toHaveBeenCalledWith('message', expect.any(Function));
    expect(wsInstance.addEventListener).toHaveBeenCalledWith('open', expect.any(Function));
    expect(wsInstance.addEventListener).toHaveBeenCalledWith('close', expect.any(Function));
  });

  test('demo data population', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Navigate to tasks (which shows demo button when no tasks)
    await waitFor(() => {
      fireEvent.click(screen.getByText('📋 Tasks'));
    });

    // Mock empty tasks response
    fetch.mockImplementationOnce(() =>
      Promise.resolve(mockApiResponse([]))
    );

    await waitFor(() => {
      const demoButton = screen.getByText('📝 Create Demo Tasks');
      expect(demoButton).toBeInTheDocument();
      
      fireEvent.click(demoButton);
    });

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/demo/populate',
      expect.objectContaining({ method: 'POST' })
    );
  });
});
