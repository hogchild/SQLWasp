# Cookie Injector Core

## Overview

The "cookie_injector_core.py" script is a tool for educational or security testing purposes. It is designed to demonstrate a blind SQL injection attack against a web application that uses tracking cookies. The script injects malicious SQL code into a tracking cookie and sends HTTP requests to the target web application to detect vulnerabilities.

## Dependencies

To run this script, you need to have the following dependencies installed:

- Python 3.12 or higher
- The `requests` library for making HTTP requests
- The `rich` library for improved console output
- Custom modules, including `SQLWasp.custom_errors`, `SQLWasp.reverse_logger`, and `SQLWasp.reverse_logger.filename_parser`

You can install these dependencies using Python package managers like pip.

```bash
pip install requests rich
```

## Usage

1. Clone or download this repository to your local machine.

2. Open a terminal or command prompt and navigate to the directory containing "cookie_injector_core.py."

3. Run the script using Python 3.12 or a compatible version:

```bash
python3.12 cookie_injector_core.py
```

4. The script will execute the blind SQL injection attack against the target URL specified within the code.

5. The attack results, including any discovered characters or errors, will be displayed in the console.

## Configuration

Before running the script, you may need to modify certain constants within the script:

- `url`: Update this variable to the target URL you want to test.
- `code`: Modify this variable to contain the SQL injection code you want to inject.
- `payload_char`: Change this variable to specify the payload character for the injection.
- `confirm_bytes`: Set this variable to match the confirmation string you expect in the response.

Please ensure that you are using this tool in an authorized and ethical manner. Unauthorized use of this script against websites or systems you do not own or have permission to test is illegal and unethical.

## Disclaimer

This script is provided for educational and security testing purposes only. It should only be used against websites or systems for which you have explicit permission to test. Unauthorized use of this tool may result in legal consequences.

## License

This script is provided under the MIT License. Please see the "LICENSE" file for details.

## Author

[Your Name](https://github.com/hogchild)

## Contact

For questions or feedback, please contact [Your Email Address].
```

You can copy and paste this code into your `readme.md` file. Remember to replace `[Your Name]` and `[Your Email Address]` with the appropriate information.