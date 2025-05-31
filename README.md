# 🧞‍♂️ JobGenie - AI-Powered Job Discovery

JobGenie is an intelligent job search and matching platform that uses AI and NLP to help you find the perfect job opportunities. It combines job scraping from multiple sources with smart resume analysis to provide personalized job recommendations.

## ✨ Features

### 🔍 Smart Job Search
- **Multiple API Sources**: Searches jobs from RapidAPI services (JSearch, LinkedIn, Indeed)
- **Flexible Search**: Keywords, location, and various filters
- **Real-time Results**: Fast and efficient job discovery
- **Fallback Mechanisms**: Automatic switching between API services

### 📄 Resume Intelligence
- **Multi-format Support**: PDF, DOCX, and TXT files
- **AI-Powered Parsing**: Extracts skills, education, and experience
- **Quality Assessment**: Validates and scores resume content
- **Smart Recommendations**: Suggests improvements for better matches

### 🎯 AI Job Matching
- **NLP Analysis**: Uses spaCy for advanced text processing
- **Smart Scoring**: Multi-factor matching algorithm
- **Skill Matching**: Identifies matching and missing skills
- **Experience Analysis**: Matches experience requirements
- **Education Compatibility**: Evaluates education requirements

### 📊 Analytics & Insights
- **Match Explanations**: Detailed breakdown of match scores
- **Job Statistics**: Track applications and success rates
- **Visual Analytics**: Charts and graphs for insights
- **Export Capabilities**: CSV export for all data

### 💾 Data Management
- **PostgreSQL Database**: Robust data persistence
- **Search History**: Track all job searches
- **Application Tracking**: Mark and track job applications
- **Data Export**: Export jobs and analytics to CSV

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+**
2. **PostgreSQL Database** (automatically configured in this environment)
3. **RapidAPI Account** with access to job search APIs (optional for demo)

### Installation

1. **Install Dependencies**
```bash
# Dependencies are already installed via pyproject.toml
# Main packages include: streamlit, pandas, psycopg2-binary, etc.
```

2. **Environment Configuration**
```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your configuration
# DATABASE_URL is already configured in this environment
# Add your RapidAPI key for real job search (optional)
```

3. **Optional: Install spaCy Model** (for enhanced NLP features)
```bash
python -m spacy download en_core_web_sm
```

### Running the Application

```bash
# Start the Streamlit application
streamlit run app.py --server.port 5000
```

The application will be available at `http://localhost:5000`

## 📋 Usage Guide

### 1. Configuration Setup
- Navigate to the "Configuration" page
- Set your default job search preferences
- Configure API settings if you have a RapidAPI key

### 2. Resume Upload
- Go to "Resume Upload" page
- Upload your resume (PDF, DOCX, or TXT)
- Review the AI analysis and recommendations

### 3. Job Search
- Use the "Job Search" page to find opportunities
- Enter keywords and location preferences
- Results are automatically saved to the database

### 4. AI Matching
- Visit "Job Matches" to see personalized recommendations
- View detailed match explanations
- Mark jobs as applied for tracking

### 5. Analytics
- Check the "Analytics" page for insights
- View application statistics and trends
- Export data for external analysis

## 🔧 Configuration

### Environment Variables

The application uses these environment variables:

```bash
# Database (automatically configured)
DATABASE_URL=postgresql://username:password@host:port/database

# API Configuration (optional)
RAPIDAPI_KEY=your_api_key_here

# Application Settings
PORT=5000
DEBUG=false
```

### API Setup (Optional)

For real job data, you can configure RapidAPI access:

1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to job search APIs:
   - [JSearch API](https://rapidapi.com/aspsine/api/jsearch) (Recommended)
   - [LinkedIn Job Search](https://rapidapi.com/rockapis/api/linkedin-job-search)
   - [Indeed Job Search](https://rapidapi.com/aspsine/api/indeed-job-search-api)
3. Add your API key to the environment variables

**Note**: The application works with demo data if no API key is provided.

## 🏗️ Architecture

### Components

- **Frontend**: Streamlit web interface
- **Backend**: Python with PostgreSQL
- **AI Engine**: spaCy NLP + custom matching algorithms
- **Data Sources**: RapidAPI job search services
- **Database**: PostgreSQL for data persistence

### File Structure

```
jobgenie/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration management
├── postgres_database.py   # Database operations
├── flexible_job_scraper.py # Job search API integration
├── resume_parser.py       # Resume parsing and analysis
├── job_matcher.py         # AI matching engine
├── utils.py               # Utility functions
├── pyproject.toml         # Python dependencies
├── requirements.txt       # Pip requirements
├── .streamlit/            # Streamlit configuration
├── .env.example           # Environment template
└── README.md              # This file
```

## 🤖 AI Features

### Resume Analysis
- Skill extraction using pattern matching and NLP
- Education and experience parsing
- Contact information detection
- Content quality assessment

### Job Matching Algorithm
- **Skills Match (40%)**: Technical skill overlap
- **Experience Match (30%)**: Relevant experience keywords
- **Education Match (20%)**: Education requirement compatibility
- **Text Similarity (10%)**: Overall content similarity

### Match Score Calculation
- Scores range from 0-100%
- Weighted algorithm considers multiple factors
- Detailed explanations for each match

## 📊 Data Export

### Supported Formats
- CSV export for all job data
- Applied jobs tracking
- Search history export
- Analytics data export

### Export Options
- All jobs from selected time periods
- Applied jobs only
- Custom filtered results
- Full database export

## 🔒 Privacy & Security

- All data stored locally in PostgreSQL
- No external data sharing
- Resume content processed locally
- API keys stored securely in environment variables

## 🛠️ Troubleshooting

### Common Issues

**Database Connection Issues**
- Ensure PostgreSQL is running
- Check DATABASE_URL configuration
- Verify database permissions

**API Access Issues**
- Verify RapidAPI key is valid
- Check API subscription status
- Test with demo data first

**Resume Parsing Issues**
- Ensure file is not corrupted
- Try different file formats
- Check file size limits

**Performance Issues**
- Limit search results for faster processing
- Clear old data regularly
- Monitor database size

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review the configuration guide
- Open an issue on the project repository
