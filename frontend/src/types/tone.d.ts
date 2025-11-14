declare module "tone" {
  export const Transport: {
    bpm: { value: number };
    seconds: number;
    start: (time?: number | string) => void;
    stop: () => void;
    pause: () => void;
    cancel: (time?: number) => void;
    schedule: (callback: (time: number) => void, time: number) => number;
  };

  export function start(): Promise<void>;

  export function Frequency(value: number, units?: string): number;

  export class Synth {}

  export class PolySynth<TVoice = Synth> {
    constructor(
      voice?: new (...args: any[]) => TVoice,
      options?: Record<string, unknown>
    );
    triggerAttackRelease: (
      note: any,
      duration: number | string,
      time?: number,
      velocity?: number
    ) => void;
    dispose: () => void;
    toDestination: () => PolySynth<TVoice>;
  }

  export class MembraneSynth {
    constructor(options?: Record<string, unknown>);
    triggerAttackRelease: (
      note: any,
      duration: number | string,
      time?: number,
      velocity?: number
    ) => void;
    dispose: () => void;
    toDestination: () => MembraneSynth;
  }

  export class Player {
    constructor(options?: { url?: string; volume?: number });
    loaded: boolean;
    start: (time?: number, offset?: number, duration?: number) => void;
    stop: (time?: number) => void;
    dispose: () => void;
    toDestination: () => Player;
  }
}
