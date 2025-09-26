// Mock API service for agent status
// In a real implementation, this would connect to your backend API

export interface Agent {
  id: string;
  name: string;
  status: "online" | "offline" | "error" | "processing";
  lastMessageSent: string;
  lastMessageReceived: string;
  lastMessageContent: string;
  error?: string;
}

export const fetchAgentStatus = async (): Promise<Agent[]> => {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 500));

  // Return mock data
  return [
    {
      id: "agent-1",
      name: "Customer Support Agent",
      status: "online",
      lastMessageSent: "2 minutes ago",
      lastMessageReceived: "5 minutes ago",
      lastMessageContent: "Hello, how can I help you?",
    },
    {
      id: "agent-2",
      name: "Technical Support Agent",
      status: "processing",
      lastMessageSent: "10 minutes ago",
      lastMessageReceived: "12 minutes ago",
      lastMessageContent: "I need help with my account.",
    },
    {
      id: "agent-3",
      name: "Sales Agent",
      status: "error",
      lastMessageSent: "1 hour ago",
      lastMessageReceived: "1 hour ago",
      lastMessageContent: "Checking inventory",
      error: "Connection timeout to inventory service",
    },
  ];
};
