# FastEat AI

Turn a photo of your ingredients into a delicious recipe with AI-powered analysis.

**FastEat AI** is a professional AI cooking assistant that lets anyone:

1. Upload a photo of ingredients or food
2. Preview the image
3. Click "Generate Recipe"
4. Get a beautifully formatted recipe

The backend uses your existing LangChain agent (Groq + Tavily), and the frontend is a clean static website ready for GitHub Pages.

## Features

- **Vision AI** — Analyze ingredient photos with computer vision
- **Ingredient Recognition** — Identify fruits, vegetables, spices, and more
- **Smart Recipe Generation** — AI-powered recipe creation using web research
- **Web Research** — Real-time internet search for the best matching recipes
- **Simple & Fast** — No login needed, just upload and cook

## Architecture

```
USERS
  │
  ▼
GitHub Pages Website (frontend)
  │
  │ HTTPS
  ▼
FastAPI Backend
  │
  ▼
Existing LangChain Agent
  │
┌──────┴──────┐
▼             ▼
AI Model      Existing Tools (Tavily)
  │
  ▼
Recipe
```

**Frontend:** Static HTML/CSS/JavaScript (GitHub Pages)
**Backend:** Small FastAPI wrapper around your existing agent
**Agent:** LangChain with Groq (qwen/qwen3.8-27b) and Tavily web search

## Project Structure

```
ACL_Agent/
├── src/
│   └── acl_agent/
│       └── __init__.py          # (deprecated, kept for backward compatibility)
│
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   └── recipe_parser.py         # Text → structured recipe parser
│
├── frontend/
│   ├── index.html               # Single-page website
│   ├── style.css                # Custom responsive design
│   └── app.js                   # Frontend logic
│
├── main.py                       # Original CLI (still works)
├── photo_decoder.py             # Image → data URL converter
├── prompt.py                     # Agent prompts
├── tool.py                       # Tavily web search tool
│
├── agent_core.py                 # Shared agent creation (NEW)
├── .env                          # Your API keys (gitignored)
├── .env_example                 # Example environment variables
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

## Requirements

- Python 3.12+
- GROQ_API_KEY (Groq AI model)
- TAVILY_API_KEY (Web search)
- No external frontend dependencies (static HTML/CSS/JS only)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/fasteat-ai.git
   cd fasteat-ai
   ```

2. **Activate your virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   Or using `uv`:
   ```bash
   uv lock
   uv sync
   ```

4. **Set up environment variables:**

   Copy `.env_example` to `.env` and fill in your API keys:
   ```bash
   cp .env_example .env
   ```

   Edit `.env`:
   ```env
   GROQ_API_KEY="your_actual_groq_key"
   TAVILY_API_KEY="your_actual_tavily_key"
   ALLOWED_ORIGINS="http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
   MAX_IMAGE_MB="5"
   ```

## Running the Application

### Backend (FastAPI)

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will start on http://127.0.0.1:8000

**API Endpoints:**

- `GET /api/health` — Health check
  ```json
  { "status": "ok" }
  ```

- `POST /api/recipes/generate` — Generate a recipe from an image
  - **Content-Type:** `multipart/form-data`
  - **Body:** `image` (file)

### Frontend (Static Website)

Start a simple HTTP server in the `frontend` directory:

```bash
python -m http.server 5500 --directory frontend --bind 127.0.0.1
```

The frontend will be available at http://127.0.0.1:5500

### Local Development (Both Together)

**Option 1: Run servers manually:**
1. Terminal 1: `uvicorn backend.main:app --reload`
2. Terminal 2: `python -m http.server 5500 --directory frontend`

**Option 2: Use a single command (alternative):**
```bash
python -m http.server 5500 --directory frontend &
uvicorn backend.main:app --reload
```

Then visit http://127.0.0.1:5500 in your browser.

## Using the CLI

The original CLI still works and is fully preserved:

```bash
python main.py
```

This will:
1. Show a file picker dialog
2. Select an ingredient photo
3. Generate a recipe and print it

## API Reference

### POST /api/recipes/generate

Generate a recipe from an uploaded image.

**Request:**
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `image` (file) — Image file (JPG, PNG, or WEBP, max 5 MB)

**Response:**
```json
{
  "success": true,
  "recipe": {
    "title": "Garlic Butter Pasta",
    "description": "A quick weeknight dinner...",
    "ingredients": [
      {
        "name": "200g spaghetti",
        "amount": "200g",
        "unit": ""
      },
      {
        "name": "garlic",
        "amount": "3",
        "unit": "cloves"
      },
      ...
    ],
    "instructions": [
      "Boil the pasta...",
      "Melt the butter...",
      ...
    ],
    "prep_time": "10 minutes",
    "cook_time": "15 minutes",
    "servings": 2,
    "difficulty": "Easy",
    "tips": ["Save pasta water..."],
    "source_urls": ["https://example.com/garlic-pasta"],
    "sections": [
      {
        "heading": "Variations",
        "body": "- Add chilli flakes for heat."
      }
    ],
    "raw_text": "Full AI response..."
  }
}
```

**Error Responses:**

- `400` — Missing required field
- `413` — Image too large
- `415` — Unsupported file format
- `500` — Server error (report via Try Again button)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Your Groq AI API key |
| `TAVILY_API_KEY` | Yes | — | Your Tavily Search API key |
| `ALLOWED_ORIGINS` | No | localhost origins | Comma-separated list of allowed CORS origins |
| `MAX_IMAGE_MB` | No | 5 | Maximum image upload size in MB |

## GitHub Pages Deployment

### Frontend Deployment

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy FastEat AI"
   git push
   ```

2. **Enable GitHub Pages:**
   - Go to your repository **Settings** → **Pages**
   - Under **Source**, select **Deploy from a branch**
   - Branch: `main` (or `master`), folder: `/ (root)`
   - Click **Save**

3. **Wait a minute** for the site to be deployed at:
   ```
   https://yourname.github.io/fasteat-ai/
   ```

### Backend Deployment

GitHub Pages cannot run Python/FastAPI, so the backend must be deployed separately.

**Recommended hosting services:**

- **Render.com** — Free tier available for small APIs
- **Railway.app** — Simple, reliable
- **Fly.io** — Fast global edge deployment
- **Heroku** — Classic choice (paid)

**Deployment steps (Render example):**

1. **Create a repository for the backend only:**
   - Remove the `frontend/` directory from your repository.
   - Keep: `main.py`, `agent_core.py`, `photo_decoder.py`, `prompt.py`, `tool.py`, `backend/`, `pyproject.toml`, `requirements.txt`, `.env.example`, `README.md`.

2. **Add a `Procfile`:**
   ```
   web: uvicorn backend.main:app
   ```

3. **Add `runtime.txt` (optional):**
   ```
   python-3.12
   ```

4. **Deploy via Render dashboard** or Git integration.

5. **Update frontend API URL:**
   - In `frontend/app.js`, change:
     ```javascript
     const API_URL = "http://localhost:8000";
     ```
   - To your deployed backend URL:
     ```javascript
     const API_URL = "https://your-backend-url.onrender.com";
     ```

6. **Update CORS in backend:**
   - In your `.env` (on the backend host), set:
     ```
     ALLOWED_ORIGINS="https://yourname.github.io/fasteat-ai"
     ```

## Security Notes

- **Never expose API keys in the frontend.** Keep them in the backend only.
- **CORS is configured explicitly.** Production origins must be set in `ALLOWED_ORIGINS`.
- **Image validation:**
  - Maximum size: 5 MB (configurable)
  - Supported formats: JPG, PNG, WEBP
  - Magic-byte verification prevents file spoofing
  - Temporary files are cleaned up automatically
- **No user authentication required.** The system is designed for public use.

## Troubleshooting

### Backend won't start

**Error: `Missing GROQ_API_KEY` or `Missing TAVILY_API_KEY`**

- Ensure `.env` exists in the repository root
- Check that `.env` is **not** in `.gitignore` (should be gitignored)
- Verify keys are valid and not expired

### CORS errors in browser

**Error: `Access to fetch at ... from origin ... has been blocked by CORS policy`**

- Check that `ALLOWED_ORIGINS` includes your frontend origin
- For local dev, ensure origins include `http://localhost:5500` and `http://127.0.0.1:5500`
- After deploying, set `ALLOWED_ORIGINS` to your GitHub Pages URL

### Agent takes too long

- The AI model + web search can take 10-60 seconds
- Increase timeout if your frontend has no timeout (recommended: 5 minutes)

### Image upload fails

- Ensure the image is JPG, PNG, or WEBP
- Check file size is under `MAX_IMAGE_MB`
- Verify the file is not corrupted

### Frontend doesn't show recipe

- Check browser console for errors
- Ensure FastAPI backend is running
- Verify API_URL in `frontend/app.js` matches your backend URL

## Roadmap

- [ ] Add recipe sharing (social media links)
- [ ] Save favorite recipes locally
- [ ] Support for multiple languages
- [ ] Advanced search and filters
- [ ] Recipe scaling (2x, 3x portions)
- [ ] Integration with meal planning apps

## License

MIT License — feel free to use and modify for your projects.

## Credits

Built with:
- **Groq AI** — Fast, affordable AI model
- **Tavily** — Intelligent web search
- **LangChain** — Agent framework
- **FastAPI** — Modern Python web framework
- **Playwright** — Web browser automation (testing)

---

**Enjoy cooking with FastEat AI! 🍳**
