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

### Windows (recommended installer)
If you prefer an installer script that sets up a virtual environment, installs dependencies and registers the app to run at login, use the provided PowerShell script:

1. Open PowerShell in this project folder.
2. Run (may require running PowerShell as Administrator for highest privileges):

``powershell
powershell -ExecutionPolicy Bypass -File .\service_install_windows.ps1 -Action install
``

3. To remove the scheduled task and wrapper run:

``powershell
powershell -ExecutionPolicy Bypass -File .\service_install_windows.ps1 -Action uninstall
``

### Building a native Windows installer (Inno Setup)
If you want a distributable native installer (.exe) that packages the app as a single executable, follow these steps on Windows:

1. Ensure you have Python and Inno Setup installed.
2. From the project root run the build helper (creates venv, installs deps, and builds the exe):

```
build_windows.bat
```

3. This produces `dist\Phonotify.exe`. Compile the installer using Inno Setup Compiler (open `installer\Phonotify_installer.iss` in Inno or run `ISCC.exe installer\Phonotify_installer.iss`).

Notes:
- `build_windows.bat` uses PyInstaller with `--onefile` and includes the `icons` folder. Adjust `--add-data` if you add more resource folders.
- The generated installer creates Start Menu and optional Startup shortcuts and runs the app after install.

### Linux 
  1. Download git and then run service_install.sh. This will build phonotify into a user service. 
  
