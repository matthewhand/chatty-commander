import React, { memo } from 'react';

export interface ChatMessage {
  content?: React.ReactNode;
  text?: string; // Compatibility
  sender?: string;
  timestamp?: string;
  time?: string; // Compatibility
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
    <div className={`flex flex-col gap-4 ${className}`.trim()}>
      {messages.map((msg, idx) => {
        const bubbleVariant = msg.variant ? `chat-bubble-${msg.variant}` : defaultBubbleVariant;
        const sender = msg.sender || (msg.isUser ? 'User' : 'System');
        
        return (
        <div key={idx} className={`chat ${msg.isUser ? 'chat-end' : 'chat-start'}`}>
          {msg.avatar && (
            <div className="chat-image avatar placeholder">
              <div className="bg-neutral text-neutral-content rounded-full w-10">
                {msg.avatar.length <= 2 ? (
                  <span>{msg.avatar}</span>
                ) : (
                  <img src={msg.avatar} alt={sender} />
                )}
              </div>
            </div>
          )}
          <div className="chat-header mb-1">
            {sender}
            {(msg.timestamp || msg.time) && (
              <time className="text-[10px] opacity-50 ml-2">{msg.timestamp || msg.time}</time>
            )}
          </div>
          <div className={`chat-bubble shadow-sm ${bubbleVariant}`.trim()}>
            {msg.content || msg.text}
          </div>
        </div>
      )})}
    </div>
  );
});

Chat.displayName = 'Chat';

export default Chat;
