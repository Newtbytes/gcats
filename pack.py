import os
import io
import zipfile
import requests

def download_zip(url):
    response = requests.get(url)
    response.raise_for_status()
    return io.BytesIO(response.content)

def merge_zips(zip_streams, output_path):
    seen_files = set()
    with zipfile.ZipFile(output_path, 'w') as output_zip:
        for zip_stream in zip_streams:
            with zipfile.ZipFile(zip_stream) as zip_file:
                for name in zip_file.namelist():
                    if name in seen_files or name.endswith('/'):
                        continue  # Skip duplicates and directories
                    seen_files.add(name)
                    data = zip_file.read(name)
                    output_zip.writestr(name, data)

def main(url_list_path, output_zip_path):
    with open(url_list_path, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    
    zip_streams = []
    for url in urls:
        print(f"Downloading: {url}")
        try:
            zip_streams.append(download_zip(url))
        except Exception as e:
            print(f"Failed to download {url}: {e}")
    
    print(f"Merging {len(zip_streams)} ZIPs into: {output_zip_path}")
    merge_zips(zip_streams, output_zip_path)
    print("Done.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Download and merge ZIP files from a list of URLs.")
    parser.add_argument("url_list", help="Path to text file containing ZIP URLs")
    parser.add_argument("output_zip", help="Path to output merged ZIP file")
    args = parser.parse_args()
    
    main(args.url_list, args.output_zip)
