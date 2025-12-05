import os
import sys
import json

import magenta
import note_seq
import tensorflow as tf

# Add parent directory to path to access audio files
root_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.abspath(root_dir))


def transcribe_audio_to_midi(audio_path: str):
    """Transcribe an audio file to MIDI using Magenta.
    
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
        # Try to load using note_seq audio utilities
        try:
            import librosa
            print(f"Loading audio file with librosa...")
            print(f"librosa imported from: {librosa.__file__}")
            audio_samples, sample_rate = librosa.load(audio_path, sr=16000)
            
            # Create NoteSequence from audio
            # Note: For full transcription, you'd load the onsets_frames_transcription model
            # This is a simplified version that creates a basic structure
            ns = note_seq.NoteSequence()
            ns.tempos.add(time=0, qpm=120.0)
            
            print("Note: For full audio-to-MIDI transcription, load the onsets_frames_transcription model checkpoint.")
            print("This example shows the structure - you'll need to run inference with the trained model.")
            
        except ImportError:
            print("librosa not found. Please install: pip install librosa")
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