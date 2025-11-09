import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchTrackById } from "../api/songs";
import { Song } from "../types";

const Track = () => {
  const { id } = useParams();
  const [track, setTrack] = useState<Song | null>(null);
  const [musicXml, setMusicXml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (musicXml) {
      console.log(musicXml);
    }
  }, [musicXml]);

  useEffect(() => {
    if (!id) {
      setError("Missing track id");
      return;
    }

    const loadTrack = async () => {
      setLoading(true);
      setError(null);
      setMusicXml(null);

      try {
        const data = (await fetchTrackById(id)) as Song & {
          transcription: string;
        };
        setTrack(data);
        console.log(data);
        setMusicXml(data.transcription);
      } catch (err) {
        console.error(err);
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("An unexpected error occurred while loading the track.");
        }
      } finally {
        setLoading(false);
      }
    };

    loadTrack();
  }, [id]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Track {id}</h1>

      {loading && <p>Loading track information...</p>}

      {error && <p className="text-red-600">{error}</p>}

      {track && (
        <div className="space-y-2">
          <p className="text-lg font-semibold">{track.name}</p>
          {/* {track.transcription ? (
            <a
              className="text-blue-600 underline"
              href={track.transcription}
              target="_blank"
              rel="noopener noreferrer"
            >
              Download MusicXML
            </a>
          ) : (
            <p>Transcription is not available yet.</p>
          )} */}
        </div>
      )}

      {musicXml && (
        <div>
          <h2 className="text-xl font-semibold">MusicXML Transcription</h2>
          <pre className="whitespace-pre-wrap overflow-auto border rounded p-4 max-h-96">
            {musicXml}
          </pre>
        </div>
      )}
    </div>
  );
};

export default Track;
