import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
import { fetchTrackById } from "../api/songs";
import { Song } from "../types";

const Track = () => {
  const { id } = useParams();
  const [track, setTrack] = useState<Song | null>(null);
  const [musicXml, setMusicXml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);

  useEffect(() => {
    if (!containerRef.current || osmdRef.current) {
      return;
    }

    osmdRef.current = new OpenSheetMusicDisplay(containerRef.current, {
      autoResize: true,
      backend: "svg",
    });

    return () => {
      osmdRef.current?.clear();
      osmdRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!id) {
      setError("Missing track id");
      return;
    }

    const loadTrack = async () => {
      setLoading(true);
      setError(null);
      setMusicXml(null);
      setRenderError(null);

      try {
        const data = await fetchTrackById(id);
        setTrack(data);
        setMusicXml(data.transcription ?? null);
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

  useEffect(() => {
    const osmd = osmdRef.current;

    if (!osmd) {
      return;
    }

    if (!musicXml) {
      osmd.clear();
      return;
    }

    let cancelled = false;

    const renderScore = async () => {
      setRenderError(null);
      try {
        await osmd.load(musicXml);
        if (!cancelled) {
          await osmd.render();
        }
      } catch (err) {
        console.error("Failed to render MusicXML", err);
        if (!cancelled) {
          setRenderError("Unable to render the MusicXML score.");
        }
      }
    };

    renderScore();

    return () => {
      cancelled = true;
    };
  }, [musicXml]);

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

      {renderError && <p className="text-red-600">{renderError}</p>}

      <div>
        <h2 className="text-xl font-semibold">MusicXML Transcription</h2>
        {!musicXml && !loading && (
          <p>Transcription is not available yet for this track.</p>
        )}
        <div
          ref={containerRef}
          className="mt-4 min-h-[200px] overflow-auto rounded border bg-white p-4"
        />
      </div>
    </div>
  );
};

export default Track;
