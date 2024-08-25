Description
This script automatically logs into your Freedom account and triggers a blocking session. It uses the default time configured in your dashboard, which you can change by logging in manually if needed.

Notes
Default Time Setting: The script triggers a session using the default time configured in your Freedom dashboard. You can modify this time by logging into the dashboard directly.

Element Selection: The script interacts with specific elements under the "Interacting with page elements" section, which are dependent on your account setup. These elements select the options under "Block these distractions:" and "On these devices:". The elements have been selected using Katalon Recorder, so you might need to adjust them based on your particular setup.

Setup Instructions
1. Clone the Repository
Clone this repository to your local machine:

bash
Copy code
```bash
git clone https://github.com/yourusername/freedom-blocking-session-automation.git
```
2. Set Up the Environment
This project uses environment variables to manage sensitive information like your Freedom username and password.

Create a .env file:

Copy the provided .env.example file to .env:
bash
Copy code
cp .env.example .env
Open the .env file and fill in your Freedom account credentials.
Install Dependencies:

Use pip to install the necessary Python packages:
bash
Copy code
pip install -r requirements.txt
3. Run the Script
To execute the script, use the following command:

```python freedom_headless_login.py
```
Dependencies
Selenium: Used to automate browser interactions.
webdriver-manager: Automatically manages the ChromeDriver installation.
python-dotenv: Loads environment variables from a .env file.
License
This project is licensed under the MIT License. See the LICENSE file for details.