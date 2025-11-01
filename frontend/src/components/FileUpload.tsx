import { useEffect, useState } from "react";
import {
  Dropzone,
  DropzoneContent,
  DropzoneEmptyState,
} from "../components/ui/dropzone";

export default function FileUpload() {
  const [files, setFiles] = useState<File[] | undefined>();

  useEffect(() => {
    if (files) {
      const file = files[0];
      console.log("File uploaded:", file);
      const formData = new FormData();
      formData.append("file", file);
      fetch("http://localhost:4000/api/v1/jobs", {
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
        })
        .catch((error) => {
          console.error("Upload error:", error);
        });
    }
  }, [files]);

  const handleDrop = (files: File[]) => {
    setFiles(files);
  };

  return (
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
      src={files}
    >
      <DropzoneEmptyState />
      <DropzoneContent />
    </Dropzone>
  );
}
