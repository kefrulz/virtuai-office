import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE_URL || '';

function App() {
  const [agents, setAgents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState({ title: '', description: '', priority: 'medium' });
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);

  useEffect(() => {
    fetchAgents();
    fetchTasks();
    fetchSystemStatus();
    
    // Refresh tasks every 5 seconds
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/agents`);
      const data = await response.json();
      setAgents(data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/tasks`);
      const data = await response.json();
      setTasks(data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const createTask = async (e) => {
    e.preventDefault();
    if (!newTask.title || !newTask.description) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTask),
      });

      if (response.ok) {
        const task = await response.json();
        setTasks([...tasks, task]);
        setNewTask({ title: '', description: '', priority: 'medium' });
        setTimeout(fetchTasks, 1000);
      }
    } catch (error) {
      console.error('Error creating task:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAgentName = (agentId) => {
    const agent = agents.find(a => a.id === agentId);
    return agent ? agent.name : 'Unknown Agent';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'in_progress': return '#3b82f6';
      case 'failed': return '#ef4444';
      default: return '#f59e0b';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 VirtuAI Office</h1>
        <p>Your Complete AI Development Team</p>
        {systemStatus && (
          <div className="status-bar">
            <span className={`status ${systemStatus.status}`}>
              🟢 System {systemStatus.status}
            </span>
            <span>👥 {agents.length} Agents</span>
            <span>⚡ {systemStatus.active_tasks} Active</span>
            <span>✅ {systemStatus.completed_tasks} Completed</span>
          </div>
        )}
      </header>

      <main className="main-content">
        <section className="agents-section">
          <h2>👥 Your AI Team</h2>
          <div className="agents-grid">
            {agents.map((agent) => (
              <div key={agent.id} className="agent-card">
                <h3>{agent.name}</h3>
                <p className="role">{agent.role}</p>
                <p className="description">{agent.description}</p>
                <div className="agent-stats">
                  <span className="status available">🟢 Available</span>
                  <span>✅ {agent.tasks_completed} completed</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="create-task-section">
          <h2>📝 Create New Task</h2>
          <form onSubmit={createTask} className="task-form">
            <div className="form-group">
              <label>Task Title:</label>
              <input
                type="text"
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                placeholder="e.g., Create user login form"
                required
              />
            </div>
            <div className="form-group">
              <label>Description:</label>
              <textarea
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                placeholder="Describe what you want the AI team to build..."
                rows="3"
                required
              />
            </div>
            <div className="form-group">
              <label>Priority:</label>
              <select
                value={newTask.priority}
                onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? '🔄 Creating...' : '🚀 Create Task'}
            </button>
          </form>
        </section>

        <section className="tasks-section">
          <h2>📋 Recent Tasks</h2>
          <div className="tasks-list">
            {tasks.length === 0 ? (
              <div className="no-tasks">
                <p>🎯 No tasks yet. Create your first task above!</p>
                <p>Try: "Create a responsive navigation menu" or "Write user login API"</p>
              </div>
            ) : (
              tasks.slice(-10).reverse().map((task) => (
                <div key={task.id} className="task-card">
                  <div className="task-header">
                    <h3>{task.title}</h3>
                    <span
                      className="task-status"
                      style={{ backgroundColor: getStatusColor(task.status) }}
                    >
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="task-description">{task.description}</p>
                  <div className="task-meta">
                    <span>👤 {getAgentName(task.assigned_agent)}</span>
                    <span>⚡ {task.priority}</span>
                    {task.created_at && (
                      <span>📅 {new Date(task.created_at).toLocaleString()}</span>
                    )}
                  </div>
                  {task.output && (
                    <details className="task-output">
                      <summary>📄 View Generated Output</summary>
                      <pre>{task.output}</pre>
                    </details>
                  )}
                  {task.error && (
                    <div className="task-error">
                      <strong>❌ Error:</strong> {task.error}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>
      </main>

      <footer className="App-footer">
        <p>🤖 VirtuAI Office - Your AI Development Team is Ready!</p>
        <p>Alice • Marcus • Sarah • Luna • TestBot</p>
      </footer>
    </div>
  );
}

export default App;
