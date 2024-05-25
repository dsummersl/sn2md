#!/bin/bash

# nounset: undefined variable outputs error message, and forces an exit
set -u
# errexit: abort script at first error
# set -e
# print command to stdout before executing it:
set -x

cd ~/Documents/obsidian-vaults

# Initialize pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(/opt/homebrew/bin/pyenv init --path)"

# Set Python version using pyenv
/opt/homebrew/bin/pyenv local 3.11.6

# Using Poetry to run the script directly
output=$(poetry run python import_supernote.py directory ~/Dropbox/Supernote/Note -o supernote)
status=$?
if [ $status -eq 0 ]; then
    echo "$output" | while IFS= read -r markdown_file; do
        echo "  Processed to $markdown_file"
        year=$(echo $markdown_file | grep -oE '[0-9]{4}' | head -1)
        eval "cp $markdown_file ~/Documents/obsidian-vaults/personal-obsidian/Journals/$year/"
    done
else
    echo "  Skipping directory processing"
fi

