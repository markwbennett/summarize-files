# Folder and Repository Renames

This document describes the changes made to standardize folder names to kebab-case and align GitHub repository names accordingly.

## Folder Renames (Local Directories)

The following folders in `/Users/markbennett/github` were renamed from their original names to kebab-case versions:

- Audio_Cleanup → audio-cleanup
- AVViewer_Analysis → avviewer-analysis
- brief_analyzer → brief-analyzer
- brief_enhancer → brief-enhancer
- cause_chart → cause-chart
- 'Chrome Extensions' → chrome-extensions
- cite_check → cite-check
- CivAppBoardCert → civappboardcert
- cursor_settings → cursor-settings
- DailyBriefing → dailybriefing
- 'Data_Analysis_on_MBP' → data-analysis-on-mbp
- 'deskew text' → deskew-text
- Devel → devel
- Discovery_Processor → discovery-processor
- download_fastmail_attachments → download-fastmail-attachments
- drag-and-drop_processing → drag-and-drop-processing
- EDiscovery → ediscovery
- EdiscoveryZ → ediscoveryz
- FastmailArchiver → fastmailarchiver
- fill_template → fill-template
- Garmin_Watch → garmin-watch
- GTI → gti
- lawyer_file_updater → lawyer-file-updater
- Lawyer_Stats → lawyer-stats
- mac-deduce_mbox_owner → mac-deduce-mbox-owner
- 'Nick Script' → nick-script
- PDR → pdr
- 'PDR AI Detector' → pdr-ai-detector
- privilege_log → privilege-log
- 'Smart OCR' → smart-ocr
- Summarize_Files → summarize-files
- TimeTrackButton → timetrackbutton
- vivaldi_mods → vivaldi-mods
- Voice → voice
- Wasabi → wasabi

Folders that were already in kebab-case or lowercase were not changed (e.g., mac-*, homebrew-*, dotconfig, mailrules, etc.).

## Repository Renames (GitHub)

The following GitHub repositories were renamed to match the new folder names:

- DailyBriefing → dailybriefing
- TimeTrackButton → timetrackbutton
- mac-deduce_mbox_owner → mac-deduce-mbox-owner
- PDR-AI-Detector → pdr-ai-detector
- Discovery_Processor → discovery-processor
- Summarize_Files → summarize-files

## Actions Taken

1. Local folders renamed using `mv` commands.
2. GitHub repositories renamed using `gh repo rename`.
3. Local git remotes updated using `git remote set-url` to point to the new repository URLs.

## Instructions for Other Servers/Agents

To synchronize your local structure with these changes:

1. Rename the corresponding local folders to the new kebab-case names.
2. If you have clones of the renamed repositories, update the remote URLs:
   - For each renamed repo, run: `git remote set-url origin https://github.com/markwbennett/new-name.git`
3. If repositories were cloned with the old names, you may need to re-clone or rename the local directories accordingly.
4. Ensure any scripts or configurations referencing the old folder/repo names are updated.

This ensures consistency across all environments.