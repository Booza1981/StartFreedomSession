# StartFreedomSession

A Python script to automate launching Freedom sessions through Selenium. Ideal for quick starts, integration into other workflows, or scheduled tasks. Runs headless by default.

## Overview

This script allows you to automate the process of starting Freedom sessions using Selenium WebDriver. It supports both local ChromeDriver and remote Selenium Grid setups, making it flexible for different environments.

## Features

- Configure and save your blocklists and devices
- Start Freedom sessions with saved configurations
- Adjust session duration without reconfiguring blocklists and devices
- Flexible WebDriver configuration (local or remote)
- Detailed logging
- Multiple fallback strategies for Chrome binary detection

## Requirements

- Python 3.6+
- Selenium 4.0.0+
- A Freedom.to account
- Google Chrome (for local execution) - See [WebDriver Notes](#webdriver-notes) section below for details on local Chrome or remote Selenium Grid setup

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/Booza1981/StartFreedomSession.git
   cd StartFreedomSession
   ```

2. Create a virtual environment and install the requirements:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Freedom credentials:
   ```
   FREEDOM_USERNAME=your_email@example.com
   FREEDOM_PASSWORD=your_password
   ```

## Configuration

The script uses two configuration files:

1. `.freedom_settings.json` - Contains WebDriver and logging settings
   - Created automatically with defaults when not present
   - Example files are provided:
     - `freedom_settings.example.json` - Detailed explanations for all settings
     - `freedom_settings.local.example.json` - Example for local Chrome setup
     - `freedom_settings.remote.example.json` - Example for Selenium Grid setup
   
   To use an example file:
   ```bash
   # Copy the appropriate example file to your home directory
   cp freedom_settings.remote.example.json ~/.freedom_settings.json
   
   # Or specify it directly when running the script
   python trigger_freedom_session.py --settings freedom_settings.remote.example.json
   ```

2. `freedom_config.json` - Contains your selected blocklists, devices, and duration
   - Created when you run the script with `--reconfigure`

## Usage

### First-time setup / Reconfigure

Run the script with the `--reconfigure` flag to select your blocklists, devices, and duration:

```
python trigger_freedom_session.py --reconfigure
```

This will:
1. Open a browser session to Freedom.to
2. Let you select which blocklists to use
3. Let you select which devices to include
4. Set the session duration
5. Save your configuration

### Starting a session

After configuration, simply run:

```
python trigger_freedom_session.py
```

This will start a Freedom session using your saved configuration.

### Adjusting session duration

To change just the duration without reconfiguring blocklists and devices:

```
python trigger_freedom_session.py --adjust-time 30
```

This sets the session duration to 30 minutes.

### Using a Custom Settings File

If you want to use a different settings file than the default `.freedom_settings.json` in the script directory:
```
python trigger_freedom_session.py --settings /path/to/your/custom_settings.json
```

## Using with Selenium Grid

If you want to use a remote Selenium Grid instead of a local browser:

1. Edit your `.freedom_settings.json`:
   ```json
   {
     "driver_type": "remote",
     "remote_url": "http://your-selenium-grid-ip:4444/wd/hub"
   }
   ```

2. Run the script normally:
   ```
   python trigger_freedom_session.py
   ```

## Logging & Troubleshooting

* **Log File:** Detailed information about the script's execution, including steps, selections, and errors, is logged to `logs/freedom_script.log` within the project directory. Check this file first if you encounter issues.
* **Error Screenshots:** If the script fails during login or encounters a critical error later, it will attempt to save a screenshot to the `logs/` directory (e.g., `login_error_YYYYMMDD_HHMMSS.png`, `final_error_...`). These can help diagnose problems.
* **Common Issues:**
    * **Login Failed:** Double-check credentials in your `.env` file. Ensure Freedom.to is accessible. Check the log file and any screenshots.
    * **WebDriver Errors:** See the [WebDriver Notes](#webdriver-notes) below. Ensure Chrome/ChromeDriver or your Selenium Grid is set up correctly.
    * **Element Not Found / Click Intercepted:** Freedom.to website structure might have changed. This could require updating the Selenium selectors (e.g., `By.ID`, `By.CLASS_NAME`, `By.XPATH`) within the `trigger_freedom_session.py` script. Check the log file for details.


## WebDriver Notes

The script uses Selenium to control a web browser. Configuration is via `.freedom_settings.json`.

* **Local Driver (`driver_type: "local"`):**
    * Requires Google Chrome to be installed on the machine running the script.
    * The script attempts to automatically download and manage the correct `chromedriver` using Selenium's built-in *Selenium Manager* or the `webdriver-manager` library (if installed).
    * If automatic management fails (e.g., due to network restrictions or permissions), you may need to:
        1.  Download the `chromedriver` executable matching your installed Chrome version from the [official ChromeDriver website](https://chromedriver.chromium.org/downloads).
        2.  Place the executable somewhere the script can find it (e.g., in the script directory or a location listed in your system's `PATH` environment variable).
        3.  Alternatively, you can specify the full path to your *Google Chrome* executable (not chromedriver) using the `chrome_binary_path` setting in `.freedom_settings.json` if Selenium has trouble finding it.

* **Remote Driver (`driver_type: "remote"`):**
    * Requires a separate Selenium Grid, Selenoid, or other WebDriver-compatible server running.
    * Set `driver_type` to `"remote"` and `remote_url` to the correct endpoint (e.g., `"http://your-grid-ip:4444/wd/hub"`) in `.freedom_settings.json`.
    * The remote server/node must have Google Chrome available for the script to use.



## License

[MIT](LICENSE)
