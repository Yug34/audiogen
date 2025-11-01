#!/usr/bin/env python3
"""
Test script for file upload and processing flow.

Usage:
    python test_upload.py <path_to_audio_file>
    
Example:
    python test_upload.py ./test_audio.mp3
"""

import requests
import time
import sys
from pathlib import Path


def upload_file(file_path: str) -> str:
    """Upload file and return job ID"""
    print(f"\n📤 Uploading file: {file_path}")
    
    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f)}
        
        try:
            response = requests.post(
                "http://localhost:4000/api/v1/jobs",
                files=files,
                timeout=300  # 5 minutes timeout for large files
            )
            response.raise_for_status()
            data = response.json()
            job_id = data["id"]
            print(f"✅ Upload successful! Job ID: {job_id}")
            return job_id
        except requests.exceptions.RequestException as e:
            print(f"❌ Upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"   Error details: {e.response.json()}")
                except:
                    print(f"   Status code: {e.response.status_code}")
            sys.exit(1)


def poll_job_status(job_id: str, max_wait: int = 120) -> dict:
    """Poll job status until completion or timeout"""
    print(f"\n⏳ Polling job status...")
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://localhost:4000/api/v1/jobs/{job_id}")
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            
            # Print status changes
            if status != last_status:
                print(f"   Status: {status}")
                last_status = status
            
            # Check for completion
            if status == "finished":
                print(f"\n✅ Job completed!")
                return data
            elif status == "failed":
                error = data.get("error", "Unknown error")
                print(f"\n❌ Job failed: {error}")
                return data
            elif status in ["started", "queued"]:
                progress = data.get("progress", 0)
                if progress:
                    print(f"   Progress: {progress}%")
            
            time.sleep(2)
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Error polling job status: {e}")
            break
    
    print(f"\n⏱️  Timeout waiting for job completion (max {max_wait}s)")
    return data if 'data' in locals() else {}


def display_results(data: dict):
    """Display job results"""
    print("\n" + "="*60)
    print("📊 Job Results")
    print("="*60)
    
    if data.get("status") == "finished":
        print(f"\n✅ Status: {data.get('status')}")
        print(f"📈 Progress: {data.get('progress', 0)}%")
        
        # Display MusicXML result
        artifacts = data.get("artifacts", {})
        musicxml = artifacts.get("musicxml", {})
        
        if musicxml.get("content"):
            print(f"\n🎵 MusicXML String (first 200 chars):")
            print(f"   {musicxml['content'][:200]}...")
            print(f"\n📄 Full MusicXML:")
            print(musicxml['content'])
        elif data.get("result"):
            print(f"\n🎵 MusicXML String (first 200 chars):")
            print(f"   {data['result'][:200]}...")
            print(f"\n📄 Full MusicXML:")
            print(data['result'])
        else:
            print("\n⚠️  No MusicXML content found in response")
    else:
        print(f"\n❌ Status: {data.get('status', 'unknown')}")
        if data.get("error"):
            print(f"   Error: {data['error']}")


def check_services():
    """Check if required services are running"""
    print("🔍 Checking services...")
    
    # Check backend
    try:
        response = requests.get("http://localhost:4000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend API is running")
        else:
            print("   ⚠️  Backend API returned non-200 status")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Backend API is not accessible: {e}")
        print("   💡 Make sure backend is running on http://localhost:4000")
        return False
    
    return True


def main():
    """Main test function"""
    print("="*60)
    print("🧪 File Upload & Processing Test")
    print("="*60)
    
    # Check if file path provided
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide a file path")
        print(f"   Usage: {sys.argv[0]} <path_to_audio_file>")
        print("   Example: python test_upload.py ./test_audio.mp3")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check services
    if not check_services():
        print("\n💡 Tips:")
        print("   1. Start backend: cd backend && uvicorn app.main:app --reload")
        print("   2. Start worker: cd worker && python -m worker.worker")
        print("   3. Ensure Redis is running: docker-compose up -d redis")
        sys.exit(1)
    
    # Upload file
    job_id = upload_file(file_path)
    
    # Poll for results
    result = poll_job_status(job_id)
    
    # Display results
    display_results(result)
    
    print("\n" + "="*60)
    print("✨ Test completed!")
    print("="*60)


if __name__ == "__main__":
    main()

