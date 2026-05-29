# Creative Studio

Version 1.0 | A powerful project management system for organizing content with custom fields, media attachments, and internal linking.

License: MIT | Windows 10/11

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

## System Requirements

- Windows 10 or Windows 11
- 64-bit processor
- 4GB RAM minimum (8GB recommended)
- 100MB free disk space
- Internet connection (for auto-update feature)

## Installation

Download and Install:

1. Download CreativeStudio_Setup.exe from the latest release
2. Run the installer
3. Follow the on-screen instructions
4. Launch Creative Studio from the Start Menu or Desktop shortcut

Portable Version:

1. Download CreativeStudio_Portable.zip
2. Extract to any folder
3. Run CreativeStudio.exe

First Launch:
- The first launch will prompt you to create or open a project
- Default project location: Documents\CreativeStudio\Projects

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

## File Locations

Installation: C:\Program Files\Creative Studio\
User Data: %USERPROFILE%\Documents\CreativeStudio\
Settings: %APPDATA%\CreativeStudio\settings.ini

Project Structure:

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

Note: Administrator privileges may be required for auto-update if installed in Program Files.

## Keyboard Shortcuts

Save All: Ctrl+S
New Page: Ctrl+N
Search: Ctrl+F

## Uninstallation

Control Panel:
1. Open Windows Control Panel
2. Go to Programs and Features
3. Select Creative Studio
4. Click Uninstall

Using Uninstaller:
1. Start Menu -> Creative Studio -> Uninstall Creative Studio
2. Or run Uninstall.exe in the installation folder

Note: Uninstallation will not delete your projects. You can manually delete them from Documents\CreativeStudio\Projects if desired.

## Troubleshooting

Application Won't Start:
- Verify Windows is up to date
- Reinstall the application
- Check Windows Event Viewer for errors

Update Fails to Download:
- Check your internet connection
- Run as Administrator
- Temporarily disable antivirus software
- Download the latest installer manually from GitHub

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

Projects Not Saving:
- Ensure you have write permissions to Documents folder
- Check disk space
- Run as Administrator

## Known Issues

Version 1.0:
- None reported

## License

MIT License - See LICENSE.txt in installation folder

## Credits

Created by [Your Name]

Built with:
- Python 3.8+
- PySide6 (Qt for Python)
- PyInstaller (for EXE packaging)

## Version History

Version 1.0 (Current - Initial Release):
- Multi-Project Management
- Custom Categories with dynamic fields
- Rich Text Editor with internal linking
- Media attachments (images, audio, 3D models)
- Dark & Light themes
- Adjustable font size
- Auto-save functionality
- Search pages
- Recent projects list
- Settings dialog

## Roadmap

Planned features for future versions:

Version 1.1:
- Export/Import projects
- PDF export of pages
- Backup and restore

Version 1.2:
- Tag system for pages
- Full-text search across all content
- Plugin system

Version 1.3:
- Cloud sync support
- Team collaboration
- Version history for pages

## Support

- Report issues on GitHub Issues
- Feature requests welcome
- Include version number and Windows version in bug reports

## System Administrator Notes

Silent Installation (for IT deployment):
CreativeStudio_Setup.exe /verysilent /suppressmsgboxes /norun

Registry Keys:
HKEY_CURRENT_USER\Software\Creative Studio

Command Line Arguments:
--reset-settings    Reset all settings to defaults
--project "path"    Open specific project on launch

## Disclaimer

This software is provided "as is" without warranty of any kind. Always backup your projects before updating. The authors are not responsible for data loss.
