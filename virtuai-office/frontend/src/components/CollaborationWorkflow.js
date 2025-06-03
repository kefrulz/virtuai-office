import React, { useState, useEffect } from 'react';

const CollaborationWorkflow = ({ collaborationPlan, taskTitle, onStepComplete, currentStepIndex = 0 }) => {
  const [activeStep, setActiveStep] = useState(currentStepIndex);
  const [stepResults, setStepResults] = useState({});
  const [isExecuting, setIsExecuting] = useState(false);

  useEffect(() => {
    setActiveStep(currentStepIndex);
  }, [currentStepIndex]);

  if (!collaborationPlan) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">🤖</div>
          <p>No collaboration workflow active</p>
          <p className="text-sm">Complex tasks will automatically trigger team collaboration</p>
        </div>
      </div>
    );
  }

  const getStepStatus = (stepIndex) => {
    if (stepIndex < activeStep) return 'completed';
    if (stepIndex === activeStep) return isExecuting ? 'executing' : 'active';
    return 'pending';
  };

  const getStepIcon = (status, stepIndex) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'executing':
        return '⚡';
      case 'active':
        return stepIndex + 1;
      default:
        return stepIndex + 1;
    }
  };

  const getStepColor = (status) => {
    switch (status) {
      case 'completed':
        return 'border-green-500 bg-green-50 text-green-800';
      case 'executing':
        return 'border-blue-500 bg-blue-50 text-blue-800 animate-pulse';
      case 'active':
        return 'border-blue-500 bg-blue-50 text-blue-800';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-600';
    }
  };

  const getAgentIcon = (agentType) => {
    const agentIcons = {
      'product_manager': '👩‍💼',
      'frontend_developer': '👨‍💻',
      'backend_developer': '👩‍💻',
      'ui_ux_designer': '🎨',
      'qa_tester': '🔍',
      'primary': '🧠'
    };
    return agentIcons[agentType] || '🤖';
  };

  const formatDuration = (hours) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    return `${hours}h`;
  };

  const handleStepClick = (stepIndex) => {
    const status = getStepStatus(stepIndex);
    if (status === 'completed' && stepResults[stepIndex]) {
      // Show step results in modal or expanded view
      console.log('Show results for step:', stepIndex);
    }
  };

  const totalDuration = collaborationPlan.workflow_steps.reduce(
    (sum, step) => sum + (step.duration || 1), 0
  );

  const completedDuration = collaborationPlan.workflow_steps
    .slice(0, activeStep)
    .reduce((sum, step) => sum + (step.duration || 1), 0);

  const progressPercentage = (completedDuration / totalDuration) * 100;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-bold text-gray-900 flex items-center">
            🤝 Team Collaboration
            <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
              {collaborationPlan.collaboration_type}
            </span>
          </h3>
          <div className="text-sm text-gray-500">
            {activeStep + 1} of {collaborationPlan.workflow_steps.length} steps
          </div>
        </div>
        
        <p className="text-gray-600 mb-4">Task: {taskTitle}</p>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{formatDuration(completedDuration)} completed</span>
          <span>{formatDuration(totalDuration)} total</span>
        </div>
      </div>

      {/* Workflow Steps */}
      <div className="space-y-4">
        {collaborationPlan.workflow_steps.map((step, index) => {
          const status = getStepStatus(index);
          const stepColor = getStepColor(status);
          
          return (
            <div
              key={index}
              className={`
                flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
                ${stepColor}
                ${status === 'completed' ? 'hover:shadow-md' : ''}
              `}
              onClick={() => handleStepClick(index)}
            >
              {/* Step Number/Status */}
              <div className={`
                w-10 h-10 rounded-full flex items-center justify-center font-bold mr-4 text-white
                ${status === 'completed' ? 'bg-green-500' : 
                  status === 'executing' ? 'bg-blue-500' :
                  status === 'active' ? 'bg-blue-500' : 'bg-gray-400'}
              `}>
                {getStepIcon(status, index)}
              </div>
              
              {/* Step Content */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-medium">{step.task}</h4>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs px-2 py-1 bg-white bg-opacity-50 rounded">
                      {formatDuration(step.duration)}
                    </span>
                    {status === 'executing' && (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center text-sm">
                  <span className="mr-2">{getAgentIcon(step.agent_type)}</span>
                  <span>
                    {step.agent === 'primary' ? 'Primary Agent' : step.agent}
                  </span>
                  
                  {status === 'completed' && stepResults[index] && (
                    <span className="ml-2 text-xs text-green-600">
                      ✓ View Results
                    </span>
                  )}
                </div>
                
                {/* Step Details for Active/Executing */}
                {(status === 'active' || status === 'executing') && (
                  <div className="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs">
                    <p><strong>Objective:</strong> {step.objective || step.task}</p>
                    {step.dependencies && step.dependencies.length > 0 && (
                      <p><strong>Dependencies:</strong> {step.dependencies.join(', ')}</p>
                    )}
                  </div>
                )}
                
                {/* Step Results Preview for Completed */}
                {status === 'completed' && stepResults[index] && (
                  <div className="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs">
                    <p className="text-green-700">
                      <strong>Completed:</strong> {stepResults[index].summary || 'Step completed successfully'}
                    </p>
                    {stepResults[index].output && (
                      <p className="mt-1 truncate">
                        <strong>Output:</strong> {stepResults[index].output.substring(0, 100)}...
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Collaboration Info */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Type:</span>
            <span className="ml-2 capitalize">{collaborationPlan.collaboration_type.replace('_', ' ')}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Primary Agent:</span>
            <span className="ml-2">{collaborationPlan.primary_agent}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Supporting Agents:</span>
            <span className="ml-2">{collaborationPlan.supporting_agents.length}</span>
          </div>
        </div>
        
        {collaborationPlan.estimated_duration && (
          <div className="mt-2 text-sm">
            <span className="font-medium text-gray-700">Estimated Duration:</span>
            <span className="ml-2">{formatDuration(collaborationPlan.estimated_duration)}</span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex justify-between items-center">
        <div className="text-sm text-gray-500">
          {activeStep === collaborationPlan.workflow_steps.length ? (
            <span className="text-green-600 font-medium">✅ Collaboration Complete</span>
          ) : (
            <span>Step {activeStep + 1}: {collaborationPlan.workflow_steps[activeStep]?.task}</span>
          )}
        </div>
        
        <div className="flex space-x-2">
          {activeStep > 0 && (
            <button
              className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              onClick={() => setActiveStep(Math.max(0, activeStep - 1))}
            >
              Previous
            </button>
          )}
          
          {activeStep < collaborationPlan.workflow_steps.length - 1 && (
            <button
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              onClick={() => setActiveStep(Math.min(collaborationPlan.workflow_steps.length - 1, activeStep + 1))}
            >
              Next
            </button>
          )}
          
          {onStepComplete && (
            <button
              className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
              onClick={() => onStepComplete(activeStep)}
              disabled={isExecuting}
            >
              {isExecuting ? 'Processing...' : 'Complete Step'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Collaboration Types Helper Component
export const CollaborationTypeIndicator = ({ type }) => {
  const getTypeInfo = (collaborationType) => {
    switch (collaborationType) {
      case 'sequential':
        return {
          icon: '→',
          label: 'Sequential',
          description: 'Agents work one after another',
          color: 'bg-blue-100 text-blue-800'
        };
      case 'parallel':
        return {
          icon: '⚡',
          label: 'Parallel',
          description: 'Agents work simultaneously',
          color: 'bg-green-100 text-green-800'
        };
      case 'review':
        return {
          icon: '🔍',
          label: 'Review',
          description: 'One agent reviews another\'s work',
          color: 'bg-purple-100 text-purple-800'
        };
      default:
        return {
          icon: '🤝',
          label: 'Collaborative',
          description: 'Team collaboration',
          color: 'bg-gray-100 text-gray-800'
        };
    }
  };

  const typeInfo = getTypeInfo(type);

  return (
    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${typeInfo.color}`}>
      <span className="mr-1">{typeInfo.icon}</span>
      <span>{typeInfo.label}</span>
    </div>
  );
};

// Sample collaboration plan for testing
export const sampleCollaborationPlan = {
  primary_agent: "Marcus Dev",
  supporting_agents: ["Luna Design", "TestBot QA"],
  collaboration_type: "sequential",
  estimated_duration: 8.5,
  workflow_steps: [
    {
      agent: "Luna Design",
      agent_type: "ui_ux_designer",
      task: "Create wireframes and design specifications",
      duration: 2.0,
      objective: "Design the user interface layout and interaction patterns",
      dependencies: []
    },
    {
      agent: "Marcus Dev",
      agent_type: "frontend_developer",
      task: "Implement React component based on design",
      duration: 4.0,
      objective: "Build the frontend component with all specified functionality",
      dependencies: ["design_specifications"]
    },
    {
      agent: "TestBot QA",
      agent_type: "qa_tester",
      task: "Create test plan and automated tests",
      duration: 2.5,
      objective: "Ensure component meets quality standards and requirements",
      dependencies: ["react_component"]
    }
  ]
};

export default CollaborationWorkflow;
