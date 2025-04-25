import os
import datetime
import json
import time
import logging
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

# Global engine variable
engine = None

def get_db_engine():
    """
    Create or get the database engine with robust connection handling
    
    Returns:
        SQLAlchemy engine with connection pooling
    """
    global engine
    if engine is None:
        # Create engine with improved connection settings
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,  # Automatically detect and handle disconnects
            pool_recycle=1800,   # Recycle connections after 30 minutes
            connect_args={
                'connect_timeout': 10,  # Connection timeout in seconds
                'keepalives': 1,        # Enable keepalive
                'keepalives_idle': 30,  # Send keepalive every 30 seconds
                'keepalives_interval': 10,
                'keepalives_count': 5,
                'sslmode': 'require'    # Require SSL for security
            }
        )
    return engine

# Create base class for models
Base = declarative_base()

# Define analysis result model
class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Input parameters
    website_url = Column(String(255))
    budget = Column(Float)
    business_type = Column(String(50))
    
    # Advanced parameters
    avg_cpc = Column(Float)
    ctr = Column(Float)
    conversion_rate = Column(Float)
    avg_order_value = Column(Float)
    
    # Base case metrics
    clicks = Column(Float)
    impressions = Column(Float)
    conversions = Column(Float)
    cost_per_conversion = Column(Float)
    revenue = Column(Float)
    roi = Column(Float)
    roas = Column(Float)
    
    # Scenario analysis (stored as JSON in text field)
    pessimistic_scenario = Column(Text)
    optimistic_scenario = Column(Text)
    
    # User notes (optional)
    notes = Column(Text, nullable=True)
    
    # Flag for saved analysis (favorites)
    is_saved = Column(Boolean, default=False)

# Initialize the database
def init_db():
    """Initialize the database and create tables"""
    try:
        engine = get_db_engine()
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

# Create session factory
Session = None

def get_session_factory():
    """Get or create the session factory"""
    global Session
    if Session is None:
        engine = get_db_engine()
        Session = sessionmaker(bind=engine)
    return Session

@contextmanager
def get_db_session():
    """
    Context manager for database sessions with automatic cleanup and error handling
    
    Yields:
        SQLAlchemy session
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Initialize database
init_db()

def save_analysis(analysis_data):
    """
    Save analysis results to database
    
    Args:
        analysis_data (dict): Dictionary containing analysis data
        
    Returns:
        int: ID of the saved record
    """
    # Ensure Session is initialized
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        # Create new analysis result
        analysis = AnalysisResult(
            website_url=analysis_data.get('website_url'),
            budget=analysis_data.get('budget'),
            business_type=analysis_data.get('business_type'),
            
            # Advanced parameters
            avg_cpc=analysis_data.get('advanced_params', {}).get('avg_cpc'),
            ctr=analysis_data.get('advanced_params', {}).get('ctr'),
            conversion_rate=analysis_data.get('advanced_params', {}).get('conversion_rate'),
            avg_order_value=analysis_data.get('advanced_params', {}).get('avg_order_value'),
            
            # Base case metrics
            clicks=analysis_data.get('base_case', {}).get('clicks'),
            impressions=analysis_data.get('base_case', {}).get('impressions'),
            conversions=analysis_data.get('base_case', {}).get('conversions'),
            cost_per_conversion=analysis_data.get('base_case', {}).get('cost_per_conversion'),
            revenue=analysis_data.get('base_case', {}).get('revenue'),
            roi=analysis_data.get('base_case', {}).get('roi'),
            roas=analysis_data.get('base_case', {}).get('roas'),
            
            # Scenarios (stored as JSON strings)
            pessimistic_scenario=json.dumps(analysis_data.get('pessimistic_case', {})),
            optimistic_scenario=json.dumps(analysis_data.get('optimistic_case', {})),
            
            # Optional fields
            notes=analysis_data.get('notes'),
            is_saved=analysis_data.get('is_saved', False)
        )
        
        # Add to session
        session.add(analysis)
        session.commit()
        
        # Get the ID
        analysis_id = analysis.id
        logger.info(f"Successfully saved analysis with ID: {analysis_id}")
        return analysis_id
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving analysis: {str(e)}")
        raise e
    finally:
        session.close()

def get_all_analyses(limit=10):
    """
    Get all analysis results
    
    Args:
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of analysis results
    """
    max_retries = 3
    retry_count = 0
    backoff_time = 1  # Start with 1 second delay
    
    while retry_count < max_retries:
        # Get a new session for each attempt
        session_factory = get_session_factory()
        session = session_factory()
        
        try:
            analyses = session.query(AnalysisResult).order_by(
                AnalysisResult.created_at.desc()
            ).limit(limit).all()
            
            # Convert to list to detach from session
            result = list(analyses)
            logger.info(f"Successfully retrieved {len(result)} analyses")
            return result
        
        except Exception as e:
            session.rollback()
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Database connection error, retrying ({retry_count}/{max_retries}): {str(e)}")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to get analyses after {max_retries} attempts: {str(e)}")
                raise e
        finally:
            session.close()

def get_analysis_by_id(analysis_id):
    """
    Get analysis by ID
    
    Args:
        analysis_id (int): ID of the analysis
        
    Returns:
        AnalysisResult: Analysis result object
    """
    # Get a session
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        analysis = session.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id
        ).first()
        
        if analysis:
            logger.info(f"Retrieved analysis with ID: {analysis_id}")
        else:
            logger.warning(f"No analysis found with ID: {analysis_id}")
            
        return analysis
    
    except Exception as e:
        logger.error(f"Error retrieving analysis with ID {analysis_id}: {str(e)}")
        raise e
    finally:
        session.close()

def delete_analysis(analysis_id):
    """
    Delete analysis by ID
    
    Args:
        analysis_id (int): ID of the analysis
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get a session
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        analysis = session.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id
        ).first()
        
        if analysis:
            session.delete(analysis)
            session.commit()
            logger.info(f"Successfully deleted analysis with ID: {analysis_id}")
            return True
        
        logger.warning(f"No analysis found to delete with ID: {analysis_id}")
        return False
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting analysis with ID {analysis_id}: {str(e)}")
        raise e
    finally:
        session.close()

def update_analysis_notes(analysis_id, notes, is_saved=None):
    """
    Update analysis notes
    
    Args:
        analysis_id (int): ID of the analysis
        notes (str): New notes
        is_saved (bool): Whether the analysis is saved (favorited)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Get a session
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        analysis = session.query(AnalysisResult).filter(
            AnalysisResult.id == analysis_id
        ).first()
        
        if analysis:
            analysis.notes = notes
            
            if is_saved is not None:
                analysis.is_saved = is_saved
            
            session.commit()
            logger.info(f"Successfully updated notes for analysis with ID: {analysis_id}")
            return True
        
        logger.warning(f"No analysis found to update with ID: {analysis_id}")
        return False
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating notes for analysis with ID {analysis_id}: {str(e)}")
        raise e
    finally:
        session.close()