# Freedom Website Blocker Session Start Script

This script automates the process of setting up a blocking session on the Freedom platform using Selenium WebDriver. The script allows you to configure the blocklists, devices, and session duration, and then optionally start the session immediately.

## Features

- **Automated Login**: Logs into the Freedom platform using credentials stored in an environment file.
- **Blocklist Selection**: Allows you to select the blocklists you want to apply during the session.
- **Device Selection**: Allows you to select the devices that will be affected by the block session.
- **Session Duration**: Configure the length of the blocking session.
- **Configuration Persistence**: Saves your selected blocklists, devices, and duration to a configuration file (`config.json`) for easy reuse.
- **Immediate Session Start**: Option to start the session immediately after configuration.

## Prerequisites

- Python 3.x
- Selenium
- WebDriver Manager
- A Freedom account

## Setup

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Booza1981/StartFreedomSession.git
    cd StartFreedomSession
    ```

2. **Set up a virtual environment**:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Create a `.env` file** in the project root and add your Freedom credentials:
    ```plaintext
    USERNAME=your_email@example.com
    PASSWORD=your_password
    ```

## Usage

### Initial Configuration and Running

To configure the blocklists, devices, and duration, and optionally start the session immediately:

```bash
python run_freedom_block.py --reconfigure
