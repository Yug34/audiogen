import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { OpenSheetMusicDisplay } from "opensheetmusicdisplay";
import * as Tone from "tone";
import { fetchTrackById } from "../api/songs";
import { Song } from "../types";
import { defaultMusicXml } from "./constants";
// Import sample files
import kickSample from "../instruments/kick.mp3";
import snareSample from "../instruments/snare.mp3";
import hihatClosedSample from "../instruments/hihatclosed.mp3";
import hihatOpenSample from "../instruments/hihatopen.mp3";
import crashSample from "../instruments/crash.mp3";
import rideSample from "../instruments/ride.mp3";

type PlaybackEvent = {
  startSeconds: number;
  durationSeconds: number;
  midi: number;
  velocity: number;
  instrumentId: string | null;
};

const stepToMidiNumber = (step: string, octave: number) => {
  const normalizedStep = step.toUpperCase();
  const stepMap: Record<string, number> = {
    C: 0,
    D: 2,
    E: 4,
    F: 5,
    G: 7,
    A: 9,
    B: 11,
  };

  const base = stepMap[normalizedStep] ?? 0;
  return (octave + 1) * 12 + base + 12;
};

const parseMusicXmlToEvents = (
  xml: string
): { events: PlaybackEvent[]; tempo: number } => {
  if (typeof window === "undefined" || !window.DOMParser) {
    throw new Error("MusicXML parsing requires a browser DOM environment.");
  }

  const normalizedXml = xml.replace(/^\uFEFF/, "").trimStart();
  const sanitizedXml = normalizedXml.replace(/<!DOCTYPE[\s\S]*?>/i, "");

  const parser = new window.DOMParser();
  const doc = parser.parseFromString(sanitizedXml, "application/xml");

  const parseError = doc.querySelector("parsererror");
  if (parseError) {
    throw new Error(parseError.textContent ?? "Failed to parse MusicXML.");
  }

  const divisionsText = doc.querySelector(
    "part > measure > attributes > divisions"
  )?.textContent;
  const initialDivisions = Number(divisionsText ?? "1") || 1;

  const soundElement = doc.querySelector("part > measure > sound[tempo]");
  const tempo = Number(soundElement?.getAttribute("tempo") ?? "120") || 120;

  const divisionsToSeconds = (durationInDivisions: number) => {
    const secondsPerQuarter = 60 / tempo;
    const divisionsPerQuarter = initialDivisions;
    return (durationInDivisions / divisionsPerQuarter) * secondsPerQuarter;
  };

  const events: PlaybackEvent[] = [];

  const measures = Array.from(doc.querySelectorAll("part > measure"));
  let measureOffsetInDivisions = 0;

  measures.forEach((measure) => {
    const voiceTimes = new Map<string, number>();
    // Track the current position in the measure (affected by backup/forward)
    let currentPosition = measureOffsetInDivisions;
    // Process all measure children in order (notes, backups, forwards, etc.)
    const measureChildren = Array.from(measure.children);

    measureChildren.forEach((element) => {
      if (element.tagName === "backup") {
        // Handle backup: move the current position back by the backup duration
        const backupDurationText =
          element.querySelector("duration")?.textContent ?? "0";
        const backupDuration = Number(backupDurationText) || 0;
        currentPosition = Math.max(
          measureOffsetInDivisions,
          currentPosition - backupDuration
        );
      } else if (element.tagName === "forward") {
        // Handle forward: advance the current position by the forward duration
        const forwardDurationText =
          element.querySelector("duration")?.textContent ?? "0";
        const forwardDuration = Number(forwardDurationText) || 0;
        currentPosition += forwardDuration;
      } else if (element.tagName === "note") {
        const note = element;
        const voice = note.querySelector("voice")?.textContent ?? "1";
        const durationText = note.querySelector("duration")?.textContent ?? "0";
        const durationInDivisions = Number(durationText) || 0;
        const isRest = note.querySelector("rest") !== null;
        const isChord = note.querySelector("chord") !== null;

        // Use the voice's tracked time if it exists, otherwise use current position
        const voiceStart = voiceTimes.get(voice) ?? currentPosition;

        if (!isRest) {
          const step =
            note.querySelector("pitch > step")?.textContent ??
            note.querySelector("unpitched > display-step")?.textContent ??
            "C";
          const octave = Number(
            note.querySelector("pitch > octave")?.textContent ??
              note.querySelector("unpitched > display-octave")?.textContent ??
              "4"
          );
          const midi = stepToMidiNumber(step, octave);
          const instrumentId =
            note.querySelector("instrument")?.getAttribute("id") ?? null;

          events.push({
            midi,
            startSeconds: divisionsToSeconds(voiceStart),
            durationSeconds: divisionsToSeconds(
              durationInDivisions || initialDivisions
            ),
            velocity: 0.8,
            instrumentId,
          });
        }

        console.log(events);

        if (!isChord) {
          voiceTimes.set(voice, voiceStart + durationInDivisions);
        }
      }
    });

    const measureVoices = Array.from(voiceTimes.values());
    const measureDurationInDivisions =
      measureVoices.length > 0
        ? Math.max(...measureVoices) - measureOffsetInDivisions
        : 0;

    measureOffsetInDivisions += measureDurationInDivisions;
  });

  return { events, tempo };
};

// Map instrument IDs to sample files
const instrumentToSample: Record<string, string> = {
  "P1-X2": kickSample, // Kick Drum
  "P1-X4": snareSample, // Snare Drum
  "P1-X6": hihatClosedSample, // Hi-Hat Closed
  "P1-X7": hihatOpenSample, // Hi-Hat Open (standard MIDI mapping)
  "P1-X13": crashSample, // Crash Cymbal
  "P1-X51": rideSample, // Ride Cymbal (standard MIDI mapping)
};

const Track = () => {
  const { id } = useParams();
  const [track, setTrack] = useState<Song | null>(null);
  const [musicXml, setMusicXml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const osmdRef = useRef<OpenSheetMusicDisplay | null>(null);
  const playersRef = useRef<Map<string, Tone.Player>>(new Map());
  const [playbackState, setPlaybackState] = useState<
    "stopped" | "playing" | "paused"
  >("stopped");

  const { events, tempo } = useMemo(() => {
    if (!musicXml) {
      return { events: [] as PlaybackEvent[], tempo: 120 };
    }

    try {
      return parseMusicXmlToEvents(musicXml);
    } catch (err) {
      console.error("Unable to parse MusicXML for playback", err);
      return { events: [] as PlaybackEvent[], tempo: 120 };
    }
  }, [musicXml]);

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
    // Initialize Tone.Player instances for each instrument
    const players = new Map<string, Tone.Player>();

    Object.entries(instrumentToSample).forEach(([instrumentId, samplePath]) => {
      const player = new Tone.Player({
        url: samplePath,
        volume: -8,
      }).toDestination();
      players.set(instrumentId, player);
    });

    playersRef.current = players;

    return () => {
      // Cleanup: dispose all players
      players.forEach((player) => player.dispose());
      playersRef.current.clear();
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
        setMusicXml(defaultMusicXml);
        // setMusicXml(data.transcription ?? null);
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

  useEffect(() => {
    return () => {
      Tone.Transport.stop();
      Tone.Transport.cancel(0);
    };
  }, []);

  const schedulePlayback = () => {
    Tone.Transport.cancel(0);
    Tone.Transport.seconds = 0;
    Tone.Transport.bpm.value = tempo;

    console.log(events);

    // Filter and sort events by start time to ensure strictly increasing order
    const validEvents = events
      .filter((event) => event.instrumentId)
      .sort((a, b) => a.startSeconds - b.startSeconds);

    // Schedule events with epsilon offset for events with same start time
    let lastScheduledTime = -1;
    const EPSILON = 0.0001; // Small offset to ensure strictly increasing times

    validEvents.forEach((event) => {
      const player = playersRef.current.get(event.instrumentId!);
      if (player && player.loaded) {
        // Ensure start time is strictly greater than previous
        let scheduleTime = event.startSeconds;
        if (scheduleTime <= lastScheduledTime) {
          scheduleTime = lastScheduledTime + EPSILON;
        }
        lastScheduledTime = scheduleTime;

        Tone.Transport.schedule((time: number) => {
          player.start(time, 0, event.durationSeconds);
        }, scheduleTime);
      }
    });
  };

  const handlePlay = async () => {
    if (!events.length || playersRef.current.size === 0) {
      return;
    }

    await Tone.start();

    // Wait for all samples to be loaded before playing
    const players = Array.from(playersRef.current.values());
    const allLoaded = players.every((player) => player.loaded);

    if (!allLoaded) {
      // Wait for samples to load (Player loads automatically when URL is set)
      try {
        await Promise.all(
          players.map(
            (player) =>
              new Promise<void>((resolve) => {
                if (player.loaded) {
                  resolve();
                } else {
                  const checkLoaded = () => {
                    if (player.loaded) {
                      resolve();
                    } else {
                      setTimeout(checkLoaded, 50);
                    }
                  };
                  checkLoaded();
                }
              })
          )
        );
      } catch (error) {
        console.error("Error loading samples:", error);
      }
    }

    if (playbackState === "paused") {
      Tone.Transport.start();
    } else {
      schedulePlayback();
      Tone.Transport.start("+0.05");
    }

    setPlaybackState("playing");
  };

  const handlePause = () => {
    Tone.Transport.pause();
    setPlaybackState("paused");
  };

  const handleStop = () => {
    Tone.Transport.stop();
    Tone.Transport.seconds = 0;
    setPlaybackState("stopped");
  };

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
        <div className="mt-2 flex items-center gap-2">
          <button
            className="rounded bg-blue-600 px-3 py-1 text-white disabled:opacity-50"
            onClick={handlePlay}
            disabled={events.length === 0}
          >
            {playbackState === "playing" ? "Restart" : "Play"}
          </button>
          <button
            className="rounded bg-slate-200 px-3 py-1 disabled:opacity-50"
            onClick={handlePause}
            disabled={events.length === 0 || playbackState !== "playing"}
          >
            Pause
          </button>
          <button
            className="rounded bg-slate-200 px-3 py-1 disabled:opacity-50"
            onClick={handleStop}
            disabled={events.length === 0 || playbackState === "stopped"}
          >
            Stop
          </button>
          <div className="text-sm text-slate-600">Tempo: {tempo} BPM</div>
        </div>
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
