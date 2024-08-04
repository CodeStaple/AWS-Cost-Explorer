# AWS Cost Explorer
This repository contains Python scripts for calculating and retrieving costs associated with various AWS services, including EC2 instances, Elastic IPs, NAT Gateways, and more. The scripts utilize the AWS Pricing API and AWS SDK for Python (Boto3) to fetch and calculate costs based on the current AWS infrastructure.

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [Scripts](#scripts)
  - [Instances](#instances)
  - [Elastic IPs](#elastic-ips)
  - [NAT Gateways](#nat-gateways)
  - [Internet Gateways](#internet-gateways)
  - [Load Balancers](#load-balancers)
- [Contributing](#contributing)
- [License](#license)

### Clone the repository:
```
git clone https://github.com/CodeStaple/aws-cost-explorer.git
cd aws-cost-explorer
```

### Create a virtual environment and activate it:
```
python3 -m venv venv
source venv/bin/activate # On Windows use venv\Scripts\activate
```

### Install the required packages:
```
pip install -r requirements.txt
```

### Setup
Set up your AWS credentials. You can use the AWS CLI to configure your credentials:
```
aws configure
```
Alternatively, set the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.

### Usage
Each script can be run independently to calculate or retrieve specific AWS service costs.

### Running a Script
For example, to run the script for calculating Elastic IP costs:

python pricing_api.py

# Scripts
## Instances
instances.py - This script calculates the total cost of running EC2 instances across all AWS regions. It fetches instance types and calculates the monthly cost based on the hourly rates.

## Elastic IPs
elastic_ips.py - This script retrieves the hourly cost of Elastic IPs across all AWS regions. It excludes special cases like Carrier IPs and focuses on general pricing.

## NAT Gateways
nat_gateways.py - This script calculates the total cost associated with NAT Gateways. It includes both the hourly cost and data transfer costs.

## Internet Gateways
internet_gateways.py - Calculates the cost associated with Internet Gateways, including data transfer costs for the last 30 days.

## Load Balancers
load_balancers.py - This script fetches the cost data for different types of AWS Load Balancers, such as Application Load Balancers (ALB) and Network Load Balancers (NLB).

# Contributing
Contributions are welcome! Please fork this repository and submit a pull request with your changes.

# License
This project is licensed under the MIT License. See the LICENSE file for details.