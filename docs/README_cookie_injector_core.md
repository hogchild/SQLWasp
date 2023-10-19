# Cookie Injector Core

## Documentation

### Purpose

The "cookie_injector_core.py" script is designed for educational or security testing purposes. It demonstrates a blind SQL injection attack against a web application that uses tracking cookies. The script injects malicious SQL code into a tracking cookie, sends HTTP requests to the target web application, and checks for specific confirmation strings in the response. This tool is intended for educational purposes or security testing in authorized environments.

### Dependencies

To run this script, you must have the following dependencies installed:

- Python 3.12 or higher
- The `requests` library for making HTTP requests
- The `rich` library for enhanced console output
- Custom modules: `SQLWasp.custom_errors`, `SQLWasp.reverse_logger`, `SQLWasp.reverse_logger.filename_parser`

You can install these dependencies using the following command:

```bash
  pip install requests rich
```

### Usage

1. Clone or download this repository to your local machine.

2. Open a terminal or command prompt and navigate to the directory containing "cookie_injector_core.py."

3. Run the script using Python 3.12 or a compatible version:

   ```bash
   python3.12 cookie_injector_core.py
   ```

4. The script will execute the blind SQL injection attack against the target URL specified within the code.

5. The attack results, including any discovered characters or errors, will be displayed in the console.

### Configuration

Before running the script, you may need to modify certain constants within the script:

- `url`: Update this variable to the target URL you want to test.
- `code`: Modify this variable to contain the SQL injection code you want to inject.
- `payload_char`: Change this variable to specify the payload character for the injection.
- `confirm_bytes`: Set this variable to match the confirmation string you expect in the response.
- `cookiename`: Adjust this variable to match the name of the cookie you want to inject.

### Examples

Here are some examples of how to use the script with different configurations:

1. Basic Usage:

   ```python
   url = "https://example.com/target-url"
   code = "' OR 1=1--"
   payload_char = "a"
   confirm_bytes = b"Welcome"
   cookiename = "sessionID"
   ```
   
   Run from command line:

   ```zsh   
   python3.12 cookie_injector_core.py
   ```

2. Custom Configuration:

   ```python
   url = "https://example.com/login"
   code = "' UNION SELECT username, password FROM users WHERE username='admin'--"
   payload_char = "b"
   confirm_bytes = b"Login Successful"
   cookiename = "tracking_cookie"
   ```

   Run from command line:

   ```zsh
   python3.12 cookie_injector_core.py
   ```

### Disclaimer

This script is provided for educational and security testing purposes only. It should only be used against websites or systems for which you have explicit permission to test. Unauthorized use of this tool may result in legal consequences.

### License

This script is provided under the MIT License. Please see the "LICENSE" file for details.

### Author

[Your Name]

### Contact

For questions or feedback, please contact [Your Email Address].

## Author

[Your Name]

## Contact

For questions or feedback, please contact [Your Email Address].
```

This updated `readme.md` includes example usage scenarios to help users understand how to configure and run the script for different testing purposes.