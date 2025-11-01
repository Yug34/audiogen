import { useState } from "react";
import {
  Dropzone,
  DropzoneContent,
  DropzoneEmptyState,
} from "../components/ui/dropzone";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";

export default function FileUpload() {
  const [file, setFile] = useState<File | undefined>();
  const [songName, setSongName] = useState<string>("");
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const handleDrop = (files: File[]) => {
    if (files.length === 1) {
      const file = files[0];
      setFile(file);
      // Pre-fill with original filename without extension
      const originalName = file.name;
      const nameWithoutExt =
        originalName.substring(0, originalName.lastIndexOf(".")) ||
        originalName;
      setSongName(nameWithoutExt);
    } else {
      return;
    }
  };

  const handleUpload = () => {
    if (!file || !songName.trim()) {
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("songName", songName.trim());

    fetch(`${import.meta.env.VITE_API_URL}/api/v1/jobs`, {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((err) => {
            throw new Error(
              err.detail || `HTTP error! status: ${response.status}`
            );
          });
        }
        return response.json();
      })
      .then((data) => {
        console.log("Upload response:", data);
        // Reset after successful upload
        setFile(undefined);
        setSongName("");
      })
      .catch((error) => {
        console.error("Upload error:", error);
      })
      .finally(() => {
        setIsUploading(false);
      });
  };

  return (
    <div className="w-full max-w-md space-y-4">
      <Dropzone
        className="cursor-pointer"
        accept={{
          "audio/*": [".mp3", ".wav", ".flac", ".m4a", ".ogg"],
        }}
        maxFiles={1}
        maxSize={1024 * 1024 * 10}
        minSize={1024}
        onDrop={handleDrop}
        onError={console.error}
        src={file ? [file] : []}
      >
        <DropzoneEmptyState />
        <DropzoneContent />
      </Dropzone>
      {file && (
        <div className="space-y-2">
          <div className="space-y-1">
            <label htmlFor="songName" className="text-sm font-medium">
              Song Name
            </label>
            <Input
              id="songName"
              type="text"
              placeholder="Enter song name"
              value={songName}
              onChange={(e) => setSongName(e.target.value)}
              disabled={isUploading}
            />
          </div>
          <Button
            onClick={handleUpload}
            disabled={!songName.trim() || isUploading}
            className="w-full"
          >
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
        </div>
      )}
    </div>
  );
}
