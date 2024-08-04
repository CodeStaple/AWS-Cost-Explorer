import boto3
from datetime import datetime, timedelta
import json

# Mapping of AWS region codes to Pricing API locations
REGION_NAME_MAPPING = {
    'us-east-1': 'US East (N. Virginia)',
    'us-east-2': 'US East (Ohio)',
    'us-west-1': 'US West (N. California)',
    'us-west-2': 'US West (Oregon)',
    'ca-central-1': 'Canada (Central)',
    'eu-central-1': 'EU (Frankfurt)',
    'eu-west-1': 'EU (Ireland)',
    'eu-west-2': 'EU (London)',
    'eu-west-3': 'EU (Paris)',
    'eu-north-1': 'EU (Stockholm)',
    'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'ap-northeast-2': 'Asia Pacific (Seoul)',
    'ap-northeast-3': 'Asia Pacific (Osaka-Local)',
    'ap-southeast-1': 'Asia Pacific (Singapore)',
    'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-south-1': 'Asia Pacific (Mumbai)',
    'sa-east-1': 'South America (São Paulo)',
    # Add more mappings as needed
}

def is_default_vpc(vpc_id, region):
    """
    Check if the given VPC is a default VPC in the specified region.
    """
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_vpcs(VpcIds=[vpc_id])
    vpc = response['Vpcs'][0]
    return vpc.get('IsDefault', False)

def get_data_transfer_cost(region, data_out_gb):
    """
    Fetch the data transfer cost per GB from the AWS Pricing API.
    """
    client = boto3.client('pricing', region_name='us-east-1')
    location = REGION_NAME_MAPPING.get(region, None)
    if not location:
        print(f"No location mapping found for region {region}")
        return 0.0

    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Data Transfer'},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
        {'Type': 'TERM_MATCH', 'Field': 'usagetype', 'Value': 'AWS-Out-Bytes'}
    ]

    try:
        response = client.get_products(ServiceCode='AmazonEC2', Filters=filters)
        price_list = response['PriceList']

        if not price_list:
            print(f"No pricing data found for data transfer in {location}")
            return 0.0

        price_item = json.loads(price_list[0])
        terms = price_item['terms']['OnDemand']
        for term in terms.values():
            price_dimensions = term['priceDimensions']
            for dimension in price_dimensions.values():
                price_per_gb = float(dimension['pricePerUnit']['USD'])
                return price_per_gb * data_out_gb
    except Exception as e:
        print(f"Error fetching price for data transfer in {location}: {e}")
        return 0.0

def get_data_transfer_metrics(igw_id, region):
    """
    Retrieves the total data transfer out in GB for the last 30 days for a specific Internet Gateway.
    """
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)

    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/VPC',
        MetricName='BytesOutToDestination',
        Dimensions=[
            {'Name': 'InternetGatewayId', 'Value': igw_id},
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600 * 24,  # Daily statistics
        Statistics=['Sum']
    )

    total_bytes = sum(dp['Sum'] for dp in metrics['Datapoints'])
    total_gb = total_bytes / (1024 ** 3)  # Convert bytes to GB
    return total_gb

def list_internet_gateways():
    session = boto3.Session(region_name='us-east-1')
    ec2 = session.client('ec2')

    regions = ec2.describe_regions()['Regions']
    total_gateways = 0
    total_cost = 0.0

    for region in regions:
        region_name = region['RegionName']
        print(f"Checking Internet Gateways in region: {region_name}")

        ec2_region = session.client('ec2', region_name=region_name)
        try:
            igws = ec2_region.describe_internet_gateways()
        except Exception as e:
            print(f"Error retrieving Internet Gateways in region {region_name}: {e}")
            continue

        for igw in igws['InternetGateways']:
            igw_id = igw['InternetGatewayId']
            attached_vpcs = [attachment['VpcId'] for attachment in igw['Attachments']]

            # Exclude Internet Gateways associated with default VPCs
            if any(is_default_vpc(vpc_id, region_name) for vpc_id in attached_vpcs):
                print(f"Internet Gateway {igw_id} is associated with a default VPC and will be excluded from cost calculations.")
                continue

            # Exclude Internet Gateways with no attached VPCs
            if not attached_vpcs:
                print(f"Internet Gateway {igw_id} has no attached VPCs and will be excluded from cost calculations.")
                continue

            total_gateways += 1

            # Get data transfer out in GB for the last 30 days
            data_out_gb = get_data_transfer_metrics(igw_id, region_name)
            data_transfer_cost = get_data_transfer_cost(region_name, data_out_gb)
            total_cost += data_transfer_cost

            print(f"Internet Gateway ID: {igw_id}")
            print(f"Attached VPCs: {', '.join(attached_vpcs) if attached_vpcs else 'None'}")
            print(f"Estimated Data Transfer (last 30 days): {data_out_gb:.2f} GB")
            print(f"Estimated Data Transfer Cost: {data_transfer_cost:.2f} USD")
            print("")

    print(f"Total Internet Gateways across all regions: {total_gateways}")
    print(f"Total estimated cost for all Internet Gateways: {total_cost:.2f} USD")
    return f"{total_cost:.2f}"
