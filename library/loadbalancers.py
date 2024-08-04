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

def get_load_balancer_costs(load_balancer_type, region):
    """
    Fetch the cost per hour and data transfer cost per GB from the AWS Pricing API for the given load balancer type.
    """
    client = boto3.client('pricing', region_name='us-east-1')
    location = REGION_NAME_MAPPING.get(region, None)
    if not location:
        print(f"No location mapping found for region {region}")
        return 0.0, 0.0

    product_family = 'Load Balancer' if load_balancer_type in ['application', 'network'] else 'Load Balancer Usage'
    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': product_family},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
        {'Type': 'TERM_MATCH', 'Field': 'usagetype', 'Value': f'AWS-{load_balancer_type.title()}-Usage'}
    ]

    try:
        response = client.get_products(ServiceCode='AmazonEC2', Filters=filters)
        price_list = response['PriceList']

        if not price_list:
            print(f"No pricing data found for {load_balancer_type} load balancer in {location}")
            raise ValueError("No pricing data found")

        price_item = json.loads(price_list[0])
        terms = price_item['terms']['OnDemand']
        hourly_cost = 0.0
        data_transfer_cost = 0.0
        for term in terms.values():
            price_dimensions = term['priceDimensions']
            for dimension in price_dimensions.values():
                if dimension['unit'] == 'Hrs':
                    hourly_cost = float(dimension['pricePerUnit']['USD'])
                elif dimension['unit'] == 'GB':
                    data_transfer_cost = float(dimension['pricePerUnit']['USD'])
        return hourly_cost, data_transfer_cost
    except Exception as e:
        print(f"Error fetching price for {load_balancer_type} load balancer in {location}: {e}")
        # Fallback to default pricing if available
        default_pricing = {
            'network': {'hourly': 0.0225, 'data_transfer': 0.01},  # Example default values for NLB
            'application': {'hourly': 0.025, 'data_transfer': 0.008}  # Example default values for ALB
        }
        return default_pricing.get(load_balancer_type, {'hourly': 0.0, 'data_transfer': 0.0}).values()

def get_data_transfer_metrics(load_balancer_arn, region):
    """
    Retrieves the total data transfer out in GB for the last 30 days for a specific load balancer.
    """
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)

    namespace = 'AWS/ApplicationELB' if 'app/' in load_balancer_arn else 'AWS/NetworkELB'
    metrics = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName='ProcessedBytes',
        Dimensions=[
            {'Name': 'LoadBalancer', 'Value': load_balancer_arn.split('/')[1]},
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600 * 24,  # Daily statistics
        Statistics=['Sum']
    )

    total_bytes = sum(dp['Sum'] for dp in metrics['Datapoints'])
    total_gb = total_bytes / (1024 ** 3)  # Convert bytes to GB
    return total_gb

def list_load_balancers():
    session = boto3.Session(region_name='us-east-1')
    elbv2 = session.client('elbv2')

    regions = session.client('ec2').describe_regions()['Regions']
    total_load_balancers = 0
    total_cost = 0.0

    for region in regions:
        region_name = region['RegionName']
        print(f"Checking Load Balancers in region: {region_name}")

        elbv2_region = session.client('elbv2', region_name=region_name)
        try:
            lbs = elbv2_region.describe_load_balancers()
        except Exception as e:
            print(f"Error retrieving Load Balancers in region {region_name}: {e}")
            continue

        for lb in lbs['LoadBalancers']:
            lb_arn = lb['LoadBalancerArn']
            lb_type = lb['Type'].lower()
            lb_name = lb['LoadBalancerName']

            hourly_cost, data_transfer_cost_per_gb = get_load_balancer_costs(lb_type, region_name)

            if hourly_cost == 0.0 and data_transfer_cost_per_gb == 0.0:
                print(f"No pricing data available for {lb_type} load balancer in {region_name}")
                continue

            # Get data transfer out in GB for the last 30 days
            data_out_gb = get_data_transfer_metrics(lb_arn, region_name)
            data_transfer_cost = data_transfer_cost_per_gb * data_out_gb
            total_lb_cost = (hourly_cost * 720) + data_transfer_cost  # Assuming 720 hours per month
            total_cost += total_lb_cost

            total_load_balancers += 1

            print(f"Load Balancer Name: {lb_name}")
            print(f"Type: {lb_type.title()}")
            print(f"Estimated Data Transfer (last 30 days): {data_out_gb:.2f} GB")
            print(f"Estimated Data Transfer Cost: {data_transfer_cost:.2f} USD")
            print(f"Estimated Total Cost: {total_lb_cost:.2f} USD")
            print("")

    print(f"Total Load Balancers across all regions: {total_load_balancers}")
    print(f"Total estimated cost for all Load Balancers: {total_cost:.2f} USD")
    return f"{total_cost:.2f}"
