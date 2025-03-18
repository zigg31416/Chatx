# 🕹️ Retro Chat

A nostalgic, temporary chatroom application with a vibrant 80s/90s retro aesthetic. Create or join chatrooms with a flashy UI featuring neon colors, pixelated fonts, and retro effects.

## ✨ Features

- **Host a Chatroom**: Create a room with a unique 5-digit code
- **Join a Chatroom**: Enter an existing room with a code
- **Real-Time Messaging**: Chat with glitch effects and retro styling
- **User Approval**: Hosts can approve or reject join requests
- **Exit Notifications**: Get notified when users leave
- **Temporary Chats**: No history, just in-the-moment conversations

## 🚀 Tech Stack

- **Frontend & Backend**: Streamlit (Python)
- **Database & Real-time**: Supabase
- **Styling**: Custom CSS with retro effects

## 📋 Prerequisites

- Python 3.7+
- A Supabase account (free tier works fine)

## 🛠️ Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
   
   Alternatively, add these to your Streamlit secrets.toml file.

4. Set up Supabase tables:
   - `chatrooms`: For storing chatroom information
   - `messages`: For storing chat messages
   - `join_requests`: For handling join requests

## 📊 Database Schema

### chatrooms
```sql
create table chatrooms (
  id uuid default uuid_generate_v4() primary key,
  name text not null,
  code text not null unique,
  host_name text not null,
  is_active boolean default true,
  created_at timestamp with time zone default now()
);
```

### messages
```sql
create table messages (
  id uuid default uuid_generate_v4() primary key,
  chatroom_id uuid references chatrooms(id),
  username text not null,
  content text not null,
  type text default 'user',
  created_at timestamp with time zone default now()
);
```

### join_requests
```sql
create table join_requests (
  id uuid default uuid_generate_v4() primary key,
  chatroom_id uuid references chatrooms(id),
  username text not null,
  status text default 'pending',
  created_at timestamp with time zone default now()
);
```

## 🚀 Running the Application

```
streamlit run app.py
```

## 🌐 Deployment

This application can be easily deployed to Streamlit Community Cloud:

1. Push the code to a GitHub repository
2. Connect your repository to Streamlit Community Cloud
3. Add your Supabase credentials in the secrets management section
4. Deploy!

## 🎮 Usage

1. **Host**: Create a new chatroom and share the 5-digit code
2. **Join**: Use the code to send a join request to an existing room
3. **Chat**: Once approved, start chatting with others
4. **Exit**: Leave the chatroom when done

## 📷 Screenshots

(Add screenshots of your application here)

## 🔒 Privacy

- No user data is stored permanently
- Chats exist only as long as the room is active
- No registration or personal information required

## 🔮 Future Enhancements

- Sound toggle option
- Custom avatars with pixel art
- Themed chatrooms with different visual styles
- Text formatting options with retro effects
- File sharing with "floppy disk" UI
