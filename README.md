# Cookie SQL Injection Vulnerability Scanner

**cookie_vuln_scanner.py** is a Python script that scans a web application's response to a GET request for cookies and automatically injects False and True SQL statements into those cookies. It supports the discovery of SQL Injection vulnerabilities using both Boolean-Based and Time-Based techniques.

## Table of Contents
- [Usage](#usage)
- [Features](#features)
- [Installation](#installation)
- [How it Works](#how-it-works)
- [Contributing](#contributing)
- [License](#license)

## Usage
To use the Cookie SQL Injection Vulnerability Scanner, run the script with the following command:
```bash
python cookie_vuln_scanner.py [OPTIONS] URL
```
- **URL**: The target web application URL to scan for SQL Injection vulnerabilities.
- **OPTIONS**:
  - `-v, --verbose`: Use this flag for verbose output.

## Features
- Scan web applications for SQL Injection vulnerabilities in cookies.
- Support for both Boolean-Based and Time-Based SQL Injection techniques.
- Generate payloads for different SQL injection attacks.
- Compare responses to detect SQL Injection vulnerabilities.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/hogchild/SQLWasp.git
   cd SQLWasp
   ```

2. Run the script with Python 3.12:
   ```bash
   python cookie_vuln_scanner.py [OPTIONS] URL
   ```

## How it Works
The Cookie SQL Injection Vulnerability Scanner works by performing the following steps:
1. Sends a GET request to the provided URL.
2. Extracts cookies from the response.
3. Injects False and True SQL statements into each cookie.
4. Compares the responses to detect SQL Injection vulnerabilities.
5. Provides verbose output to help with the analysis.

## Contributing
Contributions to this project are welcome. If you have suggestions, bug reports, or want to add new features, please open an issue or create a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.
```
