# Assess Latency Looper

**Assess Latency Looper** is a Python script designed for performing concurrent latency assessments on a list of URLs using the `AssessLatency` class. It sends simultaneous GET and ping requests to multiple URLs, calculates latency metrics, and provides detailed reports. Additionally, it utilizes a RandomForestClassifier to predict the communication quality with web applications based on latency data.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Command-line Options](#command-line-options)
- [Example](#example)
- [Results](#results)
- [License](#license)

## Overview

Assessing the latency of web applications is crucial for understanding their performance. This script allows you to assess the latency of a list of URLs concurrently. It sends a specified number of GET and ping requests to each URL, calculates latency metrics, and compares the results to threshold values. It also uses a machine learning model (RandomForestClassifier) to predict the communication quality with the web applications.

The script is organized as follows:
- A list of target URLs is provided.
- The script runs multiple instances of the `AssessLatency` class concurrently.
- The latency assessment results are collected, and a prediction of communication quality is made using machine learning.

## Prerequisites

To use this script, you need:

- Python 3.12
- Required Python libraries: `click`, `rich`, and others used in `assess_latency_looper.py`.
- A valid list of target URLs that you want to assess.

## Usage

1. Clone the repository or download the `assess_latency_looper.py` script to your local machine.

2. Install the required Python libraries if you haven't already. You can use `pip` for this:

   ```
   pip install click rich
   ```

3. Open a terminal and navigate to the directory where `assess_latency_looper.py` is located.

4. Run the script with the desired options and provide the list of URLs to assess. For example:

   ```
   python3.12 assess_latency_looper.py -u "https://example.com" "https://example2.com" "https://example3.com" ...
   ```

   You can customize the assessment parameters using the available command-line options (see [Command-line Options](#command-line-options)).

5. The script will perform concurrent latency assessments and display the results in your terminal. It will also create a CSV file with the assessment data.

## Command-line Options

- `-u`, `--urls`: A list of URLs to assess (required).
- `-a`, `--accuracy`: The number of requests (GET and ping) to send to each URL for analysis (default: 10).
- `-t`, `--threshold`: The acceptable latency threshold in seconds (+/-) for GET requests (default: 0.2 seconds).
- `-T`, `--ping-threshold`: The acceptable latency threshold in seconds (+/-) for ping requests (default: 0.2 seconds).
- `-x`, `--std-deviation-threshold`: The maximum allowed standard deviation for latency data (default: 0.3).
- `-y`, `--ping-std-deviation-threshold`: The maximum allowed standard deviation for ping latency data (default: 0.3).
- `-D`, `--delay`: The delay in seconds between requests (default: 0.3 seconds).
- `-o`, `--outfile`: The file path to save the assessment data as a CSV file (default: "data/output/assess_latency/assess_latency.csv").
- `-v`, `--verbose`: Enable extra verbosity for the assessment process (optional, no value required).
- `-m`, `--max-threads`: The maximum number of concurrent threads (between 2 and 12) for assessments (default: 12).

## Example

To assess a list of URLs with custom parameters, you can run the script as follows:

```bash
python3.12 assess_latency_looper.py -u "https://example.com" "https://example2.com" "https://example3.com" -a 15 -t 0.3 -T 0.4 -x 0.2 -y 0.1 -D 0.5 -o "custom_assessments.csv" -v -m 6
```

This command will assess three URLs with 15 requests per URL, custom thresholds, a different output file, verbose mode, and a maximum of 6 concurrent threads.

## Results

- The script will display detailed results in the terminal, including the assessment outcome and AI predictions.
- The assessment data will be saved in a CSV file specified by the `-o` option.
- The script will create CSV files in both "data/output/assess_latency/" and "data/input/ai/assess_latency/" for analysis and model prediction.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE.md) file for details.

## Author

- [hogchild](https://github.com/hogchild)

Feel free to customize this README.md according to your project's specific needs and include any additional information or usage examples that you find relevant.