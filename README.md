# Real-Time Chat Application – Backend

This repository contains the backend implementation of a real-time one-to-one chat application built using **Django** and **Django REST Framework**.  
It provides secure REST APIs for authentication, messaging, user presence tracking, and access control.

---

## 🚀 Features

- JWT-based authentication (access & refresh tokens)
- Secure user registration using a secret access code
- One-to-one private messaging
- Message delivery and read receipts (✓ / ✓✓)
- Unread message count per user
- Online / offline user presence tracking
- User blocking and unblock functionality
- CORS and CSRF protection for frontend integration
- Production-ready configuration with environment variables

---

## 🛠 Tech Stack

- **Backend Framework:** Django, Django REST Framework  
- **Authentication:** JWT (SimpleJWT)  
- **Database:** SQLite (easily extendable to PostgreSQL)  
- **Security:** JWT Auth, CORS, CSRF, environment-based secrets  
- **Deployment:** PythonAnywhere  

---

## 🔐 Authentication Flow

1. User logs in with username and password.
2. Backend returns JWT access and refresh tokens.
3. Access token is sent in the `Authorization` header for protected APIs.
4. Backend validates the token for each request.

---

## 💬 Messaging Workflow

- Messages are stored persistently in the database.
- Each message tracks sender, receiver, timestamp, and read status.
- When a user opens a chat, unread messages are marked as read.
- Read status is reflected as single or double ticks on the frontend.

---

## 👤 User Presence

- User activity is tracked using a `last_seen` timestamp.
- If the user is active within a defined time window, they appear **online**.
- Otherwise, they appear **offline** with last seen information.

---

## 🚫 Blocking System

- Users can block or unblock other users.
- Blocked users cannot send messages to each other.
- Block status is checked before message creation.





## 📂 Project Structure

