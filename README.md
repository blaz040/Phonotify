# Phonotify

  This is source code for PC's side of Phonotify. The [android's side of Phonotify](https://github.com/blaz040/Phonotify_android) is needed to work. 

## Installation

### Windows (don't know if it still works)
  1. Download git in desired folder.
  2. Set up the current path -> in ``phoneNotificator.py`` on ``line 10`` change the ``current_folder_path`` to the current ``folder path``.
  3. run ``pip install -r requirements.txt``
  4. Run ``Compiler.bat``.
#### Run on startup 
  To run on startup make a shortcut of ``Phonotify.exe`` file and move it into the ``shell:startup`` folder
After running ``Compiler.bat``, there should be ``build`` and ``dist`` folder. Move into the ``dist`` folder and there should be ``Phonotify.exe``

### Linux 
  1. Download git and then run service_install.sh. This will build phonotify into a user service. 
  
