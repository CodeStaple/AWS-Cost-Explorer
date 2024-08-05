import boto3

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
}

def get_rds_instance_cost(instance_type, region, database_engine):
    client = boto3.client('pricing', region_name='us-east-1')

    location = REGION_NAME_MAPPING.get(region, None)
    if not location:
        print(f"No location mapping found for region {region}")
        return 0

    filters = [
        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
        {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
        {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': database_engine},
        {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'},
    ]

    try:
        response = client.get_products(ServiceCode='AmazonRDS', Filters=filters)
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

def calculate_rds_total_cost():
    session = boto3.Session(region_name='us-east-1')
    rds = session.client('rds')

    regions = [region['RegionName'] for region in session.client('ec2').describe_regions()['Regions']]
    total_cost = 0.0

    for region in regions:
        print(f"Checking RDS instances in region: {region}")

        rds_region = session.client('rds', region_name=region)
        try:
            instances = rds_region.describe_db_instances()
        except Exception as e:
            print(f"Error retrieving RDS instances in region {region}: {e}")
            continue

        for instance in instances['DBInstances']:
            instance_type = instance['DBInstanceClass']
            db_instance_id = instance['DBInstanceIdentifier']
            engine = instance['Engine']

            if instance['DBInstanceStatus'] == 'available':
                cost_per_hour = get_rds_instance_cost(instance_type, region, engine)
                instance_cost = cost_per_hour * 24 * 30
                total_cost += instance_cost

                print(f"RDS instance {db_instance_id} in {region} ({engine}) costs {instance_cost:.2f} per month")

    print(f"Total estimated RDS cost for all regions: {total_cost:.2f}")
    return f"{total_cost:.2f}"
