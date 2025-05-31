# JobGenie Local Setup Guide for VS Code

## Prerequisites

1. **Python 3.11 or higher**
2. **PostgreSQL database**
3. **VS Code with Python extension**
4. **Git** (optional, for version control)

## Step-by-Step Installation

### 1. Download Project Files

Copy all the project files to your local machine:

```
jobgenie/
├── app.py
├── config.py
├── postgres_database.py
├── flexible_job_scraper.py
├── resume_parser.py
├── job_matcher.py
├── utils.py
├── pyproject.toml
├── .streamlit/config.toml
├── .env.example
├── README.md
└── generated-icon.png
```

### 2. Set Up Python Environment

Open terminal in VS Code and create a virtual environment:

```bash
# Create virtual environment
python -m venv jobgenie_env

# Activate virtual environment
# On Windows:
jobgenie_env\Scripts\activate
# On macOS/Linux:
source jobgenie_env/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install streamlit>=1.45.1
pip install pandas>=2.2.3
pip install psycopg2-binary>=2.9.10
pip install sqlalchemy>=2.0.41
pip install requests>=2.32.3
pip install PyPDF2>=3.0.1
pip install python-docx>=1.1.2
pip install beautifulsoup4>=4.13.4
pip install trafilatura>=2.0.0
pip install spacy>=3.8.7

# Optional: Install spaCy English model for enhanced NLP
python -m spacy download en_core_web_sm
```

# 1. Install PostgreSQL (if not already installed)
sudo apt update
sudo apt install postgresql postgresql-contrib

# 2. Switch to the postgres user
sudo -i -u postgres

# 3. Open the PostgreSQL prompt
psql

# 4. Run the following SQL commands:
CREATE DATABASE jobgenie;
CREATE USER jobgenie_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE jobgenie TO jobgenie_user;

# 5. Exit psql and return to your user
\q
exit

#### Option B: Using Docker (Alternative)

```bash
# Run PostgreSQL in Docker
docker run --name jobgenie-postgres \
  -e POSTGRES_DB=jobgenie \
  -e POSTGRES_USER=jobgenie_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:15
```

### 5. Environment Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file with your settings:**
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://jobgenie_user:your_password@localhost:5432/jobgenie
   
   # Or individual settings:
   PGHOST=localhost
   PGPORT=5432
   PGDATABASE=jobgenie
   PGUSER=jobgenie_user
   PGPASSWORD=your_password
   
   # RapidAPI Key (use the one you provided)
   RAPIDAPI_KEY=f0819b1643msh21c93a48015dbdcp11dc2bjsn9ee848a4a086
   
   # Application Settings
   PORT=5000
   DEBUG=false
   ```

### 6. VS Code Configuration

1. **Select Python Interpreter:**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Python: Select Interpreter"
   - Choose the interpreter from your virtual environment

2. **Create VS Code workspace settings:**
   Create `.vscode/settings.json`:
   ```json
   {
       "python.defaultInterpreter": "./jobgenie_env/bin/python",
       "python.terminal.activateEnvironment": true,
       "files.exclude": {
           "**/__pycache__": true,
           "**/.env": false
       }
   }
   ```

3. **Create launch configuration:**
   Create `.vscode/launch.json`:
   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "JobGenie Streamlit",
               "type": "python",
               "request": "launch",
               "program": "-m",
               "args": [
                   "streamlit",
                   "run",
                   "app.py",
                   "--server.port",
                   "5000"
               ],
               "console": "integratedTerminal",
               "envFile": "${workspaceFolder}/.env"
           }
       ]
   }
   ```

### 7. Run the Application

#### Method 1: VS Code Debugger
- Press `F5` or use the Run menu
- Select "JobGenie Streamlit" configuration

#### Method 2: Terminal
```bash
# Make sure virtual environment is activated
streamlit run app.py --server.port 5000
```

The application will be available at `http://localhost:5000`

### 8. Verify Installation

1. **Check database connection:**
   - Open the application
   - Look for "Database ready" in the sidebar

2. **Test API connection:**
   - Go to Configuration page
   - Click "Test API Connection"
   - Should show "API connection successful"

3. **Test job search:**
   - Navigate to Job Search
   - Enter keywords like "Python Developer"
   - Verify real jobs are returned (not demo data)

## Development Tips

### VS Code Extensions (Recommended)

1. **Python** - Official Python support
2. **Pylance** - Enhanced Python language server
3. **Python Docstring Generator** - Auto-generate docstrings
4. **GitLens** - Enhanced Git capabilities
5. **PostgreSQL** - Database management

### Debugging

1. **Enable debug mode:**
   ```bash
   # In .env file
   DEBUG=true
   ```

2. **View logs:**
   - Check VS Code terminal for application logs
   - Database logs appear in PostgreSQL logs

3. **Common issues:**
   - **Import errors**: Ensure virtual environment is activated
   - **Database errors**: Check PostgreSQL is running and credentials are correct
   - **API errors**: Verify RapidAPI key is valid and has access to job search APIs

### Project Structure for Development

```
jobgenie/
├── .vscode/                # VS Code configuration
│   ├── settings.json
│   └── launch.json
├── .streamlit/             # Streamlit configuration
│   └── config.toml
├── jobgenie_env/           # Virtual environment
├── .env                    # Environment variables (keep private)
├── .gitignore             # Git ignore file
└── [application files]
```

### Recommended .gitignore

```
# Environment
.env
jobgenie_env/
__pycache__/
*.pyc

# Database
*.db
*.sqlite

# Logs
*.log
user_actions.log

# Temp files
temp_resume_*
jobgenie_export_*

# IDE
.vscode/settings.json
.idea/
```

## Next Steps

1. **Customize configuration** in the Configuration page
2. **Upload your resume** to test AI parsing
3. **Search for jobs** relevant to your field
4. **Explore analytics** and export features
5. **Set up regular backups** of your PostgreSQL database

## Support

If you encounter issues:
1. Check the terminal output for error messages
2. Verify all dependencies are installed correctly
3. Ensure PostgreSQL is running and accessible
4. Test API connectivity with your RapidAPI key
5. Review the troubleshooting section in README.md