import asyncio
import time
import re
import pickle
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from ..config.settings import settings
from ..utils.logging import get_logger
from ..utils.exceptions import MLServiceException
from ..models.ticket import TicketCategory

logger = get_logger(__name__)


class MLService:
    """
    Machine Learning service for ticket classification.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.models = {}
        self.vectorizers = {}
        self.label_encoders = {}
        self.nlp = None
        self.huggingface_pipeline = None
        self.model_performance = {}
        
        # Download required NLTK data
        self._download_nltk_data()
    
    def _download_nltk_data(self):
        """Download required NLTK data."""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('tokenizers/punkt_tab')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)
    
    async def initialize(self):
        """Initialize the ML service."""
        logger.info("Initializing ML service...")
        
        try:
            # Load spaCy model
            await self._load_spacy_model()
            
            # Initialize traditional ML models
            await self._initialize_traditional_models()
            
            # Initialize Hugging Face model
            await self._initialize_huggingface_model()
            
            # Load pre-trained models if available
            await self._load_pretrained_models()
            
            self.is_initialized = True
            logger.info("ML service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML service: {e}")
            raise MLServiceException(f"ML service initialization failed: {str(e)}")
    
    async def _load_spacy_model(self):
        """Load spaCy model."""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available. Using basic preprocessing.")
            self.nlp = None
            return
            
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Using basic preprocessing.")
            self.nlp = None
    
    async def _initialize_traditional_models(self):
        """Initialize traditional ML models."""
        # Text vectorizer
        self.vectorizers['tfidf'] = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        
        # Classification models
        self.models['naive_bayes'] = MultinomialNB(alpha=1.0)
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        self.models['svm'] = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            probability=True,
            random_state=42
        )
        
        # Label encoder
        self.label_encoders['category'] = LabelEncoder()
        
        # Train with sample data to fit the vectorizer and models
        await self._train_with_sample_data()
        
        logger.info("Traditional ML models initialized")
    
    async def _train_with_sample_data(self):
        """Train models with sample data to ensure they're fitted."""
        # Sample training data for demonstration
        sample_data = [
            {"title": "Laptop screen black", "description": "My laptop screen is not working", "category": "Hardware"},
            {"title": "Cannot connect WiFi", "description": "Unable to connect to wireless network", "category": "Network"},
            {"title": "Software installation error", "description": "Getting error when installing application", "category": "Software"},
            {"title": "Password reset", "description": "Need to reset my login password", "category": "Security"},
            {"title": "Email not working", "description": "Cannot send or receive emails", "category": "Email"},
            {"title": "Access denied", "description": "Cannot access shared folder", "category": "Access"},
            {"title": "Computer slow", "description": "My computer is running very slowly", "category": "Hardware"},
            {"title": "Internet connection", "description": "Internet is not working properly", "category": "Network"},
            {"title": "Application crash", "description": "The software keeps crashing", "category": "Software"},
            {"title": "Login issues", "description": "Cannot login to system", "category": "Security"},
            {"title": "Outlook problems", "description": "Outlook is not syncing emails", "category": "Email"},
            {"title": "File permissions", "description": "Cannot open files due to permissions", "category": "Access"},
            {"title": "Printer not working", "description": "Printer is not responding", "category": "Hardware"},
            {"title": "VPN connection", "description": "Cannot connect to VPN", "category": "Network"},
            {"title": "Software update", "description": "Software update failed", "category": "Software"},
            {"title": "Account locked", "description": "My account has been locked", "category": "Security"},
            {"title": "Email server", "description": "Email server connection error", "category": "Email"},
            {"title": "Folder access", "description": "Cannot access network folder", "category": "Access"},
            {"title": "Monitor display", "description": "Monitor display issues", "category": "Hardware"},
            {"title": "Network speed", "description": "Network is very slow", "category": "Network"}
        ]
        
        try:
            # Prepare training data
            texts = []
            labels = []
            
            for item in sample_data:
                combined_text = f"{item['title']} {item['description']}"
                processed_text = self.preprocess_text(combined_text)
                texts.append(processed_text)
                labels.append(item['category'])
            
            # Fit label encoder
            self.label_encoders['category'].fit(labels)
            
            # Fit vectorizer
            X_vectorized = self.vectorizers['tfidf'].fit_transform(texts)
            
            # Encode labels
            y_encoded = self.label_encoders['category'].transform(labels)
            
            # Train each model
            for model_name, model in self.models.items():
                model.fit(X_vectorized, y_encoded)
            
            logger.info("Traditional ML models trained with sample data")
            
        except Exception as e:
            logger.warning(f"Failed to train with sample data: {e}")
    
    async def _initialize_huggingface_model(self):
        """Initialize Hugging Face model."""
        try:
            model_name = settings.huggingface_model_name
            
            # Check if GPU is available and enabled
            device = 0 if torch.cuda.is_available() and settings.use_gpu else -1
            
            # Initialize the pipeline
            self.huggingface_pipeline = pipeline(
                "text-classification",
                model=model_name,
                tokenizer=model_name,
                device=device,
                max_length=settings.max_sequence_length,
                truncation=True
            )
            
            logger.info(f"Hugging Face model '{model_name}' initialized on device: {device}")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Hugging Face model: {e}")
            self.huggingface_pipeline = None
    
    async def _load_pretrained_models(self):
        """Load pre-trained models if available."""
        model_path = Path(settings.ml_model_path)
        
        if model_path.exists():
            try:
                # Load vectorizer
                vectorizer_path = model_path / "tfidf_vectorizer.pkl"
                if vectorizer_path.exists():
                    self.vectorizers['tfidf'] = joblib.load(vectorizer_path)
                
                # Load models
                for model_name in ['naive_bayes', 'random_forest', 'svm']:
                    model_file = model_path / f"{model_name}.pkl"
                    if model_file.exists():
                        self.models[model_name] = joblib.load(model_file)
                
                # Load label encoder
                encoder_path = model_path / "label_encoder.pkl"
                if encoder_path.exists():
                    self.label_encoders['category'] = joblib.load(encoder_path)
                
                logger.info("Pre-trained models loaded successfully")
                
            except Exception as e:
                logger.warning(f"Failed to load pre-trained models: {e}")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for classification.
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if self.nlp:
            # Use spaCy for advanced preprocessing
            doc = self.nlp(text)
            tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
            return ' '.join(tokens)
        else:
            # Use NLTK for basic preprocessing
            try:
                tokens = word_tokenize(text)
                stop_words = set(stopwords.words('english'))
                lemmatizer = WordNetLemmatizer()
                
                tokens = [lemmatizer.lemmatize(token) for token in tokens 
                         if token not in stop_words and len(token) > 2]
                
                return ' '.join(tokens)
            except Exception as e:
                logger.warning(f"Text preprocessing failed: {e}")
                # Fallback to basic string processing
                words = text.split()
                # Basic stopword removal
                basic_stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
                filtered_words = [word for word in words if word.lower() not in basic_stopwords and len(word) > 2]
                return ' '.join(filtered_words) if filtered_words else text
    
    def extract_features(self, text: str) -> Dict[str, float]:
        """
        Extract additional features from text.
        """
        features = {}
        
        # Text length features
        features['text_length'] = len(text)
        features['word_count'] = len(text.split())
        features['sentence_count'] = len(text.split('.'))
        
        # Urgency indicators
        urgent_words = ['urgent', 'emergency', 'critical', 'asap', 'immediately', 'help', 'broken', 'down']
        features['urgency_score'] = sum(1 for word in urgent_words if word in text.lower())
        
        # Technical terms
        tech_terms = ['error', 'bug', 'crash', 'freeze', 'slow', 'virus', 'malware', 'update', 'install']
        features['technical_score'] = sum(1 for term in tech_terms if term in text.lower())
        
        # Sentiment analysis using basic keywords
        positive_words = ['thank', 'please', 'appreciate', 'good', 'working']
        negative_words = ['angry', 'frustrated', 'terrible', 'awful', 'hate']
        
        features['positive_sentiment'] = sum(1 for word in positive_words if word in text.lower())
        features['negative_sentiment'] = sum(1 for word in negative_words if word in text.lower())
        
        return features
    
    async def classify_ticket(self, title: str, description: str) -> Dict[str, any]:
        """
        Classify a ticket using multiple models.
        """
        if not self.is_initialized:
            raise MLServiceException("ML service not initialized")
        
        start_time = time.time()
        
        # Combine title and description
        text = f"{title} {description}"
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        # Extract features
        features = self.extract_features(text)
        
        results = {}
        
        # Keyword-based classification (most reliable for IT support)
        keyword_category, keyword_confidence = self._classify_by_keywords(text)
        results['keyword_prediction'] = {
            'category': keyword_category,
            'confidence': keyword_confidence,
            'method': 'keyword_based'
        }
        
        # Traditional ML classification
        traditional_result = await self._classify_traditional(processed_text)
        results.update(traditional_result)
        
        # Hugging Face classification
        if self.huggingface_pipeline:
            hf_result = await self._classify_huggingface(processed_text)
            results.update(hf_result)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Determine final prediction
        final_prediction = self._ensemble_prediction(results)
        
        return {
            'predicted_category': final_prediction['category'],
            'confidence_score': final_prediction['confidence'],
            'model_name': final_prediction['model'],
            'model_version': '1.0.0',
            'suggested_actions': self._get_suggested_actions(final_prediction['category']),
            'keywords_identified': self._extract_keywords(processed_text),
            'sentiment_score': self._calculate_sentiment_score(features),
            'urgency_score': features['urgency_score'],
            'estimated_resolution_time': self._estimate_resolution_time(final_prediction['category'], features),
            'processing_time_ms': processing_time,
            'preprocessing_applied': ['lowercase', 'tokenization', 'lemmatization', 'stopword_removal'],
            'features': features,
            'all_predictions': results
        }
    
    async def _classify_traditional(self, text: str) -> Dict[str, any]:
        """
        Classify using traditional ML models.
        """
        results = {}
        
        try:
            # Vectorize text
            if hasattr(self.vectorizers['tfidf'], 'transform'):
                text_vector = self.vectorizers['tfidf'].transform([text])
            else:
                # If vectorizer is not fitted, return empty results
                return {}
            
            # Predict with each model
            for model_name, model in self.models.items():
                if hasattr(model, 'predict_proba'):
                    probabilities = model.predict_proba(text_vector)[0]
                    prediction = model.predict(text_vector)[0]
                    
                    # Get class names
                    if hasattr(self.label_encoders['category'], 'classes_'):
                        classes = self.label_encoders['category'].classes_
                        category = classes[prediction]
                        confidence = max(probabilities)
                    else:
                        # Default categories if encoder is not fitted
                        categories = [cat.value for cat in TicketCategory]
                        category = categories[prediction % len(categories)]
                        confidence = max(probabilities)
                    
                    results[f'{model_name}_prediction'] = {
                        'category': category,
                        'confidence': float(confidence),
                        'probabilities': {cls: float(prob) for cls, prob in zip(categories, probabilities) if len(categories) == len(probabilities)}
                    }
                    
        except Exception as e:
            logger.warning(f"Traditional ML classification failed: {e}")
        
        return results
    
    async def _classify_huggingface(self, text: str) -> Dict[str, any]:
        """
        Classify using Hugging Face model.
        """
        try:
            # Run classification
            result = self.huggingface_pipeline(text)
            
            # Map result to our categories
            mapped_category = self._map_to_ticket_category(result[0]['label'])
            
            return {
                'huggingface_prediction': {
                    'category': mapped_category,
                    'confidence': float(result[0]['score']),
                    'original_label': result[0]['label']
                }
            }
            
        except Exception as e:
            logger.warning(f"Hugging Face classification failed: {e}")
            return {}
    
    def _classify_by_keywords(self, text: str) -> Tuple[str, float]:
        """
        Classify text using keyword-based approach with confidence scoring.
        """
        text_lower = text.lower()
        
        # Define keyword patterns for each category with weights
        category_patterns = {
            TicketCategory.HARDWARE.value: {
                'keywords': ['laptop', 'computer', 'screen', 'monitor', 'keyboard', 'mouse', 'printer', 
                            'device', 'hardware', 'black screen', 'not turning on', 'fan', 'power button',
                            'display', 'broken', 'damaged', 'physical', 'cable', 'port', 'usb'],
                'phrases': ['screen is black', 'won\'t turn on', 'not working', 'hardware issue', 
                           'device not recognized', 'physical damage']
            },
            TicketCategory.SOFTWARE.value: {
                'keywords': ['software', 'application', 'program', 'install', 'installation', 'update',
                            'app', 'error', 'crash', 'freeze', 'bug', 'version', 'compatibility',
                            'license', 'download', 'upgrade'],
                'phrases': ['software installation', 'application error', 'program crash', 
                           'software update', 'installation failed', 'error code']
            },
            TicketCategory.NETWORK.value: {
                'keywords': ['wifi', 'network', 'internet', 'connection', 'connect', 'disconnect',
                            'router', 'ethernet', 'lan', 'wireless', 'bandwidth', 'slow internet',
                            'vpn', 'firewall', 'dns', 'ip address'],
                'phrases': ['cannot connect', 'wifi not working', 'network issue', 'internet down',
                           'connection problem', 'authentication failed']
            },
            TicketCategory.SECURITY.value: {
                'keywords': ['password', 'security', 'login', 'authentication', 'antivirus', 'virus',
                            'malware', 'phishing', 'spam', 'unauthorized', 'breach', 'hack',
                            'encryption', 'certificate', 'two factor'],
                'phrases': ['password reset', 'forgot password', 'cannot login', 'security breach',
                           'suspicious activity', 'virus detected']
            },
            TicketCategory.ACCESS.value: {
                'keywords': ['access', 'permission', 'denied', 'folder', 'file', 'share', 'drive',
                            'directory', 'unauthorized', 'privilege', 'rights', 'group',
                            'user account', 'admin'],
                'phrases': ['access denied', 'permission denied', 'cannot access', 'no permission',
                           'shared folder', 'file permission']
            },
            TicketCategory.EMAIL.value: {
                'keywords': ['email', 'mail', 'outlook', 'exchange', 'smtp', 'imap', 'pop',
                            'inbox', 'send', 'receive', 'attachment', 'sync', 'calendar'],
                'phrases': ['email not working', 'cannot send email', 'email sync', 'outlook error',
                           'mail server', 'email delivery']
            }
        }
        
        category_scores = {}
        
        for category, patterns in category_patterns.items():
            score = 0
            
            # Check keywords (weight: 1)
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    score += 1
            
            # Check phrases (weight: 2)
            for phrase in patterns['phrases']:
                if phrase in text_lower:
                    score += 2
            
            # Normalize score
            total_patterns = len(patterns['keywords']) + len(patterns['phrases']) * 2
            category_scores[category] = score / total_patterns if total_patterns > 0 else 0
        
        # Get best category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = category_scores[best_category]
            
            # If confidence is too low, classify as OTHER
            if confidence < 0.1:
                return TicketCategory.OTHER.value, 0.5
            
            # Scale confidence to be more realistic (between 0.6 and 0.95)
            scaled_confidence = 0.6 + (confidence * 0.35)
            return best_category, min(scaled_confidence, 0.95)
        
        return TicketCategory.OTHER.value, 0.5
    
    def _map_to_ticket_category(self, label: str) -> str:
        """
        Map Hugging Face model output to ticket categories.
        """
        # Since the general model doesn't know about IT categories,
        # we'll use our keyword-based approach instead
        return TicketCategory.OTHER.value
    
    def _ensemble_prediction(self, results: Dict[str, any]) -> Dict[str, any]:
        """
        Combine predictions from multiple models with keyword-based priority.
        """
        predictions = []
        
        # Collect all predictions
        for key, value in results.items():
            if key.endswith('_prediction'):
                model_name = key.replace('_prediction', '')
                predictions.append({
                    'category': value['category'],
                    'confidence': value['confidence'],
                    'model': model_name
                })
        
        if not predictions:
            # Default prediction if no models worked
            return {
                'category': TicketCategory.OTHER.value,
                'confidence': 0.5,
                'model': 'default'
            }
        
        # Priority-based ensemble:
        # 1. If keyword prediction has good confidence (>0.7), use it
        # 2. Otherwise, use highest confidence prediction
        
        keyword_pred = next((p for p in predictions if p['model'] == 'keyword'), None)
        
        if keyword_pred and keyword_pred['confidence'] > 0.7:
            return keyword_pred
        
        # If keyword prediction exists but confidence is moderate, boost it slightly
        if keyword_pred and keyword_pred['confidence'] > 0.5:
            keyword_pred['confidence'] = min(keyword_pred['confidence'] + 0.1, 0.95)
            return keyword_pred
        
        # Otherwise, use highest confidence
        best_prediction = max(predictions, key=lambda x: x['confidence'])
        
        # If best prediction is OTHER and we have a keyword prediction, prefer keyword
        if best_prediction['category'] == TicketCategory.OTHER.value and keyword_pred:
            return keyword_pred
        
        return best_prediction
    
    def _get_suggested_actions(self, category: str) -> List[str]:
        """
        Get suggested actions based on category.
        """
        actions_map = {
            TicketCategory.HARDWARE.value: [
                "Check physical connections",
                "Verify hardware diagnostics",
                "Schedule on-site visit if needed",
                "Check warranty status"
            ],
            TicketCategory.SOFTWARE.value: [
                "Check for software updates",
                "Verify application configuration",
                "Review system requirements",
                "Check for conflicting software"
            ],
            TicketCategory.NETWORK.value: [
                "Test network connectivity",
                "Check network configuration",
                "Verify firewall settings",
                "Test with different network"
            ],
            TicketCategory.SECURITY.value: [
                "Review security policies",
                "Check for malware",
                "Verify user permissions",
                "Update security software"
            ],
            TicketCategory.ACCESS.value: [
                "Verify user credentials",
                "Check access permissions",
                "Review group memberships",
                "Reset passwords if needed"
            ],
            TicketCategory.EMAIL.value: [
                "Check email configuration",
                "Verify SMTP/IMAP settings",
                "Test email connectivity",
                "Check spam filters"
            ],
            TicketCategory.OTHER.value: [
                "Gather more information",
                "Review ticket details",
                "Contact user for clarification",
                "Escalate if necessary"
            ]
        }
        
        return actions_map.get(category, actions_map[TicketCategory.OTHER.value])
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from text.
        """
        if not text:
            return []
        
        # Simple keyword extraction
        words = text.split()
        
        # Filter out common words and short words
        keywords = [word for word in words if len(word) > 3]
        
        # Return top 10 most frequent keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def _calculate_sentiment_score(self, features: Dict[str, float]) -> float:
        """
        Calculate sentiment score from features.
        """
        positive = features.get('positive_sentiment', 0)
        negative = features.get('negative_sentiment', 0)
        
        if positive + negative == 0:
            return 0.0
        
        return (positive - negative) / (positive + negative)
    
    def _estimate_resolution_time(self, category: str, features: Dict[str, float]) -> float:
        """
        Estimate resolution time in minutes.
        """
        # Base times by category (in minutes)
        base_times = {
            TicketCategory.HARDWARE.value: 240,  # 4 hours
            TicketCategory.SOFTWARE.value: 120,  # 2 hours
            TicketCategory.NETWORK.value: 180,   # 3 hours
            TicketCategory.SECURITY.value: 360,  # 6 hours
            TicketCategory.ACCESS.value: 60,     # 1 hour
            TicketCategory.EMAIL.value: 90,      # 1.5 hours
            TicketCategory.OTHER.value: 180,     # 3 hours
        }
        
        base_time = base_times.get(category, 180)
        
        # Adjust based on urgency
        urgency_multiplier = 1.0 + (features.get('urgency_score', 0) * 0.2)
        
        return base_time * urgency_multiplier
    
    async def train_models(self, training_data: List[Dict[str, str]]):
        """
        Train ML models with new data.
        """
        if not training_data:
            raise MLServiceException("No training data provided")
        
        logger.info(f"Training models with {len(training_data)} samples")
        
        # Prepare data
        texts = []
        labels = []
        
        for item in training_data:
            text = f"{item['title']} {item['description']}"
            texts.append(self.preprocess_text(text))
            labels.append(item['category'])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Fit vectorizer
        X_train_vec = self.vectorizers['tfidf'].fit_transform(X_train)
        X_test_vec = self.vectorizers['tfidf'].transform(X_test)
        
        # Fit label encoder
        self.label_encoders['category'].fit(labels)
        y_train_encoded = self.label_encoders['category'].transform(y_train)
        y_test_encoded = self.label_encoders['category'].transform(y_test)
        
        # Train models
        for model_name, model in self.models.items():
            logger.info(f"Training {model_name}...")
            
            model.fit(X_train_vec, y_train_encoded)
            
            # Evaluate
            y_pred = model.predict(X_test_vec)
            accuracy = accuracy_score(y_test_encoded, y_pred)
            
            self.model_performance[model_name] = {
                'accuracy': accuracy,
                'classification_report': classification_report(
                    y_test_encoded, y_pred, 
                    target_names=self.label_encoders['category'].classes_,
                    output_dict=True
                )
            }
            
            logger.info(f"{model_name} accuracy: {accuracy:.3f}")
        
        # Save models
        await self._save_models()
        
        logger.info("Model training completed")
    
    async def _save_models(self):
        """
        Save trained models to disk.
        """
        model_path = Path(settings.ml_model_path)
        model_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save vectorizer
            joblib.dump(self.vectorizers['tfidf'], model_path / "tfidf_vectorizer.pkl")
            
            # Save models
            for model_name, model in self.models.items():
                joblib.dump(model, model_path / f"{model_name}.pkl")
            
            # Save label encoder
            joblib.dump(self.label_encoders['category'], model_path / "label_encoder.pkl")
            
            # Save performance metrics
            with open(model_path / "performance.json", 'w') as f:
                import json
                json.dump(self.model_performance, f, indent=2)
            
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
            raise MLServiceException(f"Failed to save models: {str(e)}")
    
    def is_ready(self) -> bool:
        """
        Check if ML service is ready.
        """
        return self.is_initialized
    
    def get_model_info(self) -> Dict[str, any]:
        """
        Get information about loaded models.
        """
        return {
            'initialized': self.is_initialized,
            'models': list(self.models.keys()),
            'vectorizers': list(self.vectorizers.keys()),
            'huggingface_model': settings.huggingface_model_name if self.huggingface_pipeline else None,
            'spacy_model': "en_core_web_sm" if self.nlp else None,
            'performance': self.model_performance
        }
    
    async def cleanup(self):
        """
        Cleanup resources.
        """
        logger.info("Cleaning up ML service...")
        
        # Clear models
        self.models.clear()
        self.vectorizers.clear()
        self.label_encoders.clear()
        
        # Clear other resources
        self.nlp = None
        self.huggingface_pipeline = None
        
        self.is_initialized = False
        logger.info("ML service cleanup completed")