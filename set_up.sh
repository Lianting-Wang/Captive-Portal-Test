#!/bin/bash

# Update package lists and install curl and unzip if they are not installed
sudo apt update
sudo apt install -y curl unzip

# Create and navigate to the target directory
mkdir -p ~/Captive-Portal
cd ~/Captive-Portal || exit

# Download and unzip the archive
curl -L -o Captive-Portal.zip https://github.com/Lianting-Wang/Captive-Portal-Test/archive/refs/heads/main.zip
unzip -o Captive-Portal.zip
rm Captive-Portal.zip

# Move the extracted files to the current directory
# Get the name of the extracted directory (assuming the zip contains only one top-level directory)
extracted_dir=$(find . -mindepth 1 -maxdepth 1 -type d)

# Move files to the current directory and remove the temporary directory
if [ -d "$extracted_dir" ]; then
  mv "$extracted_dir"/* .
  rmdir "$extracted_dir"
fi
