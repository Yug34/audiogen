import { Button } from "./components/ui/button";
import { Upload } from "lucide-react";

export function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b">
        <div className="container py-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">AI Drum Tab Generator</h1>
          <div className="flex items-center gap-2">
            <Button variant="ghost">Docs</Button>
            <Button>Sign in</Button>
          </div>
        </div>
      </header>
      <main className="container flex-1 py-10">
        <div className="mx-auto max-w-2xl rounded-lg border p-8">
          <h2 className="text-lg font-medium mb-2">Upload an MP3</h2>
          <p className="text-sm text-muted-foreground mb-6">
            We’ll generate a MusicXML + MIDI drum transcription. You’ll get a
            link to view and download the result.
          </p>
          <div className="flex items-center justify-center border-2 border-dashed rounded-lg p-8">
            <div className="text-center">
              <Upload className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-4 text-sm">Drag & drop your file here, or</p>
              <div className="mt-4">
                <Button>Choose file</Button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                MP3 up to 100MB
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
