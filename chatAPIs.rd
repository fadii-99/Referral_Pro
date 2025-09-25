
## **API Endpoints Overview**

### **Base URL:** `http://your-domain.com/api/chat/`

---

## **1. Chat Rooms Management**

### **Get User's Chat Rooms**
```javascript
GET /api/chat/rooms/
Headers: {
  'Authorization': 'Bearer <token>',
  'Content-Type': 'application/json'
}

// Response
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Chat with John Solo",
      "chat_type": "rep_solo",
      "participants": [
        {
          "id": 2,
          "email": "rep@company.com",
          "full_name": "Rep User",
          "role": "rep"
        },
        {
          "id": 3,
          "email": "solo@user.com", 
          "full_name": "Solo User",
          "role": "solo"
        }
      ],
      "last_message": {
        "id": 10,
        "content": "Hello there!",
        "timestamp": "2025-09-22T10:30:00Z",
        "sender": {
          "id": 2,
          "full_name": "Rep User"
        }
      },
      "unread_count": 3,
      "created_at": "2025-09-22T09:00:00Z"
    }
  ]
}
```

### **Create Chat Room**
```javascript
POST /api/chat/rooms/
Headers: {
  'Authorization': 'Bearer <token>',
  'Content-Type': 'application/json'
}
Body: {
  "participant_id": 3,  // ID of user to chat with
  "chat_type": "rep_solo"  // or "company_solo"
}

// Response
{
  "id": 2,
  "name": "Chat with Solo User",
  "chat_type": "rep_solo",
  "participants": [...],
  "created_at": "2025-09-22T11:00:00Z"
}
```

### **Get Specific Chat Room**
```javascript
GET /api/chat/rooms/{room_id}/
Headers: {
  'Authorization': 'Bearer <token>'
}

// Response: Same as single room object above
```

---

## **2. Messages Management**

### **Get Messages for a Room**
```javascript
GET /api/chat/rooms/{room_id}/messages/?page=1&page_size=20
Headers: {
  'Authorization': 'Bearer <token>'
}

// Response
{
  "count": 45,
  "next": "http://api/chat/rooms/1/messages/?page=2",
  "previous": null,
  "results": [
    {
      "id": 15,
      "content": "Latest message here",
      "message_type": "text",
      "sender": {
        "id": 2,
        "full_name": "Rep User",
        "role": "rep",
        "image": "https://s3.amazonaws.com/profile.jpg"
      },
      "timestamp": "2025-09-22T10:35:00Z",
      "is_read": true,
      "edited_at": null
    },
    {
      "id": 14,
      "content": "Previous message",
      "message_type": "text", 
      "sender": {
        "id": 3,
        "full_name": "Solo User",
        "role": "solo"
      },
      "timestamp": "2025-09-22T10:30:00Z",
      "is_read": true
    }
  ]
}
```

### **Send Message**
```javascript
POST /api/chat/rooms/{room_id}/messages/
Headers: {
  'Authorization': 'Bearer <token>',
  'Content-Type': 'application/json'
}
Body: {
  "content": "Hello! How can I help you?",
  "message_type": "text"
}

// Response
{
  "id": 16,
  "content": "Hello! How can I help you?",
  "message_type": "text",
  "sender": {
    "id": 2,
    "full_name": "Rep User",
    "role": "rep"
  },
  "timestamp": "2025-09-22T10:40:00Z",
  "is_read": false
}
```

### **Mark Messages as Read**
```javascript
POST /api/chat/rooms/{room_id}/mark-read/
Headers: {
  'Authorization': 'Bearer <token>',
  'Content-Type': 'application/json'
}

// Response
{
  "success": true,
  "message": "Messages marked as read"
}
```

---

## **3. WebSocket Connection**

### **WebSocket URL**
```javascript
// WebSocket connection for real-time chat
ws://your-domain.com/ws/chat/{room_id}/

// With authentication token
ws://your-domain.com/ws/chat/{room_id}/?token=<auth_token>
```

### **WebSocket Message Structure**

#### **Sending Messages:**
```javascript
// Send message via WebSocket
const message = {
  type: 'chat_message',
  content: 'Hello there!',
  message_type: 'text'
};
websocket.send(JSON.stringify(message));
```

#### **Receiving Messages:**
```javascript
// Listen for incoming messages
websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'chat_message':
      // New message received
      const newMessage = {
        id: data.message.id,
        content: data.message.content,
        sender: data.message.sender,
        timestamp: data.message.timestamp,
        message_type: data.message.message_type
      };
      break;
      
    case 'user_joined':
      // User joined the chat
      console.log(`${data.user.full_name} joined the chat`);
      break;
      
    case 'user_left':
      // User left the chat
      console.log(`${data.user.full_name} left the chat`);
      break;
      
    case 'typing':
      // User is typing
      console.log(`${data.user.full_name} is typing...`);
      break;
  }
};
```

---

## **4. React Native Implementation Example**

### **Chat Service Class**
```javascript
class ChatService {
  constructor() {
    this.baseURL = 'http://your-domain.com/api/chat';
    this.wsURL = 'ws://your-domain.com/ws/chat';
  }

  // Get user's chat rooms
  async getChatRooms(token) {
    const response = await fetch(`${this.baseURL}/rooms/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  // Create new chat room
  async createChatRoom(token, participantId, chatType) {
    const response = await fetch(`${this.baseURL}/rooms/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        participant_id: participantId,
        chat_type: chatType
      })
    });
    return response.json();
  }

  // Get messages for a room
  async getMessages(token, roomId, page = 1) {
    const response = await fetch(`${this.baseURL}/rooms/${roomId}/messages/?page=${page}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.json();
  }

  // Send message via REST API
  async sendMessage(token, roomId, content, messageType = 'text') {
    const response = await fetch(`${this.baseURL}/rooms/${roomId}/messages/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content,
        message_type: messageType
      })
    });
    return response.json();
  }

  // Mark messages as read
  async markAsRead(token, roomId) {
    const response = await fetch(`${this.baseURL}/rooms/${roomId}/mark-read/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  // Connect to WebSocket
  connectWebSocket(roomId, token) {
    const ws = new WebSocket(`${this.wsURL}/${roomId}/?token=${token}`);
    return ws;
  }
}
```

### **Usage in React Native Component**
```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TextInput, TouchableOpacity } from 'react-native';

const ChatRoom = ({ roomId, userToken }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [websocket, setWebsocket] = useState(null);
  
  const chatService = new ChatService();

  useEffect(() => {
    // Load initial messages
    loadMessages();
    
    // Connect WebSocket
    const ws = chatService.connectWebSocket(roomId, userToken);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'chat_message') {
        setMessages(prev => [data.message, ...prev]);
      }
    };
    
    setWebsocket(ws);
    
    return () => {
      ws.close();
    };
  }, [roomId]);

  const loadMessages = async () => {
    try {
      const response = await chatService.getMessages(userToken, roomId);
      setMessages(response.results);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const sendMessage = () => {
    if (newMessage.trim() && websocket) {
      // Send via WebSocket for real-time
      websocket.send(JSON.stringify({
        type: 'chat_message',
        content: newMessage,
        message_type: 'text'
      }));
      
      setNewMessage('');
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View>
            <Text>{item.sender.full_name}: {item.content}</Text>
            <Text>{new Date(item.timestamp).toLocaleTimeString()}</Text>
          </View>
        )}
      />
      
      <View style={{ flexDirection: 'row' }}>
        <TextInput
          value={newMessage}
          onChangeText={setNewMessage}
          placeholder="Type a message..."
          style={{ flex: 1, borderWidth: 1, padding: 10 }}
        />
        <TouchableOpacity onPress={sendMessage}>
          <Text>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};
```

---
