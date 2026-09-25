# NL → SQL Query Builder

An AI-powered natural language interface for querying a SQLite database.

Instead of writing SQL manually, users can type questions in plain English such as:

> Show employees whose salary is greater than 50000

The application uses Groq AI to convert the natural-language request into a SQL `SELECT` query, validates the generated query, executes it safely against a read-only SQLite database, and displays the results in the web interface.

---

## 🚀 Live Demo

https://nl-sql-query-builder-frontend.onrender.com

---

## ✨ Features

- Convert natural language into SQL queries
- AI-powered SQL generation using Groq
- Automatic database schema detection
- SQLite database integration
- Support for `JOIN` queries
- Support for filtering, sorting, aggregation, and grouping
- SQL validation before execution
- Read-only database connection
- Protection against database modification commands
- Interactive query results
- FastAPI backend
- Responsive web interface

---

## 🧠 How It Works

The application follows this workflow:

```text
User
  │
  │ Natural-language question
  ↓
Frontend
  │
  │ HTTP POST request
  ↓
FastAPI Backend
  │
  ├── Reads database schema
  │
  ├── Sends question + schema to Groq
  │
  ↓
Groq AI
  │
  │ Generates SQL
  ↓
SQL Validation
  │
  ├── SELECT-only validation
  ├── Multiple-statement protection
  ├── SQL comment protection
  └── SQLite authorizer
  │
  ↓
Read-only SQLite Database
  │
  ↓
Query Results
  │
  ↓
Frontend
