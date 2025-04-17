# StartFreedomSession

A Python script to automate launching Freedom sessions through Selenium.

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
- Google Chrome (for local execution)

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
   - Example:
     ```json
     {
       "driver_type": "local",
       "remote_url": "http://localhost:4444/wd/hub",
       "chrome_binary_path": "",
       "browser_logging": false,
       "log_path": "~/freedom_script.log",
       "config_path": "~/freedom_config.json"
     }
     ```

2. `freedom_config.json` - Contains your selected blocklists, devices, and duration
   - Created when you run the script with `--reconfigure`

## Usage

### First-time setup

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

## Troubleshooting

### Cannot find Chrome binary

If you encounter the error "Cannot find Chrome binary", try the following solutions:

1. **Specify Chrome binary path in settings:**
   ```json
   {
     "chrome_binary_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
   }
   ```

2. **Use a Selenium Grid:** Set up a Docker-based Selenium Grid:
   ```yaml
   selenium-chrome-standalone:
     image: selenium/standalone-chrome:latest
     container_name: selenium-chrome-standalone
     restart: unless-stopped
     shm_size: 2gb
     ports:
       - "4446:4444"  # Bind to all interfaces
     volumes:
       - /dev/shm:/dev/shm
   ```

   Then update your settings to use it:
   ```json
   {
     "driver_type": "remote",
     "remote_url": "http://localhost:4446/wd/hub"
   }
   ```

### Chrome version mismatch

If you encounter errors about Chrome version mismatches:

1. Update your Chrome browser to the latest version
2. Ensure webdriver-manager is updated (`pip install --upgrade webdriver-manager`)
3. Try using Selenium's built-in driver manager by removing webdriver-manager

## License

[MIT](LICENSE)
