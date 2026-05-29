# Creative Studio

Version 1.2 | A powerful, self-updating project management system for organizing content with custom fields, media attachments, and internal linking.

License: MIT | Python 3.8+ | PySide6

## Features

Core Functionality:
- Multi-Project Management - Create and switch between multiple projects
- Custom Categories - Define your own content categories with custom fields
- Rich Text Editor - Write content with [[Page Links]] for internal navigation
- Media Attachments - Add images, GIFs, audio files, and 3D models
- Search Pages - Quickly find content across your project
- Auto-Save - Never lose your work with configurable auto-save intervals

Custom Fields:
- Single Line Text - Short text entries
- Multi-line Text - Longer notes and descriptions
- Dropdown - Predefined selection lists
- Number (Spin Box) - Numeric values with min/max ranges

User Interface:
- Dark & Light Themes
- Adjustable Font Size (8-24pt)
- Responsive Layout
- Fast Navigation

Auto-Update System:
- Self-Updating - Checks for new versions automatically
- Status Bar Notifications - Click to update when available
- One-Click Installation - Downloads and restarts automatically
- Preserves Data - All projects and settings remain intact

## Requirements

- Python 3.8 or higher
- PySide6
- Internet connection (for auto-update feature)

## Installation

Quick Start (Recommended for Users):

1. Download creative_studio.py from the latest release
2. Run: python creative_studio.py
3. First launch will prompt you to create or open a project

Manual Installation (For Developers):

1. Clone the repository:
   git clone https://github.com/yourusername/creative-studio-updates.git
   cd creative-studio-updates

2. Install dependencies:
   pip install PySide6

3. Run the application:
   python creative_studio.py

## First Time Setup

When you first run Creative Studio, you will see a welcome dialog where you can:

- Create New Project - Start a fresh project with a name and location
- Open Existing Project - Load a previously created project
- Select from Recent Projects - Quickly access your recent work

Your projects are stored in folders containing:
- studio_project.json - Main project data
- images/ - Image attachments
- media/ - Other media files (audio, 3D models)

## How to Use

Creating Categories:

1. Click "Manage Categories" in the toolbar
2. Click "Add Category"
3. Enter an internal ID (no spaces, e.g., "characters")
4. Enter a display name (e.g., "Characters")
5. Add custom fields to your category if needed

Adding Custom Fields:

1. In Manage Categories, select a category
2. Click "Add Field"
3. Choose a field type: Single Line Text, Multi-line Text, Dropdown, or Number
4. Configure field-specific options (dropdown choices, min/max values)

Creating Pages:

1. Select a category from the dropdown
2. Click "+ New Page"
3. Enter a title
4. Fill in the custom fields
5. Write content in the editor
6. Add media attachments by drag-and-drop or clicking "+ Add Media"
7. Click "Save Page" (auto-save also runs periodically)

Internal Linking:

Link between pages using double brackets:

Check out [[Character Name]] for more details.
See the [[Main Quest]] page.

Links appear in blue and are clickable in the preview panel.

Media Support:

- Images: PNG, JPG, JPEG, BMP, WEBP
- Animated: GIF (plays automatically)
- Audio: MP3, WAV, OGG (playback controls)
- 3D Models: OBJ, GLTF, GLB (file reference)

## Settings

Access settings via Edit -> Settings

Appearance:
- Theme: Switch between Dark and Light mode
- Font Size: Adjust text size (8-24 points)

Startup:
- Open Last Project: Automatically load your most recent project
- Auto-Save Interval: Set how often to save (10-300 seconds)

## Project Structure

Each project creates a folder with this structure:

MyProject/
├── studio_project.json    # Main project data
├── images/                # Image attachments
└── media/                 # Other media files

The studio_project.json file contains:
- Project name
- Category definitions
- All pages with their fields, content, and media references

## Auto-Update System

Creative Studio checks for updates automatically:

1. Background Check - 5 seconds after launch
2. Status Bar Notification - If an update is available, a clickable link appears
3. One-Click Update - Click the link to download and install
4. Automatic Restart - The app restarts with the new version

To manually check for updates: Help -> Check for Updates

Note: The app needs write permission to its own directory to update itself.

## Keyboard Shortcuts

Save All: Ctrl+S
New Page: Ctrl+N
Search: Ctrl+F

## Troubleshooting

Update Fails to Download:
- Check your internet connection
- Verify the GitHub repository is accessible
- Try Help -> Check for Updates manually

Media Files Not Displaying:
- Ensure files are in the correct project folder
- Check that file formats are supported
- Restart the application

Auto-Save Not Working:
- Verify the auto-save interval in Settings
- Check write permissions to the project folder

Can't Create Categories:
- You must have a project open first
- Category IDs cannot contain spaces
- Each category needs a unique internal ID

File Structure:

creative_studio.py          # Main application
version.txt                 # Version number (for auto-update)
README.md                   # This file

## License

MIT License

## Credits

Created by FossilBacon

Built with: Python, PySide6 (Qt for Python)
