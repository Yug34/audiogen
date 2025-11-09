from __future__ import annotations

from pathlib import Path
import os
import sys
from uuid import UUID

# Add parent directory to path to import backend models
# This allows the worker to import from backend module
root_dir = os.path.join(os.path.dirname(__file__), '..')
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, os.path.abspath(root_dir))
sys.path.insert(0, os.path.abspath(backend_dir))

from backend.app.database import get_db_session
from backend.app.models import Song
from worker.s3_client import save_transcription_to_s3


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
    musicxml = f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC
  "-//Recordare//DTD MusicXML 3.1 Partwise//EN"
  "http://www.musicxml.org/dtds/partwise.dtd">

<score-partwise version="3.1">
  <work><work-title>{songName}</work-title></work>

  <part-list>
    <score-part id="P1">
      <part-name>Drum Set</part-name>

      <!-- Force 5 lines at the part-definition level -->
      <staff-details>
        <staff-lines>5</staff-lines>
      </staff-details>

      <score-instrument id="P1-I1"><instrument-name>Kick</instrument-name></score-instrument>
      <score-instrument id="P1-I2"><instrument-name>Snare</instrument-name></score-instrument>

      <midi-instrument id="P1-I1"/>
      <midi-instrument id="P1-I2"/>
    </score-part>
  </part-list>

  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>4</divisions>

        <!-- also set staff-lines here -->
        <staff-details>
          <staff-lines>5</staff-lines>
        </staff-details>

        <time><beats>4</beats><beat-type>4</beat-type></time>

        <clef>
          <sign>percussion</sign>
          <line>2</line>
        </clef>
      </attributes>

      <!-- Kick - beat 1 (moved lower: C2) -->
      <note>
        <unpitched>
          <step>C</step>
          <octave>2</octave>
          <display-step>C</display-step>
          <display-octave>2</display-octave>
        </unpitched>
        <duration>4</duration>
        <type>quarter</type>
        <instrument id="P1-I1"/>
        <voice>1</voice>
        <staff>1</staff>
      </note>

      <!-- Kick - beat 2 (C2) -->
      <note>
        <unpitched>
          <step>C</step>
          <octave>2</octave>
        </unpitched>
        <duration>4</duration>
        <type>quarter</type>
        <instrument id="P1-I1"/>
        <voice>1</voice>
        <staff>1</staff>
      </note>

      <!-- Kick - beat 3 (C2) -->
      <note>
        <unpitched>
          <step>C</step>
          <octave>2</octave>
        </unpitched>
        <duration>4</duration>
        <type>quarter</type>
        <instrument id="P1-I1"/>
        <voice>1</voice>
        <staff>1</staff>
      </note>

      <!-- Snare - beat 4 (unchanged) -->
      <note>
        <unpitched>
          <step>C</step>
          <octave>5</octave>
          <display-step>C</display-step>
          <display-octave>5</display-octave>
        </unpitched>
        <duration>4</duration>
        <type>quarter</type>
        <instrument id="P1-I2"/>
        <voice>1</voice>
        <staff>1</staff>
      </note>

    </measure>
  </part>
</score-partwise>
"""
    print(f"MusicXML: {musicxml}")
    
    # Save transcription to MinIO/S3
    transcription_url = save_transcription_to_s3(musicxml, song_id, songName)
    print(f"Transcription URL: {transcription_url}")
    
    # Update song record with transcription URL
    try:
        with get_db_session() as db:
            # Convert song_id string to UUID if needed
            song_uuid = UUID(song_id) if isinstance(song_id, str) else song_id
            
            # Find the song by ID
            song = db.query(Song).filter(Song.id == song_uuid).first()
            if not song:
                raise ValueError(f"Song with ID {song_id} not found in database")
            
            # Update song with transcription URL
            song.transcription_url = transcription_url
            # get_db_session context manager will commit on successful exit
            print(f"Transcription URL saved to database for song {song_id}: {transcription_url}")
    except Exception as e:
        print(f"Error saving transcription URL to database: {str(e)}")
        # Continue even if database update fails - still return the musicxml
        # You might want to handle this differently in production
    
    return musicxml


