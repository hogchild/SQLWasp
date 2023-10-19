# URL Checker

URL Checker is a Python script designed to validate URLs and perform HEAD or GET requests to check the target host's status. This tool is useful for ensuring the validity of URLs and verifying the availability of web resources.

## Features

- Validate URLs to ensure they have the correct format.
- Send HEAD requests to check the target host's status.
- Optionally, send GET requests in place of HEAD requests for more detailed checks.
- Generate output reports including validation results and request status.

## Usage

### Prerequisites

Make sure you have Python 3.12 installed. You can install it from the official Python website: [Python Downloads](https://www.python.org/downloads/).

### Installation

1. Clone this repository to your local machine.
```zsh
git clone https://github.com/your-username/url-checker.git
```
```zsh
cd url-checker
````
2. Install the required dependencies using pip.

```zsh
pip install -r requirements.txt
```

### Running the Script

To use URL Checker, open your terminal and navigate to the project directory containing `url_checker.py`. You can use the following command-line options:

- `urls`: You can pass URLs as positional arguments, e.g., `python url_checker.py example.com google.com`.
- `-l` or `--url-list`: Pass a list of URLs in JSON format, e.g., `python url_checker.py -l '["example.com", "google.com"]'`.
- `-o` or `--outfile`: Use this option to write the output to a CSV file.
- `-v` or `--validate-url`: Use this option to perform URL format validation without sending requests.
- `-g` or `--send-get`: Use this option to send GET requests instead of HEAD requests.

Here are some examples of how to use the script:

- Perform URL format validation and output results:

```zsh
  python url_checker.py -v -l '["example.com", "invalid_url"]'
```

- Send HEAD requests to validate URLs and check the target host's status, then save the results to a CSV file:
```zsh
python url_checker.py -l '["example.com", "google.com"]' -o
```

- Send GET requests to URLs and save the results to a CSV file:
```zsh
python url_checker.py -l '["example.com", "google.com"]' -o -g
```

### Output

The script will generate an output report with validation results, response statuses, and descriptions for checked URLs. The report can be displayed in the terminal or saved to a CSV file, depending on your chosen options.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

- [hogchild](https://github.com/hogchild)

Feel free to contribute, report issues, or submit feature requests. Enjoy using URL Checker!
