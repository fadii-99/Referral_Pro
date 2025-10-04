# Client-Side Read State Implementation Guide

## Overview
The server now sends **dual-perspective** read states for each message:
1. **Viewer perspective**: `is_read_by_me` - whether the current user has read this message
2. **Sender perspective**: `read_by_user_ids`, `read_by_others_count`, `read_by_all_others` - who else has read the sender's message

This enables proper double-tick/read receipt functionality for all roles (solo, company, employee).

---

## Message Data Structure

```typescript
type ChatMessage = {
  id: number;
  room_id: string;
  sender: {
    id: number;
    name: string;
    role: string;
    image_url: string | null;
  };
  content: string;
  message_type: 'text' | 'image' | 'document' | 'file';
  created_at: string;

  // VIEWER PERSPECTIVE (recipient)
  is_read_by_me: boolean;          // Has the viewer read this message?

  // SENDER PERSPECTIVE (for "others read" indicators)
  read_by_user_ids: number[];      // User IDs who read (excluding sender)
  read_by_others_count: number;    // How many others read this
  read_by_all_others: boolean;     // Did all other participants read this?

  // Legacy fields (kept for backwards compatibility)
  is_read: boolean;                // Same as is_read_by_me
  read_by: number[];               // All user IDs who read (including viewer)

  // File fields (for media messages)
  file_url?: string;
  file_name?: string;
  file_size?: number;
  file_type?: string;
  // ... other file metadata
};
```

---

## Rendering Logic

### For messages YOU received (not sent by you):
```typescript
// Show as "read" if you've read it
const showAsRead = message.is_read_by_me;
```

### For messages YOU sent:
```typescript
// 1:1 chat - show double-tick if anyone read it
const showDoubleTick = message.read_by_others_count >= 1;

// Group chat - show avatars/count of who read
const readAvatars = message.read_by_user_ids.map(userId => 
  participants.find(p => p.id === userId)
);

// Optional: show "all read" indicator
const allRead = message.read_by_all_others;
```

---

## WebSocket Event Handling

### Structure of `message_read_update` event:
```typescript
type MessageReadUpdateEvent = {
  type: 'message_read_update';
  room_id: string;
  user_id: number;              // Who read the messages
  user_name: string;
  message_ids: number[];        // Specific message IDs (may be empty)
  last_read_message_id: number; // Cutoff pointer for bulk updates
  read_at: string;              // ISO timestamp
  timestamp: string;            // ISO timestamp
  mark_all?: boolean;           // True if this was "mark all read"
};
```

### Update State on Read Event:
```typescript
const onMessageReadUpdate = (event: MessageReadUpdateEvent) => {
  const { room_id, user_id, message_ids, last_read_message_id } = event;
  
  // Only update if this is the current room
  if (currentRoomId !== room_id) return;

  setMessages(prevMessages => prevMessages.map(msg => {
    // Use cutoff pointer if provided (efficient for bulk updates)
    if (typeof last_read_message_id === 'number') {
      // Mark all messages up to this ID
      if (msg.id <= last_read_message_id && msg.sender.id !== user_id) {
        const updatedReadBy = new Set(msg.read_by_user_ids);
        updatedReadBy.add(user_id);
        
        const newReadByArray = Array.from(updatedReadBy);
        const newCount = newReadByArray.length;
        const othersCount = participantsCount - 1; // Exclude sender
        
        return {
          ...msg,
          read_by_user_ids: newReadByArray,
          read_by_others_count: newCount,
          read_by_all_others: newCount === othersCount,
        };
      }
      return msg;
    }

    // Otherwise use specific message IDs
    if (Array.isArray(message_ids) && message_ids.includes(msg.id)) {
      // Don't add reader to their own sent messages
      if (msg.sender.id === user_id) {
        return msg;
      }

      const updatedReadBy = new Set(msg.read_by_user_ids);
      updatedReadBy.add(user_id);
      
      const newReadByArray = Array.from(updatedReadBy);
      const newCount = newReadByArray.length;
      const othersCount = participantsCount - 1;
      
      return {
        ...msg,
        read_by_user_ids: newReadByArray,
        read_by_others_count: newCount,
        read_by_all_others: newCount === othersCount,
      };
    }

    return msg;
  }));
};
```

---

## Optimistic Updates

### When you send a message:
```typescript
const sendMessage = async (content: string) => {
  // Optimistically add to state
  const tempMessage: ChatMessage = {
    id: Date.now(), // Temporary ID
    room_id: currentRoomId,
    sender: currentUser,
    content,
    message_type: 'text',
    created_at: new Date().toISOString(),
    
    // Sender automatically "reads" their own message
    is_read_by_me: true,
    
    // No one else has read it yet
    read_by_user_ids: [],
    read_by_others_count: 0,
    read_by_all_others: false,
    
    is_read: true,
    read_by: [currentUser.id],
  };
  
  setMessages(prev => [...prev, tempMessage]);
  
  // Send via WS or REST
  await chatApi.sendMessage(currentRoomId, content);
};
```

### When opening a room (mark all read):
```typescript
const openRoom = async (roomId: string) => {
  setCurrentRoomId(roomId);
  
  // Fetch messages
  const messages = await chatApi.getMessages(roomId);
  setMessages(messages);
  
  // Optimistically mark as read
  setMessages(prev => prev.map(msg => 
    msg.sender.id !== currentUser.id 
      ? { ...msg, is_read_by_me: true }
      : msg
  ));
  
  // Tell server
  await chatApi.markAllRead(roomId);
  
  // WS event will update other clients
};
```

---

## Common Pitfalls to Avoid

### ❌ DON'T:
```typescript
// Don't add reader to sender's sent messages
if (msg.id === readMessageId) {
  msg.read_by_user_ids.push(user_id); // WRONG if msg.sender.id === user_id
}

// Don't use single is_read for all perspectives
const showDoubleTick = message.is_read; // WRONG - this is viewer-centric
```

### ✅ DO:
```typescript
// Only update read state for messages NOT sent by the reader
if (msg.id === readMessageId && msg.sender.id !== user_id) {
  const updated = new Set(msg.read_by_user_ids);
  updated.add(user_id);
  msg.read_by_user_ids = Array.from(updated);
}

// Use correct perspective
const showDoubleTick = message.read_by_others_count > 0; // CORRECT
```

---

## Full Example: Message Bubble Component

```tsx
const MessageBubble = ({ message, currentUserId, participants }) => {
  const isMine = message.sender.id === currentUserId;
  
  if (isMine) {
    // My message - show "others read" status
    return (
      <div className="my-message">
        <p>{message.content}</p>
        
        {/* Double-tick indicator */}
        {message.read_by_others_count > 0 ? (
          <CheckCheckIcon color={message.read_by_all_others ? "blue" : "gray"} />
        ) : (
          <CheckIcon />
        )}
        
        {/* Optional: show who read in group chat */}
        {participants.length > 2 && message.read_by_user_ids.length > 0 && (
          <div className="read-avatars">
            {message.read_by_user_ids.map(userId => (
              <Avatar key={userId} user={participants.find(p => p.id === userId)} />
            ))}
          </div>
        )}
      </div>
    );
  } else {
    // Their message - show "I read" status
    return (
      <div className="their-message">
        <Avatar user={message.sender} />
        <p>{message.content}</p>
        {/* No read indicator on their messages from my perspective */}
      </div>
    );
  }
};
```

---

## Testing Checklist

- [ ] Solo user sends message to company → company reads → solo sees double-tick
- [ ] Company sends to solo → solo reads → company sees double-tick
- [ ] Employee sends to solo → solo reads → employee sees double-tick
- [ ] Mark all read updates all messages correctly
- [ ] Read state persists after reconnecting WebSocket
- [ ] No "ghost unread" badges after marking read
- [ ] Sender doesn't count in their own `read_by_user_ids`
- [ ] `last_read_message_id` efficiently marks multiple messages
- [ ] Group chat shows all participants who read (when > 2 people)

---

## API Endpoints Reference

### GET `/api/chat/rooms/{room_id}/`
Returns messages with full read state:
```json
{
  "messages": [
    {
      "id": 123,
      "content": "Hello",
      "is_read_by_me": true,
      "read_by_user_ids": [45, 67],
      "read_by_others_count": 2,
      "read_by_all_others": true
    }
  ]
}
```

### POST `/api/chat/rooms/{room_id}/mark-read/`
Body: `{ "message_ids": [123, 124] }` or `{ "message_id": 123 }`

Broadcasts:
```json
{
  "type": "message_read_update",
  "user_id": 45,
  "message_ids": [123, 124],
  "last_read_message_id": 124,
  "read_at": "2025-10-04T12:34:56Z"
}
```

### POST `/api/chat/rooms/{room_id}/mark-all-read/`
Marks all unread messages, broadcasts with `last_read_message_id` cutoff.

---

## Questions?

- **Q: Why both `is_read_by_me` and `is_read`?**
  A: Backwards compatibility. New code should use `is_read_by_me` for clarity.

- **Q: Why exclude sender from `read_by_user_ids`?**
  A: Senders implicitly "read" their own messages. This array is for showing *others* who read.

- **Q: What if I want a "delivered" vs "read" distinction?**
  A: Add a `delivered_to_user_ids` field using similar logic, tracking when messages arrive at clients (not yet implemented).

