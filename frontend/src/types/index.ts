type Song = {
  created_at: string;
  id: string;
  job_id: string | null;
  name: string;
  transcription?: string | null;
  transcription_url: string | null;
  updated_at: string;
};

export type { Song };
