Create a complete `GUIDE.md` for the Nutri Delight project.

The project has two GitHub repositories:

Frontend:
https://github.com/vineel-kolli/nutridelightproject

Backend:
https://github.com/vineel-kolli/nutridelight-backend

Write the guide for a new developer who has never worked on this project before and has just cloned both repositories.

The guide must be practical, accurate, and based on the current project structure. Do not invent commands, files, environment variables, API routes, or architecture that do not exist in the repositories. If something cannot be verified from the repositories, clearly mark it as something the developer must obtain from the project owner.

Include these sections:

1. Project Overview
- Explain what Nutri Delight is.
- Explain the frontend/backend architecture.
- Explain the responsibility of each repository.

2. Repository Setup
- Clone both repositories.
- Show a recommended local directory structure.

3. Prerequisites
- Required Node.js/npm
- Required Python version
- Git
- PostgreSQL/Supabase
- VS Code or equivalent
- Any other dependency that is actually required by the repositories.

4. Backend Setup
- Navigate to the backend repository.
- Create and activate the Python virtual environment.
- Install requirements.
- Explain the backend `.env` file.
- Show a safe `.env` template with placeholders only.
- NEVER include real passwords, API keys, database credentials, or session secrets.

5. Database Setup
- Explain that PostgreSQL is used.
- Explain Supabase if it is part of the current configuration.
- Explain `DATABASE_URL`.
- Explain how Alembic is used.
- Give the exact migration commands supported by the repository.
- Explain how to check the current migration.
- Warn developers not to manually modify the database schema when an Alembic migration should be used.

6. Admin Account Setup
- Explain how the existing admin creation CLI works.
- Give the exact command from the repository.
- Explain the password requirements.
- Explain that passwords are hashed and must never be stored in plaintext.

7. Running the Backend
- Give the exact Uvicorn command.
- Give the local backend URL.
- Give the health endpoint.
- Give the Swagger/OpenAPI URL if available.

8. Frontend Setup
- Navigate to the frontend repository.
- Install dependencies.
- Explain the frontend environment variables.
- Give the exact local `VITE_API_BASE_URL` format.
- Explicitly explain that the API base URL must NOT have a trailing slash.

9. Running the Frontend
- Give the exact npm command.
- Give the expected local URL.
- Explain the admin URL if it exists.

10. Admin Authentication
Explain the current authentication architecture accurately:
- Admin username/password authentication
- Argon2 password hashing
- Server-side sessions
- Random session token
- Hashed session token stored in the database
- HttpOnly cookie
- Credentialed frontend requests
- CORS restrictions
Do not suggest replacing this architecture with JWT unless the existing project actually uses JWT.

11. Game Configuration
Explain:
- `total_games`
- Odd-number validation
- Minimum/maximum values
- Initial configuration behavior
- How the admin configures games per match
- How the frontend and backend interact.

12. Game Rules
Explain the current match behavior:
- Exactly `total_games` counted games
- Draws do not count
- A draw is retried
- Non-draw results advance the match
- Odd total games prevent an overall tie.

13. Prize Rules
Explain:
- `required_wins`
- `prize_name`
- `prize_image_url`
- `is_active`
- Relationship with `game_configs`
- Validation that required wins cannot exceed total games.
- How admins create/update/delete prize rules.

14. Prize Image Uploads
Explain the currently implemented upload behavior:
- Supported formats
- File size limit
- Backend validation
- Upload endpoint if present
- Important production considerations if applicable.
Do not invent storage behavior.

15. Local Development Workflow
Give exact commands for:
- Backend terminal
- Frontend terminal
- Running both simultaneously.

16. Testing
- Give the exact backend test command.
- Give the frontend build/type-check commands only if they actually exist in package.json.
- Explain what should be checked before committing.

17. Git Workflow
Provide a simple workflow:
- git pull --rebase
- feature branch
- git status
- git diff
- git add
- git commit
- git push
Use sensible conventional commit examples such as:
`feat: ...`
`fix: ...`
`refactor: ...`

18. Environment Variables and Secrets
Clearly explain:
- Never commit `.env`
- Never commit passwords
- Never commit API keys
- Never commit database URLs containing credentials
- Never expose session tokens.
Show only placeholder values.

19. Production Deployment
Explain the current deployment architecture only if it can be verified:
- Vercel frontend
- Render backend
- Supabase PostgreSQL
- Production environment variables
- Vite environment variables
- Need to redeploy Vercel after changing VITE_* variables
- Need to restart/redeploy backend after changing backend environment variables.
Do not expose real production secrets.

20. Production Authentication
If the current production architecture is Vercel frontend + Render backend, accurately explain the cross-origin/cross-site authentication requirements:
- `credentials: include`
- explicit CORS origin
- credentials allowed
- secure HttpOnly session cookie
- production SameSite behavior as actually implemented.
Do not weaken CORS or authentication just to make login work.

21. Troubleshooting
Include practical troubleshooting for:
- Backend won't start
- Database connection failure
- Alembic migration problems
- Frontend cannot reach backend
- CORS errors
- Admin login 401
- Session cookie problems
- Game configuration 404
- API URL with double slash
- Vercel/Render environment variable problems.

22. Developer Rules
Include clear rules:
- Do not commit secrets.
- Do not manually edit production database schema.
- Do not delete migrations to solve migration errors.
- Do not weaken authentication.
- Do not use wildcard CORS with credentialed authentication.
- Keep frontend and backend responsibilities separated.
- Backend remains authoritative for security-sensitive validation/business logic.
- Run tests/build checks before pushing.

23. First-Time Setup Checklist
End with a concise checklist that a new developer can follow from zero to running the application:

[ ] Clone frontend
[ ] Clone backend
[ ] Install prerequisites
[ ] Create backend virtual environment
[ ] Install backend dependencies
[ ] Configure backend `.env`
[ ] Configure database
[ ] Run Alembic migrations
[ ] Create admin
[ ] Start backend
[ ] Configure frontend `.env`
[ ] Install frontend dependencies
[ ] Start frontend
[ ] Open application
[ ] Open admin dashboard
[ ] Log in
[ ] Configure game settings
[ ] Configure prize rules
[ ] Run tests
[ ] Run frontend build/check
[ ] Review git diff
[ ] Commit and push

IMPORTANT:
- Make the document professional and suitable for onboarding developers.
- Use Markdown.
- Use code blocks for commands and environment-variable examples.
- Keep explanations clear and direct.
- Do not include emojis.
- Do not include actual secrets.
- Do not invent project behavior.
- Before writing the final GUIDE.md, inspect the current repositories/files so commands, paths, scripts, environment variables, API endpoints, migrations, and authentication behavior match the actual code.
- The developer using this guide should be able to follow it without needing to guess what command to run next.