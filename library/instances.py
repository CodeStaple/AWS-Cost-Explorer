import json
import boto3

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

def get_instance_cost(instance_type, region):
    client = boto3.client('pricing', region_name='us-east-1')

    location = REGION_NAME_MAPPING.get(region, None)
    if not location:
        print(f"No location mapping found for region {region}")
        return 0

    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
        {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},  # Assuming Linux
        {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},      # No pre-installed software
        {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},         # Default tenancy
        {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},    # On-demand instances
    ]

    try:
        response = client.get_products(ServiceCode='AmazonEC2', Filters=filters)
        price_list = response['PriceList']

        if not price_list:
            print(f"No pricing data found for {instance_type} in {location}")
            return 0

        price_item = eval(price_list[0])
        terms = price_item['terms']['OnDemand']
        for term in terms.values():
            price_dimensions = term['priceDimensions']
            for dimension in price_dimensions.values():
                price_per_hour = float(dimension['pricePerUnit']['USD'])
                return price_per_hour
    except Exception as e:
        print(f"Error fetching price for {instance_type} in {location}: {e}")
        return 0

def calculate_total_cost():
    session = boto3.Session(region_name='us-east-1')
    ec2 = session.client('ec2')

    regions = ec2.describe_regions()['Regions']
    total_cost = 0.0
    calculation = {
        "total_cost": 0.0,
        "regions": {}
    }
    for region in regions:
        region_name = region['RegionName']
        print(f"Checking instances in region: {region_name}")

        ec2_region = session.client('ec2', region_name=region_name)
        try:
            instances = ec2_region.describe_instances()
        except Exception as e:
            print(f"Error retrieving instances in region {region_name}: {e}")
            continue

        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_type = instance['InstanceType']
                state = instance['State']['Name']

                if state == 'running':
                    cost_per_hour = get_instance_cost(instance_type, region_name)
                    instance_cost = cost_per_hour * 24 * 30
                    total_cost += instance_cost

                    print(f"Instance {instance['InstanceId']} in {region_name} costs {instance_cost:.2f} per month")
                    calculation["total_cost"] += instance_cost
                    calculation["regions"].setdefault(region_name, []).append({
                        "instance_id": instance['InstanceId'],
                        "instance_type": instance_type,
                        "state": state,
                        "monthly_cost": f"{instance_cost:.2f}"
                    })
    print(json.dumps(calculation, indent=4))
    print(f"Total estimated cost for all regions: {total_cost:.2f}")
    return f"{total_cost:.2f}"