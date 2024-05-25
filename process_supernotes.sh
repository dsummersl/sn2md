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
for file in ~/Dropbox/Supernote/Note/*.note; do
    echo "Processing $file"
    set +e
    markdown_file=$(poetry run python import_supernote.py -o supernote "$file")
    status=$?
    set -e
    if [ $status -eq 0 ]; then
        echo "  Processed $file to $markdown_file"
        year=$(echo $file | grep -oE '[0-9]{4}' | head -1)
        eval "cp $markdown_file ~/Documents/obsidian-vaults/personal-obsidian/Journals/$year/"
    else
        echo "  Skipping $file"
    fi
done

