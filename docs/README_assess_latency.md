# Web Application Latency Assessment Tool

![Header Image](header-image.jpg)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Command-Line Options](#command-line-options)
- [Examples](#examples)
- [Output](#output)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Web Application Latency Assessment Tool is a Python script designed to assess and monitor the response latency of a web application. It achieves this by repeatedly sending GET requests to a user-specified URL, measuring response times, and generating metrics and feedback to facilitate an in-depth evaluation of the quality of communication with the target web application.

This tool is invaluable for web application administrators, developers, and quality assurance teams looking to maintain optimal performance, identify response time anomalies, and assess the consistency of response times.

## Features

- Automated GET request submission to a designated URL.
- Precise measurement and recording of response times.
- Calculation of the mean (average) response time.
- Evaluation of response time consistency using the standard deviation.
- Customization of assessment parameters, such as accuracy and thresholds.
- Informative output and optional alerts for deviations from anticipated response times.
- Command-line functionality for seamless integration into scripts and workflows.

## Requirements

- Python 3.12 or later
- Mandatory Python packages are specified in `requirements.txt`.
- Internet access to reach the target URL.

## Installation

1. Clone this repository to your local system:

   ```bash
   git clone https://github.com/yourusername/web-app-latency-assessment.git
   cd web-app-latency-assessment
   ```

2. Employ `pip` to install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

The Web Application Latency Assessment Tool is primarily a command-line utility. Follow these instructions to execute it:

```bash
python3.12 -m assess_latency <URL> [OPTIONS]
```

Replace `<URL>` with the URL of the web application you want to assess.

### Command-Line Options

- `-a, --accuracy <N>`: The number of GET requests to send for analysis (default: 10).
- `-t, --threshold <T>`: The threshold for categorizing response times as normal (default: 0.2).
- `-d, --std-deviation-threshold <T>`: The threshold for standard deviation used to evaluate response time consistency (default: 0.1).
- `-v, --verbose`: Activate verbose mode for comprehensive output (optional).

### Examples

1. Conduct a latency assessment on "https://example.com" with default settings:

   ```bash
   python3.12 -m assess_latency -u https://example.com
   ```

2. Specify the number of requests and customize threshold values:

   ```bash
   python3.12 -m assess_latency -u https://example.com -a 20 -t 0.3
   ```

3. Enable verbose mode to receive detailed output:

   ```bash
   python3.12 -m assess_latency -u https://example.com -v
   ```

## Output

The tool provides informative output and feedback regarding the assessed web application's response times and consistency. The output includes:

- Average response time
- Threshold values for defining normal response times
- Standard deviation and the threshold for assessing response time consistency
- Messages indicating the status of response times (normal or slow)

Here's an illustrative example of typical output:

```plaintext
[+] The values are relatively consistent.

Max Value | Min Value | Standard Deviation | Current Deviation Threshold Value
1.234     | 0.987     | 0.079               | 0.1
```

## Contributing

Contributions to this project are highly encouraged. If you have suggestions for improvements, bug fixes, or new features, please create an issue or submit a pull request.

## License

This project is licensed under the MIT License. Refer to the [LICENSE](../LICENSE.md) file for detailed license information.

---

Feel free to tailor this README.md to align with your project's unique details and prerequisites. Additionally, you may include supplementary sections or information as required.