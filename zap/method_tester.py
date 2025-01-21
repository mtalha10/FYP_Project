# method_tester.py
import streamlit as st
import requests
import time
import concurrent.futures
import logging
from requests.exceptions import RequestException, Timeout, ConnectionError
from urllib.parse import urlparse
import csv
import io
from tenacity import retry, wait_fixed

# Set up logging for debugging
logging.basicConfig(filename="http_method_tests.log", level=logging.INFO)

# List of HTTP methods to test
http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Function to validate URL
def is_valid_url(url):
    """Check if the URL is valid."""
    parsed = urlparse(url)
    return bool(parsed.scheme) and bool(parsed.netloc)

# Function to explain status codes in detail
def get_status_code_description(status_code):
    """Returns a description for the HTTP status code."""
    status_codes = {
        200: "OK - The request was successful and the server returned the requested resource.",
        201: "Created - The resource was successfully created. Typically used in POST requests.",
        204: "No Content - The server successfully processed the request, but there's no content to return.",
        400: "Bad Request - The request was malformed or missing required parameters.",
        401: "Unauthorized - Authentication is required and has failed or was not provided.",
        403: "Forbidden - The server understands the request, but it refuses to authorize it.",
        404: "Not Found - The requested resource could not be found.",
        405: "Method Not Allowed - The HTTP method used is not supported for this resource.",
        500: "Internal Server Error - A server-side error occurred while processing the request.",
        502: "Bad Gateway - The server received an invalid response from an upstream server.",
        503: "Service Unavailable - The server is temporarily unavailable, usually due to overloading or maintenance.",
        504: "Gateway Timeout - The server did not receive a timely response from an upstream server."
    }
    return status_codes.get(status_code, "Unknown Status Code")

# Function to perform the HTTP request and return detailed results
@retry(wait=wait_fixed(2))
def test_http_method(method, url, custom_headers, timeout):
    """Perform the HTTP request and return detailed results."""
    try:
        # Parse custom headers if available
        headers = {}
        if custom_headers:
            try:
                headers = eval(custom_headers)  # Convert JSON-like string to dict
            except:
                st.error("❌ Invalid custom headers format. Ensure it's valid JSON.")
                return None

        # Record start time for response time calculation
        start_time = time.time()

        # Send the HTTP request
        response = requests.request(method, url, headers=headers, timeout=timeout)

        # Calculate the response time
        response_time = round(time.time() - start_time, 3)

        # Extract status code description and headers
        status_code_desc = get_status_code_description(response.status_code)
        headers = response.headers
        body = response.text if len(response.text) < 500 else f"Body too long to display ({len(response.text)} characters)"

        return {
            'method': method,
            'status_code': response.status_code,
            'status_desc': status_code_desc,
            'response_time': response_time,
            'headers': headers,
            'body': body
        }
    except Timeout:
        return {"method": method, "error": "The request timed out."}
    except ConnectionError:
        return {"method": method, "error": "Connection Error"}
    except RequestException as e:
        return {"method": method, "error": f"Request failed: {str(e)}"}

# Function to save results as CSV to a memory stream
def save_results_as_csv(results):
    """Save the HTTP method test results as a CSV file in memory."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
    output.seek(0)  # Go back to the start of the StringIO object
    return output

def http_method_tester():
    """Function to test HTTP methods, integrated into the app."""
    # Title of the app
    st.title("Advanced HTTP Method Tester")

    # Description
    st.write(
        "This tool tests which HTTP methods (e.g., GET, POST, PUT, DELETE, PATCH, etc.) are allowed on a given endpoint. "
        "It provides detailed results, including response time, status code, headers, body content, and more."
    )

    # Input field for the URL
    url = st.text_input("Enter the URL to test:", placeholder="https://example.com/api")

    # Input fields for custom headers (optional)
    custom_headers = st.text_area("Custom Headers (optional, JSON format):", placeholder='{"User-Agent": "MyApp"}')

    # Input for timeout (in seconds)
    timeout = st.number_input("Set Timeout (seconds)", min_value=1, max_value=60, value=10)

    # Function to handle button click and test methods
    if st.button("Test HTTP Methods"):
        if url and is_valid_url(url):
            st.write(f"Testing HTTP methods for: {url}")
            st.write("---")

            results = []
            # Use ThreadPoolExecutor to make requests in parallel
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for result in executor.map(lambda method: test_http_method(method, url, custom_headers, timeout), http_methods):
                    if result:
                        results.append(result)

            # Display results in a more structured and detailed format
            for result in results:
                with st.expander(f"Method: {result['method']}"):
                    if "error" in result:
                        st.error(f"❌ {result['method']} failed: {result['error']}")
                        logging.error(f"{result['method']} failed: {result['error']}")
                    else:
                        st.write(f"*Status Code*: {result['status_code']} - {result['status_desc']}")
                        st.write(f"*Response Time*: {result['response_time']} seconds")
                        st.write(f"*Response Headers*: {result['headers']}")
                        st.write(f"*Response Body*: {result['body']}")

                        # Detailed result based on status code
                        if result['status_code'] == 200:
                            st.success(f"✅ {result['method']} is allowed (Status Code: {result['status_code']})")
                            logging.info(f"{result['method']} is allowed (Status Code: {result['status_code']})")
                        elif result['status_code'] == 405:
                            st.warning(f"⚠ {result['method']} is *not allowed* on this endpoint (Status Code: {result['status_code']})")
                            logging.warning(f"{result['method']} is not allowed (Status Code: {result['status_code']})")
                        else:
                            st.warning(f"⚠ {result['method']} returned status code: {result['status_code']}")
                            logging.warning(f"{result['method']} returned status code: {result['status_code']}")

            # Save the results to a CSV file in memory and provide download
            st.write("---")
            st.subheader("Download Results")
            csv_output = save_results_as_csv(results)
            st.download_button(
                label="Download CSV Report",
                data=csv_output.getvalue(),
                file_name="http_method_results.csv",
                mime="text/csv"
            )

        else:
            st.error("Please enter a valid URL.")

