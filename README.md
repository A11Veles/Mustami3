# Clean Call Center Agent

A streamlined, organized version of the Call Center Agent application with Firebase authentication, AI-powered audio analysis, and a modern web interface.

## 🏗️ Project Structure

```
clean-call-center-agent/
├── config/
│   └── settings.py          # Centralized configuration and constants
├── utils/
│   ├── helpers.py           # Helper functions and utilities
│   └── firebase.py          # Firebase authentication and database handlers
├── agents/
│   ├── transcription.py     # Audio transcription agent
│   ├── summary.py           # Call summarization agent
│   ├── evaluation.py        # Call quality evaluation agent
│   ├── recommendation.py    # Improvement recommendations agent
│   ├── noise_analysis.py    # Audio quality analysis agent
│   └── master.py            # Master orchestrator agent
├── server/
│   └── app.py               # Flask web server with authentication
├── static/
│   └── index.html           # Combined UI with auth and main functionality
├── tests/
│   └── test_suite.py        # Comprehensive test framework
├── outputs/                 # Generated analysis outputs
├── requirements.txt         # Python dependencies
├── .env.template           # Environment variables template
└── README.md               # This file
```

## 🚀 Features

- **🔐 Firebase Authentication**: Complete user registration and login system
- **🤖 AI Analysis Pipeline**: 
  - Audio transcription with speaker identification
  - Call quality evaluation with scoring
  - Professional call summaries
  - Actionable improvement recommendations  
  - Audio quality and noise analysis
- **💻 Modern Web UI**: Combined authentication and analysis interface
- **📊 User Dashboard**: Processing history and analytics
- **🧪 Comprehensive Testing**: Individual test functions for all components
- **📱 Responsive Design**: Works on desktop and mobile devices

## 🛠️ Setup Instructions

### 1. Environment Setup

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Fill in your configuration in `.env`:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FIREBASE_*`: Your Firebase project configuration
   - Other optional settings

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Firebase Setup

1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication with Email/Password
3. Enable Firestore Database
4. Download your service account key and update the path in `.env`

### 4. Run the Application

```bash
cd server
python app.py
```

The application will be available at `http://localhost:5000`

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd tests
python test_suite.py
```

Individual tests can be run by uncommenting specific functions in `test_suite.py`.

### Available Tests

- **Configuration Tests**: Environment variables and settings
- **Helper Function Tests**: URL parsing, file validation, etc.
- **Firebase Connection Tests**: Authentication and database connectivity
- **Agent Tests**: Individual AI agent functionality
- **OpenAI Connection Tests**: API connectivity verification

## 📝 Usage

### Web Interface

1. **Registration/Login**: Create an account or login with existing credentials
2. **Audio Analysis**: Provide a Google Drive link to an audio file
3. **Results**: View comprehensive analysis including:
   - Transcript with speaker identification
   - Call quality scores and evaluation
   - Professional summary
   - Improvement recommendations
   - Audio quality metrics

### API Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/verify` - Verify authentication
- `POST /api/analyze` - Analyze audio file
- `GET /api/user/profile` - Get user profile
- `GET /api/user/history` - Get processing history
- `GET /api/health` - Health check

### Direct Agent Usage

```python
from agents.master import process_single_audio

# Process a single audio file
result = process_single_audio(
    "https://drive.google.com/file/d/YOUR_FILE_ID/view",
    custom_prompt="Focus on customer satisfaction"
)
```

## 🔧 Configuration

All configuration is centralized in `config/settings.py`:

- **AI Models**: OpenAI model selection and parameters
- **File Patterns**: Output file naming conventions
- **System Prompts**: AI agent instructions
- **Rate Limits**: User request limitations
- **Environment Variables**: Centralized env var management

## 📊 Monitoring

- **Health Check**: `GET /api/health` provides system status
- **User Analytics**: Firebase tracks user activity and processing stats
- **Error Handling**: Comprehensive error logging and user feedback

## 🚀 Production Deployment

1. Set environment variables for production
2. Use a production WSGI server like Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 server.app:app
   ```
3. Configure Firebase security rules
4. Set up proper SSL/TLS certificates
5. Configure rate limiting and monitoring

## 🛡️ Security Features

- JWT-based authentication with Firebase
- Request rate limiting per user
- Input validation and sanitization
- Secure environment variable handling
- CORS protection

## 📈 Performance

- **Modular Architecture**: Each agent runs independently
- **Efficient Processing**: Parallel audio analysis pipeline
- **Caching**: Output files cached for quick retrieval
- **Rate Limiting**: Prevents system overload

## 🐛 Troubleshooting

### Common Issues

1. **Firebase Connection Failed**:
   - Check Firebase configuration in `.env`
   - Verify service account key path
   - Ensure Firestore is enabled

2. **OpenAI API Errors**:
   - Verify API key in `.env`
   - Check API quotas and billing
   - Ensure model availability

3. **Audio Download Issues**:
   - Verify Google Drive link is public
   - Check file format compatibility
   - Ensure sufficient disk space

### Debug Mode

Enable debug mode by setting `DEBUG=True` in `.env` for detailed error logging.

## 📚 Development

### Adding New Agents

1. Create new agent file in `agents/` directory
2. Follow the existing pattern with `process_*` function
3. Add agent to master agent pipeline
4. Create corresponding tests

### Extending Configuration

1. Add new settings to `config/settings.py`
2. Update environment template
3. Add validation if needed

## 🤝 Contributing

1. Follow the established code structure
2. Add tests for new functionality
3. Update documentation as needed
4. Use meaningful commit messages

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ for better call center operations**
