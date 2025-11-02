from __future__ import annotations

from pathlib import Path
import os
import sys
from uuid import UUID

# Add parent directory to path to import backend models
# This allows the worker to import from backend module
root_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.abspath(root_dir))

from backend.app.database import get_db_session
from backend.app.models import Song, Transcription


def audio_to_musicxml(audio_path: str, songName: str, song_id: str) -> str:
    """Convert an audio file to MusicXML drum tabs and save to database.

    Args:
        audio_path: Path to the audio file
        songName: Name of the song
        song_id: UUID of the song record in database

    Returns:
        MusicXML string
    """
    # Validate input path exists early to fail fast
    if not Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"Processing audio file: {audio_path}")
    print(f"Song name: {songName}")
    print(f"Song ID: {song_id}")
    
    # TODO: load model, perform inference, generate MusicXML
    # Placeholder minimal MusicXML structure
    musicxml = f"<score-partwise version=\"3.1\"><work><work-title>{songName}</work-title></work></score-partwise>"
    print(f"MusicXML: {musicxml}")
    
    # Save transcription to database
    try:
        with get_db_session() as db:
            # Convert song_id string to UUID if needed
            song_uuid = UUID(song_id) if isinstance(song_id, str) else song_id
            
            # Find the song by ID
            song = db.query(Song).filter(Song.id == song_uuid).first()
            if not song:
                raise ValueError(f"Song with ID {song_id} not found in database")
            
            # Create or update transcription
            transcription = db.query(Transcription).filter(Transcription.song_id == song_uuid).first()
            if transcription:
                # Update existing transcription
                transcription.musicxml = musicxml
                transcription.status = "completed"
            else:
                # Create new transcription
                transcription = Transcription(
                    song_id=song_uuid,
                    musicxml=musicxml,
                    status="completed"
                )
                db.add(transcription)
            # get_db_session context manager will commit on successful exit
            print(f"Transcription saved to database for song {song_id}")
    except Exception as e:
        print(f"Error saving transcription to database: {str(e)}")
        # Continue even if database save fails - still return the musicxml
        # You might want to handle this differently in production
    
    return musicxml


