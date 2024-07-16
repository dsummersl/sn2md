#!/bin/bash

# nounset: undefined variable outputs error message, and forces an exit
# set -u
# errexit: abort script at first error
# set -e
# print command to stdout before executing it:
# set -x

cd ~/Documents/obsidian-vaults

# Initialize pyenv
export PYENV_ROOT="/Users/danesummers/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(/opt/homebrew/bin/pyenv init --path)"

# Set Python version using pyenv
source /Users/danesummers/.pyenv/versions/3.11.9/envs/obsidian-vaults/bin/activate
# bring in open api keys:
source ~/.zprofile

# Using Poetry to run the script directly
output=$(sn2md directory ~/Dropbox/Supernote/Note -t supernote-template.yaml -o supernote)
echo "$output" | while IFS= read -r markdown_file; do
    if [ -z "$markdown_file" ]; then
        continue
    fi
    echo "  Processed to $markdown_file"
    year=$(echo $markdown_file | grep -oE '[0-9]{4}' | head -1)
    cp "$markdown_file" "personal-obsidian/Journals/$year/"
    # copy over the images in the same directory too
    image_dir=$(dirname $markdown_file)
    mkdir -p "personal-obsidian/Journals/$year/$image_dir"
    cp "$image_dir/"*.png "personal-obsidian/Journals/$year/$image_dir"
done
