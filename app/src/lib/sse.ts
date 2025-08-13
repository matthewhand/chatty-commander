export interface SSEHandlers {
  chunk?: (data: { id: string; delta: string }) => void;
  tool_call?: (data: any) => void;
  tool_result?: (data: any) => void;
  done?: () => void;
  error?: (err: any) => void;
}

export async function sse(url: string, body: any, handlers: SSEHandlers) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  if (!res.body) {
    handlers.done?.();
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';
      for (const part of parts) {
        const lines = part.split('\n');
        let event = '';
        let data = '';
        for (const line of lines) {
          if (line.startsWith('event:')) event = line.replace('event:', '').trim();
          if (line.startsWith('data:')) data += line.replace('data:', '').trim();
        }
        if (event === 'chunk') {
          handlers.chunk?.(JSON.parse(data));
        } else if (event === 'tool_call') {
          handlers.tool_call?.(JSON.parse(data));
        } else if (event === 'tool_result') {
          handlers.tool_result?.(JSON.parse(data));
        } else if (event === 'done') {
          handlers.done?.();
        }
      }
    }
  } catch (err) {
    handlers.error?.(err);
  }
}
