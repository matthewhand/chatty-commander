export interface ChunkEvent {
  type: 'chunk';
  id: string;
  delta: string;
}

export interface ToolCallEvent {
  type: 'tool_call';
  id: string;
  name: string;
  args: Record<string, any>;
}

export interface ToolResultEvent {
  type: 'tool_result';
  id: string;
  result: string;
}

export type ChatEvent = ChunkEvent | ToolCallEvent | ToolResultEvent;

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Simple mock that streams text and issues a faux tool call/result
export async function* chat(messages: any[]): AsyncGenerator<ChatEvent> {
  const assistantId = 'assistant-0';
  const text = 'hello there';
  for (const char of text.split('')) {
    yield { type: 'chunk', id: assistantId, delta: char };
    if (char.trim()) await sleep(20);
  }

  const toolId = 'tool-0';
  yield { type: 'tool_call', id: toolId, name: 'time', args: {} };
  await sleep(50);
  yield { type: 'tool_result', id: toolId, result: 'noon' };
}
