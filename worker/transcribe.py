import os
import sys
import json
import numpy as np

import magenta
import note_seq
import tensorflow as tf

# Add parent directory to path to access audio files
root_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.abspath(root_dir))


def hz_to_midi_pitch(freq):
    """Convert frequency in Hz to MIDI pitch number."""
    if freq <= 0:
        return None
    # MIDI pitch = 69 + 12 * log2(freq / 440)
    midi = 69 + 12 * np.log2(freq / 440.0)
    return int(round(midi))


def detect_notes_from_pitch(pitches, times, frame_length=2048, hop_length=512, sample_rate=22050):
    """Detect notes from pitch track using onset detection and pitch tracking.
    
    Args:
        pitches: Array of pitch frequencies (Hz) over time (can contain NaN)
        times: Time array corresponding to pitch frames
        frame_length: FFT frame length
        hop_length: Hop length between frames
        sample_rate: Sample rate of audio
    
    Returns:
        List of (start_time, end_time, pitch, velocity) tuples
    """
    notes = []
    min_note_duration = 0.05  # Minimum note duration in seconds
    pitch_change_threshold = 2  # Semitones
    
    # Find note onsets by detecting pitch changes
    current_pitch = None
    note_start = None
    note_pitch = None
    
    for i, (time, pitch) in enumerate(zip(times, pitches)):
        # Check if pitch is valid (not NaN, not zero)
        try:
            is_valid = not np.isnan(pitch) and pitch > 0
        except (TypeError, ValueError):
            is_valid = pitch > 0 if pitch else False
        
        if is_valid:
            pitch_midi = hz_to_midi_pitch(pitch)
            if pitch_midi is None or pitch_midi < 21 or pitch_midi > 108:  # Valid MIDI range
                # Invalid pitch - end current note
                if current_pitch is not None and note_start is not None:
                    if (time - note_start) >= min_note_duration:
                        notes.append((note_start, time, note_pitch, 80))
                    current_pitch = None
                    note_start = None
                continue
                
            if current_pitch is None:
                # Start new note
                current_pitch = pitch_midi
                note_start = time
                note_pitch = pitch_midi
            elif abs(pitch_midi - current_pitch) > pitch_change_threshold:  # Significant pitch change
                # End previous note if it's long enough
                if note_start is not None and (time - note_start) >= min_note_duration:
                    notes.append((note_start, time, note_pitch, 80))
                # Start new note
                current_pitch = pitch_midi
                note_start = time
                note_pitch = pitch_midi
            else:
                # Same pitch, continue note (update pitch to median/average if needed)
                # Keep the note going
                pass
        else:
            # No pitch detected - end current note if exists
            if current_pitch is not None and note_start is not None:
                if (time - note_start) >= min_note_duration:
                    notes.append((note_start, time, note_pitch, 80))
                current_pitch = None
                note_start = None
    
    # Don't forget the last note
    if current_pitch is not None and note_start is not None:
        if len(times) > 0 and (times[-1] - note_start) >= min_note_duration:
            notes.append((note_start, times[-1], note_pitch, 80))
    
    return notes


def transcribe_audio_to_midi(audio_path: str):
    """Transcribe an audio file to MIDI using pitch detection.
    
    Args:
        audio_path: Path to the audio file (mp3, wav, mid, etc.)
    
    Returns:
        NoteSequence object representing the MIDI transcription
    """
    audio_path = os.path.abspath(audio_path)
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    print(f"Loading file: {audio_path}")
    
    # Check if it's already a MIDI file
    if audio_path.lower().endswith(('.mid', '.midi')):
        print("File is MIDI, loading directly...")
        ns = note_seq.midi_file_to_note_sequence(audio_path)
    else:
        # For audio files, we need to use transcription
        try:
            import librosa
            
            print(f"Loading audio file with librosa...")
            print(f"librosa imported from: {librosa.__file__}")
            
            # Load audio at higher sample rate for better pitch detection
            sample_rate = 22050
            audio_samples, sr = librosa.load(audio_path, sr=sample_rate)
            
            print(f"Audio loaded: {len(audio_samples)} samples at {sr} Hz")
            print(f"Duration: {len(audio_samples) / sr:.2f} seconds")
            
            # Detect pitch using librosa's piptrack algorithm
            print("Detecting pitch using piptrack...")
            
            hop_length = 512
            frame_length = 2048
            
            # Use piptrack for pitch detection
            pitches, magnitudes = librosa.piptrack(
                y=audio_samples,
                sr=sample_rate,
                threshold=0.1,
                fmin=librosa.note_to_hz('C2'),  # C2 (~65 Hz)
                fmax=librosa.note_to_hz('C7'),  # C7 (~2093 Hz)
                hop_length=hop_length,
                n_fft=frame_length
            )
            
            # Extract the most prominent pitch at each time frame
            pitch_track = []
            times = librosa.frames_to_time(np.arange(pitches.shape[1]), sr=sample_rate, hop_length=hop_length)
            
            for t in range(pitches.shape[1]):
                # Find the pitch with the highest magnitude in this frame
                pitch_values = pitches[:, t]
                magnitude_values = magnitudes[:, t]
                
                # Filter out zero pitches
                valid_indices = pitch_values > 0
                if np.any(valid_indices):
                    # Get the pitch with maximum magnitude
                    valid_magnitudes = magnitude_values[valid_indices]
                    valid_pitches = pitch_values[valid_indices]
                    max_idx = np.argmax(valid_magnitudes)
                    pitch = valid_pitches[max_idx]
                    pitch_track.append(float(pitch))
                else:
                    pitch_track.append(0.0)
            
            # Convert to numpy array
            pitch_track = np.array(pitch_track)
            
            print(f"Pitch track extracted: {len(pitch_track)} frames")
            valid_pitch_count = np.sum(pitch_track > 0)
            
            # Check if pitch_track is empty to avoid division by zero
            if len(pitch_track) > 0:
                valid_percentage = 100 * valid_pitch_count / len(pitch_track)
                print(f"Valid pitches detected: {valid_pitch_count} frames ({valid_percentage:.1f}%)")
            else:
                print(f"Valid pitches detected: {valid_pitch_count} frames (N/A - empty pitch track)")
            
            # If we don't have enough valid pitches, try a simpler approach
            if len(pitch_track) > 0 and valid_pitch_count < len(pitch_track) * 0.1:  # Less than 10% valid
                print("Low pitch detection rate, trying alternative method...")
                # Use harmonic-percussive separation and re-detect
                try:
                    y_harmonic, y_percussive = librosa.effects.hpss(audio_samples)
                    # Re-run piptrack on harmonic component
                    pitches2, magnitudes2 = librosa.piptrack(
                        y=y_harmonic,
                        sr=sample_rate,
                        threshold=0.05,  # Lower threshold
                        fmin=librosa.note_to_hz('C2'),
                        fmax=librosa.note_to_hz('C7'),
                        hop_length=hop_length,
                        n_fft=frame_length
                    )
                    
                    # Extract pitches again
                    pitch_track2 = []
                    for t in range(pitches2.shape[1]):
                        pitch_values = pitches2[:, t]
                        magnitude_values = magnitudes2[:, t]
                        valid_indices = pitch_values > 0
                        if np.any(valid_indices):
                            valid_magnitudes = magnitude_values[valid_indices]
                            valid_pitches = pitch_values[valid_indices]
                            max_idx = np.argmax(valid_magnitudes)
                            pitch_track2.append(float(valid_pitches[max_idx]))
                        else:
                            pitch_track2.append(0.0)
                    
                    pitch_track2 = np.array(pitch_track2)
                    valid_count2 = np.sum(pitch_track2 > 0)
                    if valid_count2 > valid_pitch_count:
                        pitch_track = pitch_track2
                        print(f"Using harmonic-separated results: {valid_count2} valid pitches")
                except Exception as e:
                    print(f"Alternative method failed: {e}, using original results")
            
            # Detect notes from pitch track
            print("Detecting notes from pitch track...")
            detected_notes = detect_notes_from_pitch(pitch_track, times, frame_length=2048, hop_length=512, sample_rate=sample_rate)
            
            print(f"Detected {len(detected_notes)} notes")
            
            # Create NoteSequence
            ns = note_seq.NoteSequence()
            ns.tempos.add(time=0, qpm=120.0)
            
            # Add detected notes to NoteSequence
            for start_time, end_time, pitch, velocity in detected_notes:
                note = ns.notes.add()
                note.pitch = int(pitch)
                note.start_time = start_time
                note.end_time = end_time
                note.velocity = velocity
                note.instrument = 0
            
            print(f"Created NoteSequence with {len(ns.notes)} notes")
            
        except ImportError as e:
            print(f"Error importing librosa: {e}")
            print("Creating empty NoteSequence structure...")
            ns = note_seq.NoteSequence()
            ns.tempos.add(time=0, qpm=120.0)
        except Exception as e:
            print(f"Error during transcription: {e}")
            import traceback
            traceback.print_exc()
            print("Creating empty NoteSequence structure...")
            ns = note_seq.NoteSequence()
            ns.tempos.add(time=0, qpm=120.0)
    
    # Print the MIDI transcription
    print("\n" + "="*60)
    print("MIDI TRANSCRIPTION")
    print("="*60)
    
    # Print NoteSequence details
    print(f"\nTotal time: {ns.total_time:.2f} seconds")
    print(f"Tempos: {len(ns.tempos)}")
    for tempo in ns.tempos:
        print(f"  - Time: {tempo.time:.2f}s, QPM: {tempo.qpm}")
    
    print(f"\nNotes: {len(ns.notes)}")
    for i, note in enumerate(ns.notes[:10]):  # Show first 10 notes
        print(f"  Note {i+1}: pitch={note.pitch}, start={note.start_time:.2f}s, "
              f"end={note.end_time:.2f}s, velocity={note.velocity}")
    if len(ns.notes) > 10:
        print(f"  ... and {len(ns.notes) - 10} more notes")
    
    print(f"\nTime signatures: {len(ns.time_signatures)}")
    for ts in ns.time_signatures:
        print(f"  - Time: {ts.time:.2f}s, {ts.numerator}/{ts.denominator}")
    
    # Print as JSON for detailed inspection
    print("\n" + "="*60)
    print("MIDI TRANSCRIPTION (JSON)")
    print("="*60)
    print(json.dumps({
        'total_time': ns.total_time,
        'tempos': [{'time': t.time, 'qpm': t.qpm} for t in ns.tempos],
        'time_signatures': [{'time': ts.time, 'numerator': ts.numerator, 'denominator': ts.denominator} 
                           for ts in ns.time_signatures],
        'notes': [{
            'pitch': n.pitch,
            'start_time': n.start_time,
            'end_time': n.end_time,
            'velocity': n.velocity,
            'instrument': n.instrument
        } for n in ns.notes],
        'total_notes': len(ns.notes)
    }, indent=2))
    
    # Also print the NoteSequence string representation
    print("\n" + "="*60)
    print("MIDI TRANSCRIPTION (NoteSequence)")
    print("="*60)
    print(str(ns))
    
    return ns


if __name__ == "__main__":
    # Default to audio.mp3 in the root directory
    audio_file = os.path.join(root_dir, "sample.mp3")
    
    # Allow command line argument for audio file path
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    
    print(f"Magenta version: {magenta.__version__}")
    print(f"TensorFlow version: {tf.__version__}")
    print()
    
    try:
        ns = transcribe_audio_to_midi(audio_file)
        print("\n✅ Transcription complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()