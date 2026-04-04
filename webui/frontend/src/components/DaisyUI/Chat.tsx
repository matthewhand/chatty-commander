import React, { memo } from 'react';

export interface ChatMessage {
  content: React.ReactNode;
  sender: string;
  timestamp?: string;
  isUser: boolean;
  avatar?: string;
  variant?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error';
}

export interface ChatProps {
  messages: ChatMessage[];
  variant?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error';
  className?: string;
}

export const Chat = memo(({ messages, variant, className = '' }: ChatProps) => {
  const defaultBubbleVariant = variant ? `chat-bubble-${variant}` : '';

  return (
    <div className={`flex flex-col gap-1 ${className}`.trim()}>
      {messages.map((msg, idx) => {
        const bubbleVariant = msg.variant ? `chat-bubble-${msg.variant}` : defaultBubbleVariant;
        return (
        <div key={idx} className={`chat ${msg.isUser ? 'chat-end' : 'chat-start'}`}>
          {msg.avatar && (
            <div className="chat-image avatar">
              <div className="w-10 rounded-full">
                <img src={msg.avatar} alt={msg.sender} />
              </div>
            </div>
          )}
          <div className="chat-header">
            {msg.sender}
            {msg.timestamp && (
              <time className="text-xs opacity-50 ml-1">{msg.timestamp}</time>
            )}
          </div>
          <div className={`chat-bubble ${bubbleVariant}`.trim()}>
            {msg.content}
          </div>
        </div>
      )})}
    </div>
  );
});

Chat.displayName = 'Chat';

export default Chat;
