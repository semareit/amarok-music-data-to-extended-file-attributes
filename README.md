# amarok-music-player-to-extended-file-attributes-script

## Purpose

- Get the Rating and Label information from Amarok Music Player database and add them as Extended File Attribute to the related files so that they are displayed in Dolpin File Browser.

## Pre-Requisites

- install required packages:

   ```bash
   # APT package bases systems as e.g. GNU/Linux Debian/Ubuntu
   apt install attr xattr python3 python3-pip python3-xattr python3-mysql.connector
   ```

## Analysis

1. **Amarok database structure:**

   - table `urls` contain the basic information as `deviceid`, `rpath` and `directory`
   - table `statistics` contain the Rating
   - table `urls_labels` links URLs with labels
   - table `labels` contain the label-texts

2. **Dolphin xattr-Attributes:**

   - `user.baloo.rating` is used for Rating
   - `user.xdg.tags` is used for Tags

## Features

- **Flexible Input**: allow user defined input of amarok database parameter
- **Flexible Output**: allow user defined output file name
- **MySQL-Connection**: connect to Amarok-database
- **Data-Extraction**: get filepaths, labels, rating
- **Optimized Query**:
  - filter only for entries with valid paths
  - using direct JOINs for better performance
  - remove the leading dot from `rpath`
  - concatenate `lastmountpoint` and the adjusted `rpath`
  - add a slash between `lastmountpoint` and the adjusted `rpath`
- **Auto Pathconversion**: convert `file://` URLs into local paths
- **Auto Escaping**: handle special characters of file paths
- **Sorted Labels**: labels are sorted alphabetic for consistent display
- **Errorhandling**:
  - robust Error-Handling
  - check that files exists
- **Logging**:
  - display host and port of successful connection
  - display progress and statistics
- **Simple Import**: use a single command to import content of output file into filesystem

## Usage

1. execute script `amarok_xattr_export.py` as following

   ```bash
   # Execution with default parameters and default Output
   python amarok_xattr_export.py

   # Execution with detailed Output information
   python amarok_xattr_export.py --verbose

   # Execution with user defined output file
   python amarok_xattr_export.py --output metadata.txt

   # Execution with user defined database settings
   python amarok_xattr_export.py --host localhost --port 3307 --user amarok --password amarok --database amarok

   # Execution with all availabe user defined settings
   python amarok_xattr_export.py --host localhost --port 3307 --user amarok --password amarok --database amarok --output metadata.txt --verbose
   ```

   > **Hint**
   > to simplify creation procedure you can create a helper file e.g. `amarok_xattr_export.sh` that contain the preferred execution command line.

2. wait until file with the extended file attributes information is created

   ```txt
   # file: /home/user/music/song1.mp3
   user.baloo.rating="8"
   user.xdg.tags="Rock,1999"

   # file: /home/user/music/song2.mp3
   user.baloo.rating="5"

   # file: /home/user/music/song3.mp3
   user.baloo.rating="10"
   user.xdg.tags="Jazz,Chillout,2010"
   ```

   *Listing: Example content of output file e.g. `metadata.txt`*

3. import the created file e.g. `metadata.txt` to apply all Rating- and Label-Information of Amarok as extended attributes at the music files

   ```bash
   # Import Metadata
   setfattr -h --restore=metadata.txt
   ```